# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test OAuth actions for RDM migration."""

from pathlib import Path

import orjson
import pytest
from invenio_rdm_migrator.extract import Tx
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load

from zenodo_rdm_migrator.actions.transform import (
    OAuthApplicationCreateAction,
    OAuthApplicationDeleteAction,
    OAuthApplicationUpdateAction,
    OAuthServerTokenCreateAction,
    OAuthServerTokenDeleteAction,
    OAuthServerTokenUpdateAction,
)

##
# TOKENS
##


@pytest.fixture()
def create_oauth_server_token_tx():
    """Transaction data to create an OAuth server token.

    As it would be after the extraction step.
    """
    datafile = Path(__file__).parent / "testdata" / "tokens" / "create.jsonl"
    with open(datafile, "rb") as reader:
        ops = [orjson.loads(line)["value"] for line in reader]

    return {"tx_id": 1, "operations": ops}


class TestOAuthServerTokenCreateAction:
    """Create OAuth server token action tests."""

    def test_matches_with_valid_data(self):
        assert (
            OAuthServerTokenCreateAction.matches_action(
                Tx(
                    id=1,
                    operations=[
                        {
                            "op": OperationType.INSERT,
                            "source": {"table": "oauth2server_client"},
                            "after": {},
                        },
                        {
                            "op": OperationType.INSERT,
                            "source": {"table": "oauth2server_token"},
                            "after": {},
                        },
                    ],
                )
            )
            is True
        )

    def test_matches_with_invalid_data(self):
        missing_client = [
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}},
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        missing_token = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}},
        ]

        only_client = [
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}}
        ]

        only_token = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_token"},
                "after": {},
            }
        ]

        wrong_op_token = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        wrong_op_client = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        extra_op = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "another"},
                "after": {},
            },
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}},
        ]

        for invalid_ops in [
            missing_client,
            missing_token,
            wrong_op_client,
            wrong_op_token,
            extra_op,
        ]:
            assert (
                OAuthServerTokenCreateAction.matches_action(
                    Tx(id=1, operations=invalid_ops)
                )
                is False
            )

    def test_transform_with_valid_data(self, create_oauth_server_token_tx):
        action = OAuthServerTokenCreateAction(
            Tx(
                id=create_oauth_server_token_tx["tx_id"],
                operations=create_oauth_server_token_tx["operations"],
            )
        )
        assert isinstance(action.transform(), load.OAuthServerTokenCreateAction)


@pytest.fixture()
def update_oauth_server_token_tx():
    """Transaction data to update an OAuth server token.

    As it would be after the extraction step.
    """
    datafile = Path(__file__).parent / "testdata" / "tokens" / "update.jsonl"
    with open(datafile, "rb") as reader:
        ops = [orjson.loads(line)["value"] for line in reader]

    return {"tx_id": 1, "operations": ops}


class TestOAuthServerTokenUpdateAction:
    """Update OAuth server token action tests."""

    def test_matches_with_valid_data(self):
        both = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        only_token = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        for valid_ops in [
            both,
            only_token,
        ]:
            assert (
                OAuthServerTokenUpdateAction.matches_action(
                    Tx(id=1, operations=valid_ops)
                )
                is True
            )

    def test_matches_with_invalid_data(self):
        empty = []

        wrong_op_token = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        wrong_op_client = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        extra_op = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}},
        ]

        extra_op_only_client = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}},
        ]

        only_client = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
        ]

        for invalid_ops in [
            empty,
            wrong_op_client,
            wrong_op_token,
            extra_op,
            extra_op_only_client,
            only_client,
        ]:
            assert (
                OAuthServerTokenUpdateAction.matches_action(
                    Tx(id=1, operations=invalid_ops)
                )
                is False
            )

    def test_transform_with_valid_data(self, update_oauth_server_token_tx):
        action = OAuthServerTokenUpdateAction(
            Tx(
                id=update_oauth_server_token_tx["tx_id"],
                operations=update_oauth_server_token_tx["operations"],
            )
        )
        assert isinstance(action.transform(), load.OAuthServerTokenUpdateAction)


@pytest.fixture()
def delete_oauth_server_token_tx():
    """Transaction data to delete an OAuth server token.

    As it would be after the extraction step.
    """
    datafile = Path(__file__).parent / "testdata" / "tokens" / "delete.jsonl"
    with open(datafile, "rb") as reader:
        ops = [orjson.loads(line)["value"] for line in reader]

    return {"tx_id": 1, "operations": ops}


