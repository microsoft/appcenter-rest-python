"""App Center account API wrappers."""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import urllib.parse

import deserialize

from appcenter.derived_client import AppCenterDerivedClient
from appcenter.models import User, Permission, Role, AppTeamResponse


class AppCenterAppsClient(AppCenterDerivedClient):
    """Wrapper around the App Center app APIs.

    :param token: The authentication token
    :param parent_logger: The parent logger that we will use for our own logging
    """

    def __init__(self, token: str, parent_logger: logging.Logger) -> None:
        super().__init__("app", token, parent_logger)

    def users(self, *, org_name: str, app_name: str) -> list[User]:
        """Get the users for an app.

        :param org_name: The name of the organization
        :param app_name: The name of the app

        :returns: A list of User
        """

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += "/users"

        response = self.http_get(request_url)

        return deserialize.deserialize(list[User], response.json())

    def teams(self, *, org_name: str, app_name: str) -> list[AppTeamResponse]:
        """Get the teams for an app.

        :param org_name: The name of the organization
        :param app_name: The name of the app.

        :returns: A list of AppTeamResponse
        """

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += "/teams"

        response = self.http_get(request_url)

        return deserialize.deserialize(list[AppTeamResponse], response.json())

    def add_collaborator(
        self,
        *,
        org_name: str,
        app_name: str,
        user_email: str,
        role: Role | None = None,
    ) -> None:
        """Add a user as a collaborator to an app.

        If they are a new collaborator, they will be invited. If that is the
        case, the role must be specified.

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param user_email: The email of the user
        :param role: The role the user should have (this is required for new users)

        :returns: The list of users
        """

        self.log.info(f"Adding user {user_email} as collaborator on: {org_name}/{app_name}")

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += "/invitations"

        data = {"user_email": user_email}

        if role:
            data["role"] = role.value

        self.http_post(request_url, data=data)

    def delete_collaborator(self, *, org_name: str, app_name: str, user_email: str) -> None:
        """Remove a user as a collaborator from an app.

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param user_email: The email of the user to remove
        """

        self.log.info(f"Deleting user {user_email} from: {org_name}/{app_name}")

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += f"/users/{urllib.parse.quote(user_email)}"

        self.http_delete(request_url)

    def set_collaborator_permissions(
        self, *, org_name: str, app_name: str, user_email: str, permission: Permission
    ) -> None:
        """Set a users collaborator permissions on an app.

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param user_email: The email of the user
        :param permission: The permission level to grant

        :returns: The list of users
        """

        self.log.info(
            f"Setting user {user_email} as collaborator with permission "
            + f"{permission.value} on: {org_name}/{app_name}"
        )

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += f"/users/{urllib.parse.quote(user_email)}"

        self.http_patch(request_url, data={"permissions": [permission.value]})
