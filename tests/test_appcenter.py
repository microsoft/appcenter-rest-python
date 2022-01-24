#!/usr/bin/env python3

"""Tests for the package."""

# pylint: disable=line-too-long

import datetime
import os
import re
import subprocess
import sys
from typing import List, Optional
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.abspath(__file__), "..", "..")))
import appcenter


# pylint: disable=redefined-outer-name


def get_from_keychain() -> Optional[str]:
    """Get the test details from the keychain.

    :returns: A string with the details (colon separated)
    """

    # From https://github.com/microsoft/keyper/blob/develop/keyper/__init__.py

    command = ["security", "find-generic-password", "-l", "appcenter", "-g"]

    try:
        output = subprocess.run(
            command,
            universal_newlines=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stderr
    except subprocess.CalledProcessError:
        return None

    # The output is somewhat complex. We are looking for the line starting "password:"
    password_lines = [line for line in output.split("\n") if line.startswith("password: ")]

    if len(password_lines) != 1:
        raise Exception("Failed to get password from security output")

    password_line = password_lines[0]

    complex_pattern_match = re.match(r"^password: 0x([0-9A-F]*) .*$", password_line)
    simple_pattern_match = re.match(r'^password: "(.*)"$', password_line)

    password = None

    if complex_pattern_match:
        hex_value = complex_pattern_match.group(1)
        password = bytes.fromhex(hex_value).decode("utf-8")

    elif simple_pattern_match:
        password = simple_pattern_match.group(1)

    else:
        password = ""

    return password


def get_tokens() -> List[str]:
    """Get the tokens for authentication.

    :returns: The owner name, app name and token as a tuple.
    """
    details = get_from_keychain()

    if details:
        return details.split(":")

    return os.environ["appcenter"].split(":")


@pytest.fixture(scope="session")
def owner_name() -> str:
    """Get the owner name.

    :returns: The owner name
    """
    return get_tokens()[0]


@pytest.fixture(scope="session")
def app_name() -> str:
    """Get the app name.

    :returns: The app name
    """
    return get_tokens()[1]


@pytest.fixture(scope="session")
def token() -> str:
    """Get the auth token.

    :returns: The auth token
    """
    return get_tokens()[2]


def test_construction(owner_name: str, app_name: str, token: str):
    """Test construction."""
    client = appcenter.AppCenterClient(access_token=token)
    start_time = datetime.datetime.now() - datetime.timedelta(days=10)
    # Test to fetch at least 2 error group batches
    error_group_batch_limit = 2
    error_group_batch_count = 0

    for group in client.crashes.get_error_groups(
        owner_name=owner_name,
        app_name=app_name,
        start_time=start_time,
        order_by="count desc",
        limit=1,
    ):
        group_details = client.crashes.group_details(
            owner_name=owner_name,
            app_name=app_name,
            error_group_id=group.errorGroupId,
        )

        assert group_details is not None

        errors = client.crashes.errors_in_group(
            owner_name=owner_name,
            app_name=app_name,
            start_time=start_time,
            error_group_id=group.errorGroupId,
        )

        has_errors = False
        for error in errors:
            assert error.errorId is not None
            error_details = client.crashes.error_details(
                owner_name=owner_name,
                app_name=app_name,
                error_group_id=group.errorGroupId,
                error_id=error.errorId,
            )
            assert error_details is not None

            full_details = client.crashes.error_info_dictionary(
                owner_name=owner_name,
                app_name=app_name,
                error_group_id=group.errorGroupId,
                error_id=error.errorId,
            )
            assert full_details is not None

            has_errors = True
            break

        assert has_errors

        error_group_batch_count += 1

        if error_group_batch_count == error_group_batch_limit:
            break


def test_recent(owner_name: str, app_name: str, token: str):
    """Test recent."""
    client = appcenter.AppCenterClient(access_token=token)
    recent_builds = client.versions.recent(owner_name=owner_name, app_name=app_name)
    for build in recent_builds:
        print(build)


def test_versions(owner_name: str, app_name: str, token: str):
    """Test recent."""
    client = appcenter.AppCenterClient(access_token=token)
    builds = client.versions.all(owner_name=owner_name, app_name=app_name)
    for build in builds:
        print(build)


def test_release_id(owner_name: str, app_name: str, token: str):
    """Test release id check."""
    client = appcenter.AppCenterClient(access_token=token)
    release_id = client.versions.release_id_for_version(
        owner_name=owner_name, app_name=app_name, version="2917241"
    )
    print(release_id)


def test_release_details(owner_name: str, app_name: str, token: str):
    """Test release details."""
    client = appcenter.AppCenterClient(access_token=token)
    recent_builds = client.versions.recent(owner_name=owner_name, app_name=app_name)
    build = recent_builds[0]
    full_details = client.versions.release_details(
        owner_name=owner_name,
        app_name=app_name,
        release_id=build.identifier,
    )
    print(full_details)


def test_latest_commit(owner_name: str, app_name: str, token: str):
    """Test release details."""
    client = appcenter.AppCenterClient(access_token=token)
    commit_hash = client.versions.latest_commit(owner_name=owner_name, app_name=app_name)
    assert commit_hash is not None


def test_release_counts(owner_name: str, app_name: str, token: str):
    """Test release details."""
    client = appcenter.AppCenterClient(access_token=token)
    recent_builds = client.versions.recent(owner_name=owner_name, app_name=app_name)
    build = recent_builds[0]
    full_details = client.versions.release_details(
        owner_name=owner_name,
        app_name=app_name,
        release_id=build.identifier,
    )
    assert full_details.destinations is not None
    counts = client.analytics.release_counts(
        owner_name=owner_name,
        app_name=app_name,
        releases=[
            appcenter.models.ReleaseWithDistributionGroup(
                full_details.identifier, full_details.destinations[0].identifier
            )
        ],
    )
    print(counts)


def test_upload(owner_name: str, token: str):
    """Test upload."""
    ipa_path = "/path/to/some.ipa"
    if not os.path.exists(ipa_path):
        return
    client = appcenter.AppCenterClient(access_token=token)
    release_id = client.versions.upload_build(
        owner_name=owner_name,
        app_name="UploadTestApp",
        binary_path=ipa_path,
        release_notes="These are some release notes",
        branch_name="test_branch",
        commit_hash="1234567890123456789012345678901234567890",
        commit_message="This is a commit message",
    )
    assert release_id is not None


def test_symbol_upload(owner_name: str, token: str):
    """Test symbol."""
    symbols_path = "/path/to/some.dSYM.zip"

    if not os.path.isfile(symbols_path):
        return

    client = appcenter.AppCenterClient(access_token=token)
    client.crashes.upload_symbols(
        owner_name=owner_name,
        app_name="UploadTestApp",
        version="0.1",
        build_number="123",
        symbols_path=symbols_path,
        symbol_type=appcenter.models.SymbolType.APPLE,
    )


def test_annotations(owner_name: str, app_name: str, token: str):
    """Test construction."""
    client = appcenter.AppCenterClient(access_token=token)

    group_id = None
    annotation = str(uuid.uuid4())

    for result in client.crashes.get_error_groups(
        owner_name=owner_name,
        app_name=app_name,
        start_time=datetime.datetime.now() - datetime.timedelta(days=60),
        order_by="count desc",
        limit=1,
    ):
        group_id = result.errorGroupId
        break

    assert group_id is not None

    client.crashes.set_annotation(
        owner_name=owner_name,
        app_name=app_name,
        error_group_id=group_id,
        annotation=annotation,
    )

    details = client.crashes.group_details(
        owner_name=owner_name,
        app_name=app_name,
        error_group_id=group_id,
    )

    assert details.annotation == annotation


def test_users(owner_name: str, app_name: str, token: str):
    """Test construction."""
    client = appcenter.AppCenterClient(access_token=token)
    users = client.account.users(owner_name=owner_name, app_name=app_name)

    assert len(users) > 0

    testers = list(
        filter(lambda user: user.permissions[0] == appcenter.models.Permission.TESTER, users)
    )
    viewers = list(
        filter(lambda user: user.permissions[0] == appcenter.models.Permission.VIEWER, users)
    )
    developers = list(
        filter(lambda user: user.permissions[0] == appcenter.models.Permission.DEVELOPER, users)
    )
    managers = list(
        filter(lambda user: user.permissions[0] == appcenter.models.Permission.MANAGER, users)
    )

    assert len(testers) <= len(users)
    assert len(viewers) <= len(users)
    assert len(developers) <= len(users)
    assert len(managers) <= len(users)

    assert len(testers) + len(viewers) + len(developers) + len(managers) == len(users)


def test_get_tokens(token: str):
    """Test get tokens."""
    client = appcenter.AppCenterClient(access_token=token)
    tokens = client.tokens.get_user_tokens()
    assert len(tokens) > 0


def test_create_delete_tokens(token: str):
    """Test creating and deleting tokens."""
    client = appcenter.AppCenterClient(access_token=token)
    name = "appcenter test token"
    new_token = client.tokens.create_user_token(
        name, appcenter.AppCenterTokensClient.TokenScope.FULL
    )
    assert new_token.description == name
    client.tokens.delete_user_token(new_token)
