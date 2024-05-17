"""App Center analytics API wrappers."""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging

import deserialize

from appcenter.derived_client import AppCenterDerivedClient
from appcenter.models import ReleaseWithDistributionGroup, ReleaseCounts


class AppCenterAnalyticsClient(AppCenterDerivedClient):
    """Wrapper around the App Center analytics APIs.

    :param token: The authentication token
    :param parent_logger: The parent logger that we will use for our own logging
    """

    def __init__(self, token: str, parent_logger: logging.Logger) -> None:
        super().__init__("analytics", token, parent_logger)

    def release_counts(
        self,
        *,
        org_name: str,
        app_name: str,
        releases: list[ReleaseWithDistributionGroup],
    ) -> ReleaseCounts:
        """Get the release counts for an app

        :param org_name: The name of the organization
        :param app_name: The name of the app
        :param releases: The list of releases to get the counts for

        :returns: The release counts
        """

        self.log.info(f"Getting release counts for: {org_name}/{app_name}")

        request_url = self.generate_app_url(org_name=org_name, app_name=app_name)
        request_url += "/analytics/distribution/release_counts"

        data = []
        for release in releases:
            data.append(
                {
                    "release": release.release,
                    "distribution_group": release.distribution_group,
                }
            )

        response = self.post(request_url, data={"releases": data})

        return deserialize.deserialize(ReleaseCounts, response.json())
