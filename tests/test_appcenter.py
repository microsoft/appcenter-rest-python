#!/usr/bin/env python3

"""Tests for the package."""

# pylint: disable=line-too-long

import datetime
import os
import sys
from typing import List
import unittest
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.abspath(__file__), "..", "..")))
import appcenter

# pylint: disable=no-self-use


def get_tokens() -> List[str]:
    """Get the tokens for authentication.

    :returns: The owner name, app name and token as a tuple.
    """
    try:
        # pylint: disable=import-outside-toplevel
        import keyper

        # pylint: enable=import-outside-toplevel

        return keyper.get_password(label="appcenter").split(":")
    except ImportError:
        return os.environ["appcenter"].split(":")


class LibraryTests(unittest.TestCase):
    """Basic tests."""

    OWNER_NAME, APP_NAME, TOKEN = get_tokens()

    def test_construction(self):
        """Test construction."""
        client = appcenter.AppCenterClient(access_token=LibraryTests.TOKEN)
        start_time = datetime.datetime.now() - datetime.timedelta(days=10)        
        # Test to fetch at least 2 error group batches
        ERROR_GROUP_BATCH_LIMIT = 2
        error_group_batch_count = 0

        for group in client.crashes.get_error_groups(
            owner_name=LibraryTests.OWNER_NAME,
            app_name=LibraryTests.APP_NAME,
            start_time=start_time,
            order_by="count desc",
            limit=1,
        ):
            details = client.crashes.group_details(
                owner_name=LibraryTests.OWNER_NAME,
                app_name=LibraryTests.APP_NAME,
                error_group_id=group.errorGroupId,
            )

            self.assertIsNotNone(details)

            errors = client.crashes.errors_in_group(
                owner_name=LibraryTests.OWNER_NAME,
                app_name=LibraryTests.APP_NAME,
                start_time=start_time,
                error_group_id=group.errorGroupId,
            )

            has_errors = False
            for error in errors:
                details = client.crashes.error_details(
                    owner_name=LibraryTests.OWNER_NAME,
                    app_name=LibraryTests.APP_NAME,
                    error_group_id=group.errorGroupId,
                    error_id=error.errorId,
                )
                self.assertIsNotNone(details)

                full_details = client.crashes.error_info_dictionary(
                    owner_name=LibraryTests.OWNER_NAME,
                    app_name=LibraryTests.APP_NAME,
                    error_group_id=group.errorGroupId,
                    error_id=error.errorId,
                )
                self.assertIsNotNone(full_details)

                has_errors = True
                break

            self.assertTrue(has_errors)

            error_group_batch_count += 1
            
            if error_group_batch_count == ERROR_GROUP_BATCH_LIMIT:
                break

    def test_recent(self):
        """Test recent."""
        client = appcenter.AppCenterClient(access_token=LibraryTests.TOKEN)
        recent_builds = client.versions.recent(
            owner_name=LibraryTests.OWNER_NAME, app_name=LibraryTests.APP_NAME
        )
        for build in recent_builds:
            print(build)

    def test_versions(self):
        """Test recent."""
        client = appcenter.AppCenterClient(access_token=LibraryTests.TOKEN)
        builds = client.versions.all(
            owner_name=LibraryTests.OWNER_NAME, app_name=LibraryTests.APP_NAME
        )
        for build in builds:
            print(build)

    def test_release_id(self):
        """Test release id check."""
        client = appcenter.AppCenterClient(access_token=LibraryTests.TOKEN)
        release_id = client.versions.release_id_for_version(
            owner_name=LibraryTests.OWNER_NAME, app_name=LibraryTests.APP_NAME, version="2917241"
        )
        print(release_id)

    def test_release_details(self):
        """Test release details."""
        client = appcenter.AppCenterClient(access_token=LibraryTests.TOKEN)
        recent_builds = client.versions.recent(
            owner_name=LibraryTests.OWNER_NAME, app_name=LibraryTests.APP_NAME
        )
        build = recent_builds[0]
        full_details = client.versions.release_details(
            owner_name=LibraryTests.OWNER_NAME,
            app_name=LibraryTests.APP_NAME,
            release_id=build.identifier,
        )
        print(full_details)

    def test_latest_commit(self):
        """Test release details."""
        client = appcenter.AppCenterClient(access_token=LibraryTests.TOKEN)
        commit_hash = client.versions.latest_commit(
            owner_name=LibraryTests.OWNER_NAME, app_name=LibraryTests.APP_NAME
        )
        self.assertIsNotNone(commit_hash)

    def test_release_counts(self):
        """Test release details."""
        client = appcenter.AppCenterClient(access_token=LibraryTests.TOKEN)
        recent_builds = client.versions.recent(
            owner_name=LibraryTests.OWNER_NAME, app_name=LibraryTests.APP_NAME
        )
        build = recent_builds[0]
        full_details = client.versions.release_details(
            owner_name=LibraryTests.OWNER_NAME,
            app_name=LibraryTests.APP_NAME,
            release_id=build.identifier,
        )
        counts = client.analytics.release_counts(
            owner_name=LibraryTests.OWNER_NAME,
            app_name=LibraryTests.APP_NAME,
            releases=[
                appcenter.models.ReleaseWithDistributionGroup(
                    full_details.identifier, full_details.destinations[0].identifier
                )
            ],
        )
        print(counts)

    def test_upload(self):
        """Test upload."""
        client = appcenter.AppCenterClient(access_token=LibraryTests.TOKEN)
        download_url = client.versions.upload_and_release(
            owner_name=LibraryTests.OWNER_NAME,
            app_name="UploadTestApp",
            version="0.1",
            build_number="123",
            binary_path="/path/to/some.ipa",
            group_id="3b2e51c1-5d07-4d04-8980-14d3b91e1a1c",
            release_notes="These are some release notes",
            branch_name="test_branch",
            commit_hash="1234567890123456789012345678901234567890",
            commit_message="This is a commit message",
        )
        self.assertIsNotNone(download_url)

    def test_symbol_upload(self):
        """Test symbol."""
        client = appcenter.AppCenterClient(access_token=LibraryTests.TOKEN)
        client.crashes.upload_symbols(
            owner_name=LibraryTests.OWNER_NAME,
            app_name="UploadTestApp",
            version="0.1",
            build_number="123",
            symbols_path="/path/to/some.dSYM.zip",
            symbol_type=appcenter.models.SymbolType.apple,
        )

    def test_annotations(self):
        """Test construction."""
        client = appcenter.AppCenterClient(access_token=LibraryTests.TOKEN)

        group_id = None
        annotation = str(uuid.uuid4())

        for result in client.crashes.get_error_groups(
            owner_name=LibraryTests.OWNER_NAME,
            app_name=LibraryTests.APP_NAME,
            start_time=datetime.datetime(2019, 9, 20, 12, 0, 0),
            order_by="count desc",
            limit=1,
        ):
            group_id = result.errorGroupId
            break

        client.crashes.set_annotation(
            owner_name=LibraryTests.OWNER_NAME,
            app_name=LibraryTests.APP_NAME,
            error_group_id=group_id,
            annotation=annotation,
        )

        details = client.crashes.group_details(
            owner_name=LibraryTests.OWNER_NAME,
            app_name=LibraryTests.APP_NAME,
            error_group_id=group_id,
        )

        self.assertEqual(details.annotation, annotation)

    def test_users(self):
        """Test construction."""
        client = appcenter.AppCenterClient(access_token=LibraryTests.TOKEN)
        users = client.account.users(
            owner_name=LibraryTests.OWNER_NAME, app_name=LibraryTests.APP_NAME
        )

        self.assertTrue(len(users) > 0)

        testers = list(
            filter(lambda user: user.permissions[0] == appcenter.models.Permission.tester, users)
        )
        viewers = list(
            filter(lambda user: user.permissions[0] == appcenter.models.Permission.viewer, users)
        )
        developers = list(
            filter(lambda user: user.permissions[0] == appcenter.models.Permission.developer, users)
        )
        managers = list(
            filter(lambda user: user.permissions[0] == appcenter.models.Permission.manager, users)
        )

        self.assertLessEqual(len(testers), len(users))
        self.assertLessEqual(len(viewers), len(users))
        self.assertLessEqual(len(developers), len(users))
        self.assertLessEqual(len(managers), len(users))

        self.assertEqual(len(testers) + len(viewers) + len(developers) + len(managers), len(users))
