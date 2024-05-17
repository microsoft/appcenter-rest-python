"""App Center versions API wrappers."""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import os
import time
from typing import Iterator
import urllib.parse

import deserialize

from appcenter.derived_client import AppCenterDerivedClient
from appcenter.models import (
    BasicReleaseDetailsResponse,
    BuildInfo,
    ChunkUploadResponse,
    ReleaseDetailsResponse,
    CreateReleaseUploadResponse,
    CommitUploadResponse,
    ReleaseDestinationResponse,
    ReleaseUpdateRequest,
    SetUploadMetadataResponse,
    UploadCompleteResponse,
)


# From https://github.com/microsoft/appcenter-cli/blob/master/appcenter-file-upload-client-node/src/ac-fus-mime-types.ts
MIME_TYPES = {
    "apk": "application/vnd.android.package-archive",
    "aab": "application/vnd.android.package-archive",
    "msi": "application/x-msi",
    "plist": "application/xml",
    "aetx": "application/c-x509-ca-cert",
    "cer": "application/pkix-cert",
    "xap": "application/x-silverlight-app",
    "appx": "application/x-appx",
    "appxbundle": "application/x-appxbundle",
    "appxupload": "application/x-appxupload",
    "appxsym": "application/x-appxupload",
    "msix": "application/x-msix",
    "msixbundle": "application/x-msixbundle",
    "msixupload": "application/x-msixupload",
    "msixsym": "application/x-msixupload",
}


