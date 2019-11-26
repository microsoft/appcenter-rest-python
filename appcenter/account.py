"""App Center account API wrappers."""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
from typing import List, Optional
import urllib.parse

import deserialize

from appcenter.derived_client import AppCenterDerivedClient
from appcenter.models import User, Permission, Role


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

    def add_collaborator(
        self, *, owner_name: str, app_name: str, user_email: str, role: Optional[Role] = None
    ) -> None:
        """Add a user as a collaborator to an app.

        If they are a new collaborator, they will be invited. If that is the
        case, the role must be specified.

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app
        :param str user_email: The email of the user
        :param Optional[Role] role: The role the user should have (this is required for new users)

        :returns: The list of users
        """

        self.log.info(f"Adding user {user_email} as collaborator on: {owner_name}/{app_name}")

        request_url = self.generate_url(owner_name=owner_name, app_name=app_name)
        request_url += f"/invitations"

        data = {"user_email": user_email}

        if role:
            data["role"] = role.value

        self.post(request_url, data=data)

    def delete_collaborator(self, *, owner_name: str, app_name: str, user_email: str) -> None:
        """Remove a user as a collaborator from an app.

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app
        :param str user_email: The email of the user to remove
        """

        self.log.info(f"Deleting user {user_email} from: {owner_name}/{app_name}")

        request_url = self.generate_url(owner_name=owner_name, app_name=app_name)
        request_url += f"/users/{urllib.parse.quote(user_email)}"

        self.delete(request_url)

    def set_collaborator_permissions(
        self, *, owner_name: str, app_name: str, user_email: str, permission: Permission
    ) -> None:
        """Set a users collaborator permissions on an app.

        :param str owner_name: The name of the app account owner
        :param str app_name: The name of the app
        :param str user_email: The email of the user
        :param Permission permission: The permission level to grant

        :returns: The list of users
        """

        self.log.info(
            f"Setting user {user_email} as collaborator with permission "
            + f"{permission.value} on: {owner_name}/{app_name}"
        )

        request_url = self.generate_url(owner_name=owner_name, app_name=app_name)
        request_url += f"/users/{urllib.parse.quote(user_email)}"

        self.patch(request_url, data={"permissions": [permission.value]})
