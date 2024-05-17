#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""App Center API wrapper."""

import logging

from appcenter.account import AppCenterAccountClient
from appcenter.analytics import AppCenterAnalyticsClient
from appcenter.crashes import AppCenterCrashesClient
from appcenter.tokens import AppCenterTokensClient
from appcenter.versions import AppCenterVersionsClient


class AppCenterClient:
    """Class responsible for getting data from App Center through REST calls.

    :param access_token: The access token to use for authentication. Leave as None to use KeyVault
    """

    log: logging.Logger
    token: str

    account: AppCenterAccountClient
    analytics: AppCenterAnalyticsClient
    crashes: AppCenterCrashesClient
    tokens: AppCenterTokensClient
    versions: AppCenterVersionsClient

    def __init__(self, *, access_token: str, parent_logger: logging.Logger | None = None) -> None:
        """Initialize the AppCenterClient with the application id and the token."""

        if parent_logger is None:
            self.log = logging.getLogger("appcenter")
        else:
            self.log = parent_logger.getChild("appcenter")

        self.token = access_token
        self.account = AppCenterAccountClient(self.token, self.log)
        self.analytics = AppCenterAnalyticsClient(self.token, self.log)
        self.crashes = AppCenterCrashesClient(self.token, self.log)
        self.tokens = AppCenterTokensClient(self.token, self.log)
        self.versions = AppCenterVersionsClient(self.token, self.log)
