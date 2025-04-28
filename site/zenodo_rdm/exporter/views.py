# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM exporter views."""

from flask import Blueprint, abort, current_app
from invenio_files_rest.models import ObjectVersion, as_bucket

blueprint = Blueprint(
    "exporter",
    __name__,
)


def _get_bucket():
    bucket_uuid = current_app.config["EXPORTER_BUCKET_UUID"]
    bucket = as_bucket(bucket_uuid)
    if not bucket:
        abort(404, description="Bucket not found")
    return bucket


@blueprint.route("/exporter")
def list_object_versions():
    """List object versions grouped by keys, and with list of create dates and version IDs."""
    bucket = _get_bucket()
    ovs = ObjectVersion.get_by_bucket(bucket, versions=True).all()
    response = {}
    for ov in ovs:
        if ov.key not in response:
            response[ov.key] = []
        # TODO: `isoformat()` returns time at GMT without TZ information; is it OK?
        response[ov.key].append({ov.created.isoformat(): ov.version_id})
    return response


# Remark: using `path` and not `string` to support namespacing via slashes in `key`.
# Remark: exporter files are public and do not require permission.
@blueprint.route("/exporter/<path:key>")
@blueprint.route("/exporter/<path:key>/<uuid:version_id>")
def get_object_version_content(key, version_id=None):
    """Download the content of an object version for a given key and an optional version ID."""
    bucket = _get_bucket()
    # TODO: Sanitize key input? ObjectVersion.validate_key(key)
    ov = ObjectVersion.get(bucket, key, version_id)
    if not ov:
        abort(404, description="ObjectVersion not found")
    return ov.send_file()
