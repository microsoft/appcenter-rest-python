"""App Center analytics API wrappers."""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import enum
import logging
from typing import List, Union

import deserialize

from appcenter.derived_client import AppCenterDerivedClient
from appcenter.models import UserToken


class AppCenterTokensClient(AppCenterDerivedClient):
    """Wrapper around the App Center tokens APIs.

    :param token: The authentication token
    :param parent_logger: The parent logger that we will use for our own logging
    """

    class TokenScope(enum.Enum):
        """Specifies the scope of a token."""

        FULL = "all"
        READER = "viewer"

    def __init__(self, token: str, parent_logger: logging.Logger) -> None:
        super().__init__("tokens", token, parent_logger)

    def get_user_tokens(self) -> List[UserToken]:
        """Get the users tokens

        :returns: The tokens
        """

        self.log.info("Getting user tokens")

        request_url = self.base_url()
        request_url += "/api_tokens"

        response = self.get(request_url)

        return deserialize.deserialize(List[UserToken], response.json())

    def create_user_token(self, name: str, scope: TokenScope) -> UserToken:
        """Create a user token.

        :param name: The name/description of the token
        :param scope: The scope for the token
        """

        request_url = self.base_url()
        request_url += "/api_tokens"

        self.log.debug(f"Creating user token name={name}, scope={scope}")

        response = self.post(request_url, data={"description": name, "scope": [scope.value]})

        return deserialize.deserialize(UserToken, response.json())

    def delete_user_token(self, token: Union[str, UserToken]) -> None:
        """Delete a user token.

        :param token: The token itself or the ID for the token
        """

        request_url = self.base_url()
        request_url += "/api_tokens/"

        if isinstance(token, str):
            self.log.debug(f"Deleting user token={token}")
            request_url += token
        else:
            self.log.debug(f"Deleting user token={token.identifier}")
            request_url += token.identifier

        _ = self.delete(request_url)
