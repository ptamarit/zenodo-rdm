# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM exporter configuration."""

from uuid import UUID

# Similar to legacy exporter: https://github.com/zenodo/zenodo/blob/master/zenodo/modules/exporter/config.py
# TODO: Use 000000000002 since 000000000001 already exists in prod?
EXPORTER_BUCKET_UUID = UUID("00000000-0000-0000-0000-000000000001")

EXPORTER_NUMBER_VERSIONS_TO_KEEP = 3

EXPORTER_USER_ID = 1

EXPORTER_JOB_DEFAULT_FORMAT = "json"

# TODO: Use `example-community-slug` when custom args work properly.
EXPORTER_JOB_DEFAULT_COMMUNITY_SLUG = "biosyslit"