class AppCenterVersionsClient(AppCenterDerivedClient):
    """Wrapper around the App Center versions APIs.

    :param token: The authentication token
    :param parent_logger: The parent logger that we will use for our own logging
    """

    def __init__(self, token: str, parent_logger: logging.Logger) -> None:
        super().__init__("versions", token, parent_logger)

    def recent(self, *, org_name: str, app_name: str) -> list[BasicReleaseDetailsResponse]:
        """Get the recent version for each distribution group.

        :param org_name: The name of the organization
        :param app_name: The name of the app

        :returns: A list of BasicReleaseDetailsResponse
        """

        self.log.info(f"Getting recent versions of app: {org_name}/{app_name}")

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += "/recent_releases"

        response = self.http_get(request_url)

        return deserialize.deserialize(list[BasicReleaseDetailsResponse], response.json())

    def all(
        self,
        *,
        org_name: str,
        app_name: str,
        published_only: bool = False,
        scope: str | None = None,
    ) -> Iterator[BasicReleaseDetailsResponse]:
        """Get all (the 100 latest) versions.

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param published_only: Return only the published releases (defaults to false)
        :param scope: When the scope is 'tester', only includes
                                    releases that have been distributed to
                                    groups that the user belongs to.

        :returns: An iterator of BasicReleaseDetailsResponse
        """

        self.log.info(f"Getting versions of app: {org_name}/{app_name}")

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += "/releases?"

        parameters = {"published_only": str(published_only).lower()}

        if scope:
            parameters["scope"] = scope

        request_url += urllib.parse.urlencode(parameters)

        response = self.http_get(request_url)

        return deserialize.deserialize(list[BasicReleaseDetailsResponse], response.json())

    def release_details(
        self, *, org_name: str, app_name: str, release_id: int
    ) -> ReleaseDetailsResponse:
        """Get the full release details for a given version.

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param release_id: The ID of the release to get the details for

        :returns: The full details for a release
        """

        self.log.info(f"Getting details for: {org_name}/{app_name} - {release_id}")

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += f"/releases/{release_id}?"

        response = self.http_get(request_url)

        return deserialize.deserialize(ReleaseDetailsResponse, response.json())

    def release_id_for_version(self, *, org_name: str, app_name: str, version: str) -> int | None:
        """Get the App Center release identifier for the app version (usually build number).

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param version: The app version (usually build number)

        :returns: The App Center release identifier
        """

        for app_version in self.all(org_name=org_name, app_name=app_name):
            if app_version.version == version:
                return app_version.identifier

        return None

    def latest_commit(self, *, org_name: str, app_name: str) -> str | None:
        """Find the most recent release which has an available commit in it and return the commit hash.

        :param org_name: The name of the organization
        :param app_name: The name of the app

        :returns: The latest commit available on App Center
        """

        self.log.info(f"Getting latest commit for app: {org_name}/{app_name}")

        for version in self.all(org_name=org_name, app_name=app_name):
            full_details = self.release_details(
                org_name=org_name, app_name=app_name, release_id=version.identifier
            )

            if full_details.build is None:
                continue

            if full_details.build.commit_hash is not None:
                return full_details.build.commit_hash

        return None

    def get_upload_url(self, *, org_name: str, app_name: str) -> CreateReleaseUploadResponse:
        """Get the App Center release identifier for the app version (usually build number).

        :param org_name: The name of the organization
        :param app_name: The name of the app

        :returns: The App Center release identifier
        """

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += "/uploads/releases"

        for attempt in range(3):
            self.log.debug(f"Attempting post {attempt}/3 in get_upload_url")
            try:
                response = self.http_post(request_url, data={})
                if response.ok:
                    break
            except Exception as ex:
                if attempt < 2:
                    self.log.warning(f"Failed to post in get_upload_url: {ex}")
                    self.log.warning("Will wait 10 seconds and try again")
                    time.sleep(10)
                else:
                    raise

        return deserialize.deserialize(CreateReleaseUploadResponse, response.json())

    def set_upload_metadata(
        self,
        *,
        create_release_upload_response: CreateReleaseUploadResponse,
        binary_path: str,
    ) -> SetUploadMetadataResponse | None:
        """Set the metadata for a binary upload

        :param create_release_upload_response: The response to a `get_upload_url` call
        :param binary_path: The path to the binary to upload

        :returns: The upload response if we manage to get one, None otherwise
        """
        file_size = os.path.getsize(binary_path)
        file_name = os.path.basename(binary_path)
        file_ext = os.path.splitext(file_name)[-1]
        if file_ext.startswith("."):
            file_ext = file_ext[1:]
        mime_type = MIME_TYPES.get(file_ext)

        request_url = create_release_upload_response.upload_domain
        request_url += f"/upload/set_metadata/{create_release_upload_response.package_asset_id}?"

        parameters = {"file_name": file_name, "file_size": file_size}

        if mime_type:
            parameters["content_type"] = mime_type

        request_url += urllib.parse.urlencode(parameters)
        request_url += "&token=" + create_release_upload_response.url_encoded_token

        for attempt in range(3):
            self.log.debug(f"Attempting post {attempt}/3 in set_upload_metadata")
            try:
                response = self.http_post(request_url, data={})
                if response.ok:
                    return deserialize.deserialize(SetUploadMetadataResponse, response.json())
            except Exception as ex:
                if attempt < 2:
                    self.log.warning(f"Failed to post in set_upload_metadata: {ex}")
                    self.log.warning("Will wait 10 seconds and try again")
                    time.sleep(10)
                else:
                    raise

        return None

    def _upload_chunk(
        self,
        *,
        chunk_number: int,
        chunk: bytearray,
        create_release_upload_response: CreateReleaseUploadResponse,
    ) -> SetUploadMetadataResponse | None:
        """Set the metadata for a binary upload

        :param create_release_upload_response: The response to a `get_upload_url` call
        :param binary_path: The path to the binary to upload

        :returns: The upload response if we manage to get one, None otherwise
        """

        request_url = create_release_upload_response.upload_domain
        request_url += f"/upload/upload_chunk/{create_release_upload_response.package_asset_id}?"

        parameters = {"block_number": chunk_number}

        request_url += urllib.parse.urlencode(parameters)
        request_url += "&token=" + create_release_upload_response.url_encoded_token

        for attempt in range(3):
            self.log.debug(f"Attempting post {attempt}/3 in _upload_chunk")
            try:
                response = self.http_post_raw_data(url=request_url, data=chunk)
                if response.ok:
                    return deserialize.deserialize(ChunkUploadResponse, response.json())
            except Exception as ex:
                if attempt < 2:
                    self.log.warning(f"Failed to post in _upload_chunk: {ex}")
                    self.log.warning("Will wait 10 seconds and try again")
                    time.sleep(10)
                else:
                    raise

        return None

    def _mark_upload_finished(
        self, *, create_release_upload_response: CreateReleaseUploadResponse
    ) -> UploadCompleteResponse | None:
        """Mark the upload of a binary as finished

        :param create_release_upload_response: The response to a `get_upload_url` call

        :returns: The upload complete response on success, None otherwise.
        """

        request_url = create_release_upload_response.upload_domain
        request_url += f"/upload/finished/{create_release_upload_response.package_asset_id}?"

        parameters = {"callback": ""}

        request_url += urllib.parse.urlencode(parameters)
        request_url += "&token=" + create_release_upload_response.url_encoded_token

        for attempt in range(3):
            self.log.debug(f"Attempting post {attempt}/3 in _mark_upload_finished")
            try:
                response = self.http_post_raw_data(request_url, data=None)
                if response.ok:
                    return deserialize.deserialize(UploadCompleteResponse, response.json())
            except Exception as ex:
                if attempt < 2:
                    self.log.warning(f"Failed to post in _mark_upload_finished: {ex}")
                    self.log.warning("Will wait 10 seconds and try again")
                    time.sleep(10)
                else:
                    raise

        return None

    def upload_binary(
        self,
        *,
        create_release_upload_response: CreateReleaseUploadResponse,
        binary_path: str,
    ) -> bool:
        """Upload a binary

        :param create_release_upload_response: The response to a `get_upload_url` call
        :param binary_path: The path to the binary to upload

        :returns: True on success, False on failure
        """

        upload_metadata_response = self.set_upload_metadata(
            create_release_upload_response=create_release_upload_response,
            binary_path=binary_path,
        )

        if not upload_metadata_response:
            self.log.error("Failed to get upload metadata response")
            return False

        with open(binary_path, "rb") as binary_file:
            chunk_numbers = upload_metadata_response.chunk_list
            unhandled_chunks = []

            def direct_upload_chunk(chunk, chunk_number):
                nonlocal unhandled_chunks
                try:
                    response = self._upload_chunk(
                        chunk_number=chunk_number,
                        chunk=chunk,
                        create_release_upload_response=create_release_upload_response,
                    )
                    if response is None:
                        self.log.warn(f"Failed to get response for uploading chunk {chunk_number}")
                        unhandled_chunks.append((chunk_number, 0, chunk))
                except Exception as ex:
                    self.log.warn(
                        f"Got an error response for uploading chunk {chunk_number} -> {ex}"
                    )
                    unhandled_chunks.append((chunk_number, 0, chunk))

            while len(chunk_numbers) > 0:
                chunk_number = chunk_numbers.pop(0)
                chunk = binary_file.read(upload_metadata_response.chunk_size)
                direct_upload_chunk(chunk, chunk_number)

            while len(unhandled_chunks) > 0:
                chunk_number, attempts, chunk = unhandled_chunks.pop(0)
                if attempts >= 3:
                    self.log.error(f"Failed to upload {len(unhandled_chunks)}")
                    return False
                direct_upload_chunk(chunk, chunk_number)

        self._mark_upload_finished(create_release_upload_response=create_release_upload_response)

        return True

    def commit_upload(
        self, *, org_name: str, app_name: str, upload_id: str
    ) -> CommitUploadResponse:
        """Get the App Center release identifier for the app version (usually build number).

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param upload_id: The ID of the upload to commit

        :returns: The App Center release end response
        """

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += f"/uploads/releases/{upload_id}"

        data = {"upload_status": "uploadFinished"}

        for attempt in range(3):
            self.log.debug(f"Attempting patch {attempt}/3 in commit_upload")
            try:
                response = self.http_patch(request_url, data=data)
                if response.ok:
                    break
            except Exception as ex:
                if attempt < 2:
                    self.log.warning(f"Failed to patch in commit_upload: {ex}")
                    self.log.warning("Will wait 10 seconds and try again")
                    time.sleep(10)
                else:
                    raise

        return deserialize.deserialize(CommitUploadResponse, response.json())

    def _wait_for_upload(
        self, *, org_name: str, app_name: str, upload_id: str
    ) -> CommitUploadResponse:
        """Wait for an upload to finish processing

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param upload_id: The ID of the upload to wait for
        """

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += f"/uploads/releases/{upload_id}"

        def wait():
            self.log.info("Sleeping for 2 seconds before checking upload status again.")
            time.sleep(2)  # Same as the app center CLI

        while True:
            self.log.info("Checking upload status...")
            response = self.http_get(request_url)

            if not response.ok:
                wait()
                continue

            try:
                response_data = deserialize.deserialize(CommitUploadResponse, response.json())
            except Exception as ex:
                self.log.warning(f"Failed to get response data: {ex}")
                wait()
                continue

            if response_data.upload_status in ["uploadStarted", "uploadFinished"]:
                wait()
                continue

            if response_data.upload_status == "uploadCanceled":
                return response_data

            if response_data.upload_status == "readyToBePublished":
                return response_data

            if response_data.upload_status == "malwareDetected":
                raise Exception("Malware detected in uploaded binary")

            if response_data.upload_status == "error":
                raise Exception(
                    "An error occurred when waiting for binary: "
                    + response_data.get("error_details", "?")
                )

            raise Exception(f"Unexpected status: {response_data.upload_status}")

    def release(
        self,
        *,
        org_name: str,
        app_name: str,
        release_id: int,
        group_id: str,
        mandatory_update: bool = False,
        notify_testers: bool = False,
    ) -> ReleaseDestinationResponse:
        """Release a build to a group.

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param release_id: The release ID of the app
        :param group_id: The release ID of the group to release to
        :param mandatory_update: Set to True to make this a mandatory update
        :param notify_testers: Set to True to notify testers about this new build

        :returns: The App Center release identifier
        """

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += f"/releases/{release_id}/groups"

        data = {
            "id": group_id,
            "mandatory_update": mandatory_update,
            "notify_testers": notify_testers,
        }

        for attempt in range(3):
            self.log.debug(f"Attempting post {attempt}/3 in release")
            try:
                response = self.http_post(request_url, data=data)
                if response.ok:
                    break
            except Exception as ex:
                if attempt < 2:
                    self.log.warning(f"Failed to post in release: {ex}")
                    self.log.warning("Will wait 10 seconds and try again")
                    time.sleep(10)
                else:
                    raise

        return deserialize.deserialize(ReleaseDestinationResponse, response.json())

    def update_release(
        self,
        *,
        org_name: str,
        app_name: str,
        release_id: int,
        release_update_request: ReleaseUpdateRequest,
    ) -> None:
        """Update a release with new details

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param release_id: The release ID of the app
        :param release_update_request: The release ID of the group to release to

        :returns: The App Center release identifier
        """

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += f"/releases/{release_id}"

        for attempt in range(3):
            self.log.debug(f"Attempting patch {attempt}/3 in update_release")
            try:
                response = self.http_patch(request_url, data=release_update_request.json())
                if response.ok:
                    break
            except Exception as ex:
                if attempt < 2:
                    self.log.warning(f"Failed to patch in update_release: {ex}")
                    self.log.warning("Will wait 10 seconds and try again")
                    time.sleep(10)
                else:
                    raise

    def upload_build(
        self,
        *,
        org_name: str,
        app_name: str,
        binary_path: str,
        release_notes: str,
        branch_name: str | None = None,
        commit_hash: str | None = None,
        commit_message: str | None = None,
    ) -> int | None:
        """Get the App Center release identifier for the app version (usually build number).

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param binary_path: The path to the binary to upload
        :param release_notes: The release notes for the release
        :param branch_name: The git branch that the build came from
        :param commit_hash: The hash of the commit that was just built
        :param commit_message: The message of the commit that was just built

        :raises FileNotFoundError: If the supplied binary is not found
        :raises Exception: If we don't get a release ID back after upload

        :returns: The release ID
        """

        if not os.path.exists(binary_path):
            raise FileNotFoundError(f"Could not find binary: {binary_path}")

        create_release_upload_response = self.get_upload_url(org_name=org_name, app_name=app_name)

        success = self.upload_binary(
            create_release_upload_response=create_release_upload_response,
            binary_path=binary_path,
        )

        if not success:
            raise Exception("Failed to upload binary")

        self.commit_upload(
            org_name=org_name,
            app_name=app_name,
            upload_id=create_release_upload_response.identifier,
        )

        upload_end_response = self._wait_for_upload(
            org_name=org_name,
            app_name=app_name,
            upload_id=create_release_upload_response.identifier,
        )

        if upload_end_response.release_distinct_id is None:
            raise Exception("No release ID was supplied in the upload end response")

        build_info = BuildInfo(
            branch_name=branch_name,
            commit_hash=commit_hash,
            commit_message=commit_message,
        )
        update_request = ReleaseUpdateRequest(release_notes=release_notes, build=build_info)

        self.update_release(
            org_name=org_name,
            app_name=app_name,
            release_id=upload_end_response.release_distinct_id,
            release_update_request=update_request,
        )

        return upload_end_response.release_distinct_id

    # pylint: disable=too-many-arguments
    def upload_and_release(
        self,
        *,
        org_name: str,
        app_name: str,
        binary_path: str,
        group_id: str,
        release_notes: str,
        notify_testers: bool | None = None,
        branch_name: str | None = None,
        commit_hash: str | None = None,
        commit_message: str | None = None,
    ) -> ReleaseDetailsResponse:
        """Get the App Center release identifier for the app version (usually build number).

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param binary_path: The path to the binary to upload
        :param group_id: The ID of the group to release to
        :param release_notes: The release notes for the release
        :param notify_testers: Set to True to notify testers about this build
        :param branch_name: The git branch that the build came from
        :param commit_hash: The hash of the commit that was just built
        :param commit_message: The message of the commit that was just built

        :raises FileNotFoundError: If the supplied binary is not found
        :raises Exception: If we don't get a release ID back after upload

        :returns: The release details
        """

        release_id = self.upload_build(
            org_name=org_name,
            app_name=app_name,
            binary_path=binary_path,
            release_notes=release_notes,
            branch_name=branch_name,
            commit_hash=commit_hash,
            commit_message=commit_message,
        )

        if release_id is None:
            raise Exception("Did not get release ID after upload")

        self.release(
            org_name=org_name,
            app_name=app_name,
            release_id=release_id,
            group_id=group_id,
            notify_testers=notify_testers if notify_testers else False,
        )

        return self.release_details(org_name=org_name, app_name=app_name, release_id=release_id)

    # pylint: enable=too-many-arguments
