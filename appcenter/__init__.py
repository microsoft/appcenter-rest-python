#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""App Center API wrapper."""

import logging

from appcenter.apps import AppCenterAppsClient
from appcenter.analytics import AppCenterAnalyticsClient
from appcenter.crashes import AppCenterCrashesClient
from appcenter.orgs import AppCenterOrgsClient
from appcenter.tokens import AppCenterTokensClient
from appcenter.versions import AppCenterVersionsClient

# pylint: disable=too-many-instance-attributes


class AppCenterClient:
    """Class responsible for getting data from App Center through REST calls.

    :param access_token: The access token to use for authentication. Leave as None to use KeyVault
    """

    log: logging.Logger
    token: str

    apps: AppCenterAppsClient
    analytics: AppCenterAnalyticsClient
    crashes: AppCenterCrashesClient
    orgs: AppCenterOrgsClient
    tokens: AppCenterTokensClient
    versions: AppCenterVersionsClient

    def __init__(self, *, access_token: str, parent_logger: logging.Logger | None = None) -> None:
        """Initialize the AppCenterClient with the application id and the token."""

        if parent_logger is None:
            self.log = logging.getLogger("appcenter")
        else:
            self.log = parent_logger.getChild("appcenter")

        self.token = access_token
        self.apps = AppCenterAppsClient(self.token, self.log)
        self.analytics = AppCenterAnalyticsClient(self.token, self.log)
        self.crashes = AppCenterCrashesClient(self.token, self.log)
        self.orgs = AppCenterOrgsClient(self.token, self.log)
        self.tokens = AppCenterTokensClient(self.token, self.log)
        self.versions = AppCenterVersionsClient(self.token, self.log)


# pylint: enable=too-many-instance-attributes
