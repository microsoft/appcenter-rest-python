"""Base definition for App Center clients."""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
from typing import Any, BinaryIO, Callable, Dict, Optional, Tuple

import deserialize
import requests
from tenacity import retry, retry_if_exception, retry_if_result, stop_after_attempt, wait_fixed


from appcenter.constants import API_BASE_URL


ProgressCallback = Callable[[int, Optional[int]], None]


class AppCenterHTTPError:
    """Represents the response for a HTTP error."""

    code: str
    message: str

    def __str__(self) -> str:
        """Generate and return the string representation of the object.
        :return: A string representation of the object
        """
        return f"<code={self.code}, message={self.message}>"


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
            f"<method={self.response.request.method}, "
            + f"url={self.response.request.url}, "
            + f"status_code={self.response.status_code}, "
            + f"text={self.response.text}>"
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


def _is_connection_failure(exception: Exception) -> bool:
    exception_checks = [
        "Operation timed out",
        "Connection aborted.",
        "bad handshake: ",
        "Failed to establish a new connection",
    ]

    for check in exception_checks:
        if check in str(exception):
            return True

    return False


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

    @retry(
        retry=(
            retry_if_exception(_is_connection_failure)
            | retry_if_result(
                lambda response: response.status_code == 202
            )  # For a GET we also need to retry on a 202
        ),
        wait=wait_fixed(10),
        stop=stop_after_attempt(3),
    )
    def get(self, url: str) -> requests.Response:
        """Perform a GET request to a url

        :param url: The URL to run the GET on

        :returns: The raw response

        :raises AppCenterHTTPException: If the request fails with a non 200 status code
        """

        response = self.session.get(url)

        if response.status_code != 200:
            raise create_exception(response)

        return response

    @retry(
        retry=(retry_if_exception(_is_connection_failure)),
        wait=wait_fixed(10),
        stop=stop_after_attempt(3),
    )
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

    @retry(
        retry=(retry_if_exception(_is_connection_failure)),
        wait=wait_fixed(10),
        stop=stop_after_attempt(3),
    )
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

    @retry(
        retry=(retry_if_exception(_is_connection_failure)),
        wait=wait_fixed(10),
        stop=stop_after_attempt(3),
    )
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

    @retry(
        retry=(retry_if_exception(_is_connection_failure)),
        wait=wait_fixed(10),
        stop=stop_after_attempt(3),
    )
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

    @retry(
        retry=(retry_if_exception(_is_connection_failure)),
        wait=wait_fixed(10),
        stop=stop_after_attempt(3),
    )
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
