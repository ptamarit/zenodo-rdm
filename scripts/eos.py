import io
from uuid import UUID

from flask import current_app
from invenio_db import db
from invenio_files_rest.models import Bucket, Location, ObjectVersion, as_bucket

# Similar to legacy exporter: https://github.com/zenodo/zenodo/blob/master/zenodo/modules/exporter/config.py
EXPORTER_BUCKET_UUID = UUID("00000000-0000-0000-0000-000000000001")

EXPORTER_FILENAME = "namespace/records.tar.gz"  # TODO: Or .jsonl.gz
EXPORTER_NUMBER_VERSIONS_TO_KEEP = 3

# Create bucket if needed
bucket = as_bucket(EXPORTER_BUCKET_UUID)
if not bucket:
    print(f"Creating exporter bucket: {EXPORTER_BUCKET_UUID}")
    with db.session.begin_nested():
        # TODO: Set `quota_size` and `max_file_size`.
        bucket = Bucket(
            id=EXPORTER_BUCKET_UUID,
            default_location=Location.get_default().id,
            default_storage_class=current_app.config[
                "FILES_REST_DEFAULT_STORAGE_CLASS"
            ],
        )
        db.session.add(bucket)
        db.session.commit()  # TODO: Commit here OK?

# Store file to bucket
stream = io.BytesIO(b"TODO STREAM CONTENT HERE AND MORE AND MORE: \x00\x01")
# TODO: Should we pass in `size` to `set_contents` since we know the size of the stream?
object_version = ObjectVersion.create(
    bucket=bucket, key=EXPORTER_FILENAME, stream=stream, mimetype="text/plain"
)
print(f"Creating object version: {object_version}")
db.session.add(object_version)
db.session.commit()  # TODO: Commit here OK?

# Remove old versions of file
all_object_versions = ObjectVersion.get_versions(
    bucket=bucket, key=EXPORTER_FILENAME, desc=True
)
for old_object_version in all_object_versions[EXPORTER_NUMBER_VERSIONS_TO_KEEP:]:
    print(f"Removing pervious object version: {old_object_version}")
    # Using `remove` (and not `delete`) since we really want to free up space.
    old_object_version.remove()
db.session.commit()  # TODO: Commit here OK?
