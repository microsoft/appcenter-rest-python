"""App Center account API wrappers."""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging

import deserialize

from appcenter.derived_client import AppCenterDerivedClient
from appcenter.models import (
    OrganizationUserResponse,
    TeamResponse,
)


class AppCenterOrgsTeamsClient(AppCenterDerivedClient):
    """Wrapper around the App Center org APIs.

    :param token: The authentication token
    :param parent_logger: The parent logger that we will use for our own logging
    """

    def __init__(self, token: str, parent_logger: logging.Logger) -> None:
        super().__init__("teams", token, parent_logger)

    def get(self, *, org_name: str) -> list[TeamResponse]:
        """Get the teams in an org.

        :param org_name: The name of the organization

        :returns: A TeamResponse
        """

        request_url = self.generate_org_url(org_name=org_name)
        request_url += "/teams"

        response = self.http_get(request_url)

        return deserialize.deserialize(list[TeamResponse], response.json())

    def users(self, *, org_name: str, team_name: str) -> list[OrganizationUserResponse]:
        """Get the users in a team in an org.

        :param org_name: The name of the organization
        :param team_name: The name of the team

        :returns: A TeamResponse
        """

        request_url = self.generate_org_url(org_name=org_name)
        request_url += f"/teams/{team_name}/users"

        response = self.http_get(request_url)

        return deserialize.deserialize(list[OrganizationUserResponse], response.json())
