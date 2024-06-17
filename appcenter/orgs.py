"""App Center account API wrappers."""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging

import deserialize

from appcenter.orgs_teams import AppCenterOrgsTeamsClient
from appcenter.derived_client import AppCenterDerivedClient
from appcenter.models import (
    OrganizationUserResponse,
    AppResponse,
)


class AppCenterOrgsClient(AppCenterDerivedClient):
    """Wrapper around the App Center org APIs.

    :param token: The authentication token
    :param parent_logger: The parent logger that we will use for our own logging
    """

    teams: AppCenterOrgsTeamsClient

    def __init__(self, token: str, parent_logger: logging.Logger) -> None:
        super().__init__("org", token, parent_logger)
        self.teams = AppCenterOrgsTeamsClient(token, parent_logger)

    def users(self, *, org_name: str) -> list[OrganizationUserResponse]:
        """Get the users in an org.

        :param org_name: The name of the organization

        :returns: A list of OrganizationUserResponse
        """

        request_url = self.generate_org_url(org_name=org_name)
        request_url += "/users"

        response = self.http_get(request_url)

        return deserialize.deserialize(list[OrganizationUserResponse], response.json())

    def delete_user(self, *, org_name: str, user_name: str) -> None:
        """Delete a user from an org."""

        request_url = self.generate_org_url(org_name=org_name) + f"/users/{user_name}"

        _ = self.http_delete(request_url)

    def apps(self, *, org_name: str) -> list[AppResponse]:
        """Get the apps in an org.

        :param org_name: The name of the organization

        :returns: A list of AppResponse
        """

        request_url = self.generate_org_url(org_name=org_name)
        request_url += "/apps"

        response = self.http_get(request_url)

        return deserialize.deserialize(list[AppResponse], response.json())
