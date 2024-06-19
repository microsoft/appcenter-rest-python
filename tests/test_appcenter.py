#!/usr/bin/env python3

"""Tests for the package."""

# pylint: disable=line-too-long

import datetime
import os
import re
import subprocess
import sys
import uuid

import pytest

print(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import appcenter


# pylint: disable=redefined-outer-name


def get_from_keychain() -> str | None:
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


def get_tokens() -> list[str]:
    """Get the tokens for authentication.

    :returns: The org name, app name and token as a tuple.
    """
    details = get_from_keychain()

    if details:
        return details.split(":")

    return os.environ["appcenter"].split(":")


@pytest.fixture(scope="session")
def org_name() -> str:
    """Get the org name.

    :returns: The org name
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


def test_construction(org_name: str, app_name: str, token: str):
    """Test construction."""
    client = appcenter.AppCenterClient(access_token=token)
    start_time = datetime.datetime.now() - datetime.timedelta(days=10)
    # Test to fetch at least 2 error group batches
    error_group_batch_limit = 2
    error_group_batch_count = 0

    for group in client.crashes.get_error_groups(
        org_name=org_name,
        app_name=app_name,
        start_time=start_time,
        order_by="count desc",
        limit=1,
    ):
        group_details = client.crashes.group_details(
            org_name=org_name,
            app_name=app_name,
            error_group_id=group.errorGroupId,
        )

        assert group_details is not None

        errors = client.crashes.errors_in_group(
            org_name=org_name,
            app_name=app_name,
            start_time=start_time,
            error_group_id=group.errorGroupId,
        )

        has_errors = False
        for error in errors:
            assert error.errorId is not None
            error_details = client.crashes.error_details(
                org_name=org_name,
                app_name=app_name,
                error_group_id=group.errorGroupId,
                error_id=error.errorId,
            )
            assert error_details is not None

            full_details = client.crashes.error_info_dictionary(
                org_name=org_name,
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


def test_recent(org_name: str, app_name: str, token: str):
    """Test recent."""
    client = appcenter.AppCenterClient(access_token=token)
    recent_builds = client.versions.recent(org_name=org_name, app_name=app_name)
    for build in recent_builds:
        print(build)


def test_versions(org_name: str, app_name: str, token: str):
    """Test recent."""
    client = appcenter.AppCenterClient(access_token=token)
    builds = client.versions.all(org_name=org_name, app_name=app_name)
    for build in builds:
        print(build)


def test_release_id(org_name: str, app_name: str, token: str):
    """Test release id check."""
    client = appcenter.AppCenterClient(access_token=token)
    release_id = client.versions.release_id_for_version(
        org_name=org_name, app_name=app_name, version="2917241"
    )
    print(release_id)


def test_release_details(org_name: str, app_name: str, token: str):
    """Test release details."""
    client = appcenter.AppCenterClient(access_token=token)
    recent_builds = client.versions.recent(org_name=org_name, app_name=app_name)
    build = recent_builds[0]
    full_details = client.versions.release_details(
        org_name=org_name,
        app_name=app_name,
        release_id=build.identifier,
    )
    print(full_details)


def test_latest_commit(org_name: str, app_name: str, token: str):
    """Test release details."""
    client = appcenter.AppCenterClient(access_token=token)
    commit_hash = client.versions.latest_commit(org_name=org_name, app_name=app_name)
    assert commit_hash is not None


def test_release_counts(org_name: str, app_name: str, token: str):
    """Test release details."""
    client = appcenter.AppCenterClient(access_token=token)
    recent_builds = client.versions.recent(org_name=org_name, app_name=app_name)
    build = recent_builds[0]
    full_details = client.versions.release_details(
        org_name=org_name,
        app_name=app_name,
        release_id=build.identifier,
    )
    assert full_details.destinations is not None
    counts = client.analytics.release_counts(
        org_name=org_name,
        app_name=app_name,
        releases=[
            appcenter.models.ReleaseWithDistributionGroup(
                full_details.identifier, full_details.destinations[0].identifier
            )
        ],
    )
    print(counts)


def test_upload(org_name: str, token: str):
    """Test upload."""
    ipa_path = "/path/to/some.ipa"
    if not os.path.exists(ipa_path):
        return
    client = appcenter.AppCenterClient(access_token=token)
    release_id = client.versions.upload_build(
        org_name=org_name,
        app_name="UploadTestApp",
        binary_path=ipa_path,
        release_notes="These are some release notes",
        branch_name="test_branch",
        commit_hash="1234567890123456789012345678901234567890",
        commit_message="This is a commit message",
    )
    assert release_id is not None


def test_symbol_upload(org_name: str, token: str):
    """Test symbol."""
    symbols_path = "/path/to/some.dSYM.zip"

    if not os.path.isfile(symbols_path):
        return

    client = appcenter.AppCenterClient(access_token=token)
    client.crashes.upload_symbols(
        org_name=org_name,
        app_name="Test",
        version="0.1",
        build_number="123",
        symbols_path=symbols_path,
        symbol_type=appcenter.models.SymbolType.APPLE,
    )


def test_annotations(org_name: str, app_name: str, token: str):
    """Test construction."""
    client = appcenter.AppCenterClient(access_token=token)

    group_id = None
    annotation = str(uuid.uuid4())

    for result in client.crashes.get_error_groups(
        org_name=org_name,
        app_name=app_name,
        start_time=datetime.datetime.now() - datetime.timedelta(days=14),
        order_by="count desc",
        limit=1,
    ):
        group_id = result.errorGroupId
        break

    assert group_id is not None

    client.crashes.set_annotation(
        org_name=org_name,
        app_name=app_name,
        error_group_id=group_id,
        annotation=annotation,
    )

    details = client.crashes.group_details(
        org_name=org_name,
        app_name=app_name,
        error_group_id=group_id,
    )

    assert details.annotation == annotation


def test_users(org_name: str, app_name: str, token: str):
    """Test construction."""
    client = appcenter.AppCenterClient(access_token=token)
    users = client.apps.users(org_name=org_name, app_name=app_name)

    assert len(users) > 0

    testers = list(
        filter(
            lambda user: user.permissions[0] == appcenter.models.Permission.TESTER,  # type:ignore
            users,
        )
    )
    viewers = list(
        filter(
            lambda user: user.permissions[0] == appcenter.models.Permission.VIEWER,  # type:ignore
            users,
        )
    )
    developers = list(
        filter(
            lambda user: user.permissions[0]  # type:ignore
            == appcenter.models.Permission.DEVELOPER,
            users,
        )
    )
    managers = list(
        filter(
            lambda user: user.permissions[0] == appcenter.models.Permission.MANAGER,  # type:ignore
            users,
        )
    )

    assert len(testers) <= len(users)
    assert len(viewers) <= len(users)
    assert len(developers) <= len(users)
    assert len(managers) <= len(users)

    assert len(testers) + len(viewers) + len(developers) + len(managers) == len(users)


def test_get_user_tokens(token: str):
    """Test get user tokens."""
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


def test_get_teams(org_name: str, token: str):
    """Test get teams"""
    client = appcenter.AppCenterClient(access_token=token)
    teams = client.orgs.teams.get(org_name=org_name)
    assert len(teams) != 0


def test_get_team_users(org_name: str, token: str):
    """Test get teams"""
    client = appcenter.AppCenterClient(access_token=token)
    teams = client.orgs.teams.get(org_name=org_name)
    team = teams[0]
    users = client.orgs.teams.users(org_name=org_name, team_name=team.name)
    assert len(users) != 0


def test_get_apps(org_name: str, token: str):
    """Test get apps"""
    client = appcenter.AppCenterClient(access_token=token)
    apps = client.orgs.apps(org_name=org_name)
    assert len(apps) != 0


def test_get_apps_teams(org_name: str, token: str):
    """Test get apps"""
    client = appcenter.AppCenterClient(access_token=token)
    apps = client.orgs.apps(org_name=org_name)
    assert len(apps) != 0
    teams = client.apps.teams(org_name=org_name, app_name=apps[0].name)
    assert len(teams) != 0
