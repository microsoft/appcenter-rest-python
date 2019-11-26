"""App Center account API wrappers."""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
from typing import List

import deserialize

from appcenter.derived_client import AppCenterDerivedClient
from appcenter.models import User


class AppCenterAccountClient(AppCenterDerivedClient):
    """Wrapper around the App Center account APIs.

    :param token: The authentication token
    :param parent_logger: The parent logger that we will use for our own logging
    """

    def __init__(self, token: str, parent_logger: logging.Logger) -> None:
        super().__init__("account", token, parent_logger)

    def users(self, *, owner_name: str, app_name: str) -> List[User]:
        """Get the users for an app

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app

        :returns: The list of users
        """

        self.log.info(f"Getting user for: {owner_name}/{app_name}")

        request_url = self.generate_url(owner_name=owner_name, app_name=app_name)
        request_url += f"/users"

        response = self.get(request_url)

        return deserialize.deserialize(List[User], response.json())
