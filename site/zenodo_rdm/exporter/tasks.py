# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM exporter tasks."""

import csv
import gzip
import json
import os
import tarfile
from datetime import datetime
from io import BytesIO

from celery import shared_task
from flask import current_app
from flask_principal import identity_changed
from invenio_access.permissions import any_user, authenticated_user
from invenio_access.utils import get_identity
from invenio_accounts.proxies import current_datastore
from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from invenio_files_rest.models import (
    Bucket,
    FileInstance,
    Location,
    ObjectVersion,
    as_bucket,
)
from invenio_rdm_records.oai import oai_datacite_etree
from invenio_rdm_records.proxies import current_rdm_records_service as service
from lxml import etree

# TODO: or "application/x-tar" or "application/x-gtar" since it's a ".tar.gz"?
RECORDS_MIMETYPE = "application/gzip"
DELETED_MIMETYPE = "application/gzip"


def _identity_for(id_or_email):
    idty = get_identity(current_datastore.get_user(id_or_email))
    with current_app.test_request_context():
        identity_changed.send(current_app, identity=idty)
        # Needs to be added manually
        idty.provides.add(authenticated_user)
        idty.provides.add(any_user)
    return idty


def _export_records(format, community_slug, records_file, deleted_file):

    community_uuid = None

    if community_slug:
        community_uuid = (
            db.session.query(CommunityMetadata.id)
            .filter(CommunityMetadata.slug == community_slug)
            .one()[0]
        )

    user_id = current_app.config["EXPORTER_USER_ID"]
    idty = _identity_for(user_id)

    res = service.scan(
        idty,
        q=f"parent.communities.ids:{community_uuid}" if community_uuid else "",
        # TODO: Passing `"include_deleted": False` seems to also include deleted records!
        params={"allversions": True, "include_deleted": True},
    )

    deleted_writer = csv.writer(deleted_file)
    deleted_writer.writerow(
        [
            "record_id",
            "doi",
            "removal_reason",
            "removal_date",
            "citation_text",
        ]
    )

    for idx, record in enumerate(res.hits):
        if idx % 1000 == 0:
            print(datetime.now().isoformat(), idx)
        record_id = record.get("id")
        if not record_id:
            continue

        is_deleted = record.get("deletion_status", {}).get("is_deleted", False)
        if is_deleted:
            deleted_writer.writerow(
                [
                    record_id,
                    record["links"]["doi"],
                    # TODO: Or one of these other ways of getting a DOI?
                    # record["links"]["self_doi"],
                    # record["links"]["self_doi_html"],
                    # record["pids"]["doi"]["identifier"]
                    record["tombstone"]["removal_reason"]["id"],
                    record["tombstone"]["removal_date"],
                    record["tombstone"]["citation_text"],
                ]
            )
            continue

        if format == "json":
            # TODO: Is this the correct way of getting all the records information in JSON?
            # TODO: Is it fine to use `encode()` or should we use `StringIO` (instead of `BytesIO`)?
            content_bytes = json.dumps(record).encode()
        elif format == "xml":
            try:
                oai_etree = oai_datacite_etree(None, {"_source": record})
                content_bytes = etree.tostring(
                    oai_etree,
                    xml_declaration=True,
                    encoding="UTF-8",
                )
            except Exception as e:
                current_app.logger.exception(f"Error serializing {record_id}: {e}")
        else:
            raise ValueError(f"Unsupported format '{format}'")

        filename = f"{record_id}.{format}"
        tar_info = tarfile.TarInfo(filename)
        file_content = BytesIO()
        file_content.name = filename
        file_content.write(content_bytes)
        file_content.seek(0)
        tar_info.size = len(content_bytes)
        records_file.addfile(tar_info, fileobj=file_content)


def _create_or_get_bucket():
    bucket_uuid = current_app.config["EXPORTER_BUCKET_UUID"]
    bucket = as_bucket(bucket_uuid)
    if not bucket:
        print(f"Creating exporter bucket: {bucket_uuid}")
        with db.session.begin_nested():
            bucket = Bucket(
                id=bucket_uuid,
                default_location=Location.get_default().id,
                default_storage_class=current_app.config[
                    "FILES_REST_DEFAULT_STORAGE_CLASS"
                ],
            )
            db.session.add(bucket)
            db.session.commit()
            # Revert default values coming from the config.
            bucket.quota_size = None
            bucket.max_file_size = None
            db.session.commit()
    else:
        print(f"Exporter bucket found: {bucket_uuid}")
    return bucket


def _create_file_instance(bucket):
    file_instance = FileInstance.create()
    file_instance.init_contents(
        default_location=bucket.location.uri,
        default_storage_class=bucket.default_storage_class,
    )
    return file_instance


def _create_object_version(bucket, file_instance, filename, mimetype):
    object_version = ObjectVersion.create(
        bucket=bucket, key=filename, mimetype=mimetype
    )
    print(f"Creating object version: {object_version}")
    object_version.set_file(file_instance)
    db.session.add(object_version)
    db.session.commit()


def _update_file_instance_metadata(file_instance):
    file_instance.readable = True
    file_instance.writable = False
    file_instance.size = os.path.getsize(file_instance.storage().fileurl)
    file_instance.update_checksum()


def _remove_old_object_versions(bucket, filename):
    number_versions_to_keep = current_app.config["EXPORTER_NUMBER_VERSIONS_TO_KEEP"]
    object_versions = ObjectVersion.get_versions(bucket=bucket, key=filename, desc=True)
    for object_version in object_versions[number_versions_to_keep:]:
        print(f"Removing previous object version: {object_version}")
        # Using `remove` (and not `delete`) since we really want to free up space.
        object_version.remove()
    db.session.commit()


@shared_task
def export_records(format, community_slug):
    """Export records."""
    bucket = _create_or_get_bucket()

    records_file_instance = _create_file_instance(bucket)
    deleted_file_instance = _create_file_instance(bucket)

    with tarfile.open(
        records_file_instance.storage().fileurl, "w|gz"
    ) as records_file, gzip.open(
        deleted_file_instance.storage().fileurl, "wt"
    ) as deleted_file:
        _export_records(format, community_slug, records_file, deleted_file)

    _update_file_instance_metadata(records_file_instance)
    _update_file_instance_metadata(deleted_file_instance)

    # TODO: timestamp in the filename? Can't we use the timestamp from the object version?
    filename_prefix = f"{community_slug}/" if community_slug else ""
    records_filename = f"{filename_prefix}records-{format}.tar.gz"
    deleted_filename = f"{filename_prefix}records-deleted.csv.gz"

    _create_object_version(
        bucket, records_file_instance, records_filename, RECORDS_MIMETYPE
    )
    _create_object_version(
        bucket, deleted_file_instance, deleted_filename, DELETED_MIMETYPE
    )

    _remove_old_object_versions(bucket, records_filename)
    _remove_old_object_versions(bucket, deleted_filename)
