"""Base definition for App Center clients."""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import time
from typing import Any, BinaryIO, Callable, Dict, Optional, Tuple
from urllib3.util.retry import Retry

import deserialize
import requests
from requests.adapters import HTTPAdapter


from appcenter.constants import API_BASE_URL


ProgressCallback = Callable[[int, Optional[int]], None]


class AppCenterHTTPError:
    """Represents the response for a HTTP error."""

    code: str
    message: str


class AppCenterHTTPException(Exception):
    """All App Center HTTP exceptions use this class."""

    response: requests.Response

    def __init__(self, response: requests.Response) -> None:
        """Create a new AppCenterHTTPException

        :param response: The response to the HTTP request
        """

        super().__init__()
        self.response = response

    def __str__(self) -> str:
        """Generate and return the string representation of the object.
        :return: A string representation of the object
        """
        return (
            f"method={self.response.request.method}, "
            + f"url={self.response.request.url}, "
            + f"status_code={self.response.status_code}, "
            + f"text={self.response.text}"
        )


class AppCenterDecodedHTTPException(AppCenterHTTPException):
    """An App Center HTTP exception where we managed to decode the response."""

    error: AppCenterHTTPError

    def __init__(self, response: requests.Response, error: AppCenterHTTPError) -> None:
        """Create a new AppCenterDecodedHTTPException.

        :param response: The response to the HTTP request
        :param error: The decoded error
        """

        super().__init__(response)
        self.error = error

    def __str__(self) -> str:
        """Generate and return the string representation of the object.
        :return: A string representation of the object
        """
        return (
            f"method={self.response.request.method}, "
            + f"url={self.response.request.url}, "
            + f"status_code={self.response.status_code}, "
            + f"error={self.error}"
        )


def create_exception(response: requests.Response) -> AppCenterHTTPException:
    """Create the exception for a response.

    :param request: The original request
    :param response: The response from App Center

    :returns: The constructed exception
    """
    try:
        response_json = response.json()
        return AppCenterDecodedHTTPException(
            response, deserialize.deserialize(AppCenterHTTPError, response_json)
        )
    except Exception:
        return AppCenterHTTPException(response)


class AppCenterDerivedClient:
    """Base definition for App Center clients.

    :param name: The name of the derived client
    :param token: The authentication token
    :param parent_logger: The parent logger that we will use for our own logging
    """

    log: logging.Logger
    token: str
    session: requests.Session

    def __init__(self, name: str, token: str, parent_logger: logging.Logger) -> None:
        self.log = parent_logger.getChild(name)
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({"X-API-Token": self.token})
        retry = Retry(
            total=3, read=3, connect=3, backoff_factor=2, status_forcelist=(500, 502, 503, 504, 599)
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def generate_url(self, *, version: str = "0.1", owner_name: str, app_name: str) -> str:
        """Generate a URL to use for querying the API.

        :param str version: The API version to hit
        :param str owner_name: The name of the owner of the app
        :param str app_name: The name of the app

        :returns: A generated URL base
        """

        url = f"{API_BASE_URL}/v{version}/apps/{owner_name}/{app_name}"
        self.log.debug(f"Generated URL: {url}")
        return url

    def get(self, url: str) -> requests.Response:
        """Perform a GET request to a url

        :param url: The URL to run the GET on

        :returns: The raw response

        :raises AppCenterHTTPException: If the request fails with a non 200 status code
        """

        # For a GET we also need to retry on a 202
        attempts = 0
        while attempts < 3:
            attempts += 1

            response = self.session.get(url)

            if response.status_code == 202 and attempts < 3:
                time.sleep(10)
                continue

            if response.status_code != 200:
                raise create_exception(response)

            break

        return response

    def patch(self, url: str, *, data: Any) -> requests.Response:
        """Perform a PATCH request to a url

        :param url: The URL to run the POST on
        :param data: The JSON serializable data to send

        :returns: The raw response

        :raises AppCenterHTTPException: If the request fails with a non 200 status code
        """
        response = self.session.patch(url, headers={"Content-Type": "application/json"}, json=data)

        if response.status_code < 200 or response.status_code >= 300:
            raise create_exception(response)

        return response

    def post(self, url: str, *, data: Any) -> requests.Response:
        """Perform a POST request to a url

        :param url: The URL to run the POST on
        :param data: The JSON serializable data to send

        :returns: The raw response

        :raises AppCenterHTTPException: If the request fails with a non 200 status code
        """
        response = self.session.post(url, headers={"Content-Type": "application/json"}, json=data)

        if response.status_code < 200 or response.status_code >= 300:
            raise create_exception(response)

        return response

    def post_files(self, url: str, *, files: Dict[str, Tuple[str, BinaryIO]]) -> requests.Response:
        """Perform a POST request to a url, sending files

        :param url: The URL to run the POST on
        :param files: The dictionary of file data. Each key is a unique file. The values are a tuple
                      with the first property being the file name, the second being a stream of the
                      file contents.

        :returns: The raw response

        :raises AppCenterHTTPException: If the request fails with a non 200 status code
        """

        response = self.session.post(url, files=files, timeout=20 * 60)

        if response.status_code < 200 or response.status_code >= 300:
            raise create_exception(response)

        return response

    def delete(self, url: str) -> requests.Response:
        """Perform a DELETE request to a url

        :param url: The URL to run the DELETE on

        :returns: The raw response

        :raises AppCenterHTTPException: If the request fails with a non 200 status code
        """
        response = self.session.delete(url)

        if response.status_code < 200 or response.status_code >= 300:
            raise create_exception(response)

        return response

    def azure_blob_upload(self, url: str, *, file_stream: BinaryIO) -> requests.Response:
        """Upload a file to an Azure Blob Storage URL

        :param url: The URL to upload to
        :param file_stream: The stream to the file contents

        :returns: The raw response

        :raises AppCenterHTTPException: If the request fails with a non 200 status code
        """

        response = requests.put(
            url,
            headers={"Content-Type": "application/octet-stream", "x-ms-blob-type": "BlockBlob"},
            data=file_stream.read(),
        )

        if response.status_code < 200 or response.status_code >= 300:
            self.log.debug("Azure URL: " + url)
            raise create_exception(response)

        return response
