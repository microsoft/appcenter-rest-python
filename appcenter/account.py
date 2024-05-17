"""App Center account API wrappers."""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import urllib.parse

import deserialize

from appcenter.derived_client import AppCenterDerivedClient
from appcenter.models import (
    OrganizationUserResponse,
    TeamResponse,
    User,
    Permission,
    Role,
    AppResponse,
)


class AppCenterAccountClient(AppCenterDerivedClient):
    """Wrapper around the App Center account APIs.

    :param token: The authentication token
    :param parent_logger: The parent logger that we will use for our own logging
    """

    def __init__(self, token: str, parent_logger: logging.Logger) -> None:
        super().__init__("account", token, parent_logger)

    def users(self, *, org_name: str, app_name: str) -> list[User]:
        """Get the users for an app.

        :param org_name: The name of the organization
        :param app_name: The name of the app. If not set, will get for org.

        :returns: A list of User
        """

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += "/users"

        response = self.get(request_url)

        return deserialize.deserialize(list[User], response.json())

    def org_users(self, *, org_name: str) -> list[OrganizationUserResponse]:
        """Get the users in an org.

        :param org_name: The name of the organization

        :returns: A list of OrganizationUserResponse
        """

        request_url = self.generate_org_url(org_name=org_name)
        request_url += "/users"

        response = self.get(request_url)

        return deserialize.deserialize(list[OrganizationUserResponse], response.json())

    def delete_user(self, *, org_name: str, user_name: str) -> None:
        """Delete a user from an org."""

        request_url = self.generate_org_url(org_name=org_name) + f"/users/{user_name}"

        _ = self.delete(request_url)

    def teams(self, *, org_name: str) -> list[TeamResponse]:
        """Get the teams in an org.

        :param org_name: The name of the organization

        :returns: A TeamResponse
        """

        request_url = self.generate_org_url(org_name=org_name)
        request_url += "/teams"

        response = self.get(request_url)

        return deserialize.deserialize(list[TeamResponse], response.json())

    def team_users(self, *, org_name: str, team_name: str) -> list[OrganizationUserResponse]:
        """Get the users in a team in an org.

        :param org_name: The name of the organization
        :param team_name: The name of the team

        :returns: A TeamResponse
        """

        request_url = self.generate_org_url(org_name=org_name)
        request_url += f"/teams/{team_name}/users"

        response = self.get(request_url)

        return deserialize.deserialize(list[OrganizationUserResponse], response.json())

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

        self.post(request_url, data=data)

    def delete_collaborator(self, *, org_name: str, app_name: str, user_email: str) -> None:
        """Remove a user as a collaborator from an app.

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param user_email: The email of the user to remove
        """

        self.log.info(f"Deleting user {user_email} from: {org_name}/{app_name}")

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += f"/users/{urllib.parse.quote(user_email)}"

        self.delete(request_url)

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

        self.patch(request_url, data={"permissions": [permission.value]})

    def apps(self, *, org_name: str) -> list[AppResponse]:
        """Get the apps in an org.

        :param org_name: The name of the organization

        :returns: A list of AppResponse
        """

        request_url = self.generate_org_url(org_name=org_name)
        request_url += "/apps"

        response = self.get(request_url)

        return deserialize.deserialize(list[AppResponse], response.json())
