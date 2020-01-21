"""App Center versions API wrappers."""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import os
from typing import Iterator, List, Optional
import urllib.parse

import deserialize

from appcenter.derived_client import AppCenterDerivedClient
from appcenter.models import (
    BasicReleaseDetailsResponse,
    BuildInfo,
    ReleaseDetailsResponse,
    ReleaseUploadBeginResponse,
    ReleaseUploadEndResponse,
    ReleaseDestinationResponse,
    ReleaseUpdateRequest,
)


class AppCenterVersionsClient(AppCenterDerivedClient):
    """Wrapper around the App Center versions APIs.

    :param token: The authentication token
    :param parent_logger: The parent logger that we will use for our own logging
    """

    def __init__(self, token: str, parent_logger: logging.Logger) -> None:
        super().__init__("versions", token, parent_logger)

    def recent(self, *, owner_name: str, app_name: str) -> List[BasicReleaseDetailsResponse]:
        """Get the recent version for each distribution group.

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app

        :returns: A list of BasicReleaseDetailsResponse
        """

        self.log.info(f"Getting recent versions of app: {owner_name}/{app_name}")

        request_url = self.generate_url(owner_name=owner_name, app_name=app_name)
        request_url += f"/recent_releases"

        response = self.get(request_url)

        return deserialize.deserialize(List[BasicReleaseDetailsResponse], response.json())

    def all(
        self,
        *,
        owner_name: str,
        app_name: str,
        published_only: bool = False,
        scope: Optional[str] = None,
    ) -> Iterator[BasicReleaseDetailsResponse]:
        """Get all (the 100 latest) versions.

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app
        :param bool published_only: Return only the published releases (defaults to false)
        :param Optional[str] scope: When the scope is 'tester', only includes
                                    releases that have been distributed to
                                    groups that the user belongs to.

        :returns: An iterator of BasicReleaseDetailsResponse
        """

        self.log.info(f"Getting versions of app: {owner_name}/{app_name}")

        request_url = self.generate_url(owner_name=owner_name, app_name=app_name)
        request_url += f"/releases?"

        parameters = {"published_only": str(published_only).lower()}

        if scope:
            parameters["scope"] = scope

        request_url += urllib.parse.urlencode(parameters)

        response = self.get(request_url)

        return deserialize.deserialize(List[BasicReleaseDetailsResponse], response.json())

    def release_details(
        self, *, owner_name: str, app_name: str, release_id: str
    ) -> ReleaseDetailsResponse:
        """Get the full release details for a given version.

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app
        :param str release_id: The ID of the release to get the details for

        :returns: The full details for a release
        """

        self.log.info(f"Getting details for: {owner_name}/{app_name} - {release_id}")

        request_url = self.generate_url(owner_name=owner_name, app_name=app_name)
        request_url += f"/releases/{release_id}?"

        response = self.get(request_url)

        return deserialize.deserialize(ReleaseDetailsResponse, response.json())

    def release_id_for_version(
        self, *, owner_name: str, app_name: str, version: str
    ) -> Optional[int]:
        """Get the App Center release identifier for the app version (usually build number).

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app
        :param bool version: The app version (usually build number)

        :returns: The App Center release identifier
        """

        for app_version in self.all(owner_name=owner_name, app_name=app_name):
            if app_version.version == version:
                return app_version.identifier

        return None

    def latest_commit(self, *, owner_name: str, app_name: str) -> Optional[str]:
        """Find the most recent release which has an available commit in it and return the commit hash.

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app

        :returns: The latest commit available on App Center
        """

        self.log.info(f"Getting latest commit for app: {owner_name}/{app_name}")

        for version in self.all(owner_name=owner_name, app_name=app_name):

            full_details = self.release_details(
                owner_name=owner_name, app_name=app_name, release_id=str(version.identifier)
            )

            if full_details.build is None:
                continue

            if full_details.build.commit_hash is not None:
                return full_details.build.commit_hash

        return None

    def get_upload_url(
        self, *, owner_name: str, app_name: str, version: str, build_number: str
    ) -> ReleaseUploadBeginResponse:
        """Get the App Center release identifier for the app version (usually build number).

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app
        :param str version: The app version
        :param str build_number: The build number

        :returns: The App Center release identifier
        """

        request_url = self.generate_url(owner_name=owner_name, app_name=app_name)
        request_url += f"/release_uploads"

        data = {"release_id": 0, "build_version": version, "build_number": build_number}

        response = self.post(request_url, data=data)

        return deserialize.deserialize(ReleaseUploadBeginResponse, response.json())

    def upload_binary(
        self, *, upload_url_response: ReleaseUploadBeginResponse, binary_path: str
    ) -> None:
        """Upload a binary

        :param ReleaseUploadBeginResponse upload_url_response: The response to a `get_upload_url` call
        :param binary_path: The path to the binary to upload

        :returns: ?
        """

        with open(binary_path, "rb") as binary_file:
            files = {"ipa": (os.path.basename(binary_path), binary_file)}
            # Nothing to do with the response since we've already validated it
            self.post_files(url=upload_url_response.upload_url, files=files)

    def commit_upload(
        self, *, owner_name: str, app_name: str, upload_id: str
    ) -> ReleaseUploadEndResponse:
        """Get the App Center release identifier for the app version (usually build number).

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app
        :param str upload_id: The ID of the upload to commit

        :returns: The App Center release end response
        """

        request_url = self.generate_url(owner_name=owner_name, app_name=app_name)
        request_url += f"/release_uploads/{upload_id}"

        data = {"status": "committed"}

        response = self.patch(request_url, data=data)

        return deserialize.deserialize(ReleaseUploadEndResponse, response.json())

    def release(
        self,
        *,
        owner_name: str,
        app_name: str,
        release_id: str,
        group_id: str,
        mandatory_update: bool = False,
        notify_testers: bool = False,
    ) -> ReleaseDestinationResponse:
        """Release a build to a group.

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app
        :param str release_id: The release ID of the app
        :param str group_id: The release ID of the group to release to
        :param bool mandatory_update: Set to True to make this a mandatory update
        :param bool notify_testers: Set to True to notify testers about this new build

        :returns: The App Center release identifier
        """

        request_url = self.generate_url(owner_name=owner_name, app_name=app_name)
        request_url += f"/releases/{release_id}/groups"

        data = {
            "id": group_id,
            "mandatory_update": mandatory_update,
            "notify_testers": notify_testers,
        }

        response = self.post(request_url, data=data)

        return deserialize.deserialize(ReleaseDestinationResponse, response.json())

    def update_release(
        self,
        *,
        owner_name: str,
        app_name: str,
        release_id: str,
        release_update_request: ReleaseUpdateRequest,
    ) -> None:
        """Update a release with new details

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app
        :param str release_id: The release ID of the app
        :param ReleaseUpdateRequest release_update_request: The release ID of the group to release to

        :returns: The App Center release identifier
        """

        request_url = self.generate_url(owner_name=owner_name, app_name=app_name)
        request_url += f"/releases/{release_id}"

        self.patch(request_url, data=release_update_request.json())

    def upload_build(
        self,
        *,
        owner_name: str,
        app_name: str,
        version: str,
        build_number: str,
        binary_path: str,
        release_notes: str,
        branch_name: Optional[str] = None,
        commit_hash: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> Optional[str]:
        """Get the App Center release identifier for the app version (usually build number).

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app
        :param str version: The app version
        :param str build_number: The build number
        :param str binary_path: The path to the binary to upload
        :param str release_notes: The release notes for the release
        :param Optional[str] branch_name: The git branch that the build came from
        :param Optional[str] commit_hash: The hash of the commit that was just built
        :param Optional[str] commit_message: The message of the commit that was just built

        :raises FileNotFoundError: If the supplied binary is not found
        :raises Exception: If we don't get a release ID back after upload

        :returns: The release details
        """

        if not os.path.exists(binary_path):
            raise FileNotFoundError(f"Could not find binary: {binary_path}")

        upload_begin_response = self.get_upload_url(
            owner_name=owner_name, app_name=app_name, version=version, build_number=build_number
        )

        self.upload_binary(upload_url_response=upload_begin_response, binary_path=binary_path)

        upload_end_response = self.commit_upload(
            owner_name=owner_name, app_name=app_name, upload_id=upload_begin_response.upload_id
        )

        if upload_end_response.release_id is None:
            raise Exception(f"Failed to get release ID for upload")

        build_info = BuildInfo(
            branch_name=branch_name, commit_hash=commit_hash, commit_message=commit_message
        )
        update_request = ReleaseUpdateRequest(release_notes=release_notes, build=build_info)

        self.update_release(
            owner_name=owner_name,
            app_name=app_name,
            release_id=upload_end_response.release_id,
            release_update_request=update_request,
        )

        return upload_end_response.release_id

    def upload_and_release(
        self,
        *,
        owner_name: str,
        app_name: str,
        version: str,
        build_number: str,
        binary_path: str,
        group_id: str,
        release_notes: str,
        branch_name: Optional[str] = None,
        commit_hash: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> ReleaseDetailsResponse:
        """Get the App Center release identifier for the app version (usually build number).

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app
        :param str version: The app version
        :param str build_number: The build number
        :param str binary_path: The path to the binary to upload
        :param str group_id: The ID of the group to release to
        :param str release_notes: The release notes for the release
        :param Optional[str] branch_name: The git branch that the build came from
        :param Optional[str] commit_hash: The hash of the commit that was just built
        :param Optional[str] commit_message: The message of the commit that was just built

        :raises FileNotFoundError: If the supplied binary is not found
        :raises Exception: If we don't get a release ID back after upload

        :returns: The release details
        """

        release_id = self.upload_build(
            owner_name=owner_name,
            app_name=app_name,
            version=version,
            build_number=build_number,
            binary_path=binary_path,
            release_notes=release_notes,
            branch_name=branch_name,
            commit_hash=commit_hash,
            commit_message=commit_message,
        )

        if release_id is None:
            raise Exception("Did not get release ID after upload")

        self.release(
            owner_name=owner_name, app_name=app_name, release_id=release_id, group_id=group_id
        )

        return self.release_details(owner_name=owner_name, app_name=app_name, release_id=release_id)