class TestOAuthServerTokenDeleteAction:
    """Delete OAuth server token action tests."""

    def test_matches_with_valid_data(self):
        assert (
            OAuthServerTokenDeleteAction.matches_action(
                Tx(
                    id=1,
                    operations=[
                        {
                            "op": OperationType.DELETE,
                            "source": {"table": "oauth2server_token"},
                            "after": {},
                        }
                    ],
                )
            )
            is True
        )

    def test_matches_with_invalid_data(self):
        empty = []

        w_client = [
            {
                "op": OperationType.DELETE,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {
                "op": OperationType.DELETE,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        no_token = [
            {
                "op": OperationType.DELETE,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
        ]

        extra_op = [
            {
                "op": OperationType.DELETE,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}},
        ]

        for invalid_ops in [
            empty,
            w_client,
            no_token,
            extra_op,
        ]:
            assert (
                OAuthServerTokenDeleteAction.matches_action(
                    Tx(id=1, operations=invalid_ops)
                )
                is False
            )

    def test_transform_with_valid_data(self, delete_oauth_server_token_tx):
        action = OAuthServerTokenDeleteAction(
            Tx(
                id=delete_oauth_server_token_tx["tx_id"],
                operations=delete_oauth_server_token_tx["operations"],
            )
        )
        assert isinstance(action.transform(), load.OAuthServerTokenDeleteAction)


##
# APPLICATIONS
##


@pytest.fixture()
def create_oauth_application_tx():
    """Transaction data to create an OAuth application token.

    As it would be after the extraction step.
    """
    datafile = Path(__file__).parent / "testdata" / "applications" / "create.jsonl"
    with open(datafile, "rb") as reader:
        ops = [orjson.loads(line)["value"] for line in reader]

    return {"tx_id": 1, "operations": ops}


class TestOAuthApplicationCreateAction:
    """Create OAuth server application action tests."""

    def test_matches_with_valid_data(self):
        assert (
            OAuthApplicationCreateAction.matches_action(
                Tx(
                    id=1,
                    operations=[
                        {
                            "op": OperationType.INSERT,
                            "source": {"table": "oauth2server_client"},
                            "after": {},
                        }
                    ],
                )
            )
            is True
        )

    def test_matches_with_invalid_data(self):
        empty = []

        wrong_op = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
        ]

        extra_op = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        for invalid_ops in [empty, wrong_op, extra_op]:
            assert (
                OAuthApplicationCreateAction.matches_action(
                    Tx(id=1, operations=invalid_ops)
                )
                is False
            )

    def test_transform_with_valid_data(self, create_oauth_application_tx):
        action = OAuthApplicationCreateAction(
            Tx(
                id=create_oauth_application_tx["tx_id"],
                operations=create_oauth_application_tx["operations"],
            )
        )
        assert isinstance(action.transform(), load.OAuthApplicationCreateAction)


@pytest.fixture()
def update_oauth_application_tx():
    """Transaction data to update an OAuth application token.

    As it would be after the extraction step.
    """
    datafile = Path(__file__).parent / "testdata" / "applications" / "update.jsonl"
    with open(datafile, "rb") as reader:
        ops = [orjson.loads(line)["value"] for line in reader]

    return {"tx_id": 1, "operations": ops}


@pytest.fixture()
def reset_oauth_application_tx():
    """Transaction data to reset an OAuth application token.

    As it would be after the extraction step.
    """
    datafile = Path(__file__).parent / "testdata" / "applications" / "reset.jsonl"
    with open(datafile, "rb") as reader:
        ops = [orjson.loads(line)["value"] for line in reader]

    return {"tx_id": 1, "operations": ops}


class TestOAuthApplicationUpdateAction:
    """Update OAuth server application action tests."""

    def test_matches_with_valid_data(self):
        assert (
            OAuthApplicationUpdateAction.matches_action(
                Tx(
                    id=1,
                    operations=[
                        {
                            "op": OperationType.UPDATE,
                            "source": {"table": "oauth2server_client"},
                            "after": {},
                        }
                    ],
                )
            )
            is True
        )

    def test_matches_with_invalid_data(self):
        empty = []

        wrong_op = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
        ]

        extra_op = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        for invalid_ops in [empty, wrong_op, extra_op]:
            assert (
                OAuthApplicationUpdateAction.matches_action(
                    Tx(id=1, operations=invalid_ops)
                )
                is False
            )

    def test_transform_with_valid_data(self, update_oauth_application_tx):
        action = OAuthApplicationUpdateAction(
            Tx(
                id=update_oauth_application_tx["tx_id"],
                operations=update_oauth_application_tx["operations"],
            )
        )
        assert isinstance(action.transform(), load.OAuthApplicationUpdateAction)

    def test_transform_with_valid_data_reset_secret(self, reset_oauth_application_tx):
        action = OAuthApplicationUpdateAction(
            Tx(
                id=reset_oauth_application_tx["tx_id"],
                operations=reset_oauth_application_tx["operations"],
            )
        )
        assert isinstance(action.transform(), load.OAuthApplicationUpdateAction)


@pytest.fixture()
def delete_oauth_application_tx():
    """Transaction data to delete an OAuth application token.

    As it would be after the extraction step.
    """
    datafile = Path(__file__).parent / "testdata" / "applications" / "delete.jsonl"
    with open(datafile, "rb") as reader:
        ops = [orjson.loads(line)["value"] for line in reader]

    return {"tx_id": 1, "operations": ops}


class TestOAuthApplicationDeleteAction:
    """Delete OAuth server application action tests."""

    def test_matches_with_valid_data(self):
        assert (
            OAuthApplicationDeleteAction.matches_action(
                Tx(
                    id=1,
                    operations=[
                        {
                            "op": OperationType.DELETE,
                            "source": {"table": "oauth2server_client"},
                            "after": {},
                        }
                    ],
                )
            )
            is True
        )

    def test_matches_with_invalid_data(self):
        empty = []

        wrong_op = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
        ]

        extra_op = [
            {
                "op": OperationType.DELETE,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        for invalid_ops in [empty, wrong_op, extra_op]:
            assert (
                OAuthApplicationDeleteAction.matches_action(
                    Tx(id=1, operations=invalid_ops)
                )
                is False
            )

    def test_transform_with_valid_data(self, delete_oauth_application_tx):
        action = OAuthApplicationDeleteAction(
            Tx(
                id=delete_oauth_application_tx["tx_id"],
                operations=delete_oauth_application_tx["operations"],
            )
        )
        assert isinstance(action.transform(), load.OAuthApplicationDeleteAction)