"""Data type models"""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import datetime
import enum
from typing import Any, Dict, List, Optional

import deserialize


def iso8601parse(date_string: Optional[str]) -> Optional[datetime.datetime]:
    """Parse an ISO8601 date string into a datetime.

    :param date_string: The date string to parse

    :returns: The parsed datetime
    """
    if date_string is None:
        return None
    try:
        return datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")


# pylint: disable=missing-docstring


class HandledErrorReasonFrame:
    class ProgrammingLanguage(enum.Enum):
        JAVASCRIPT = "JavaScript"
        C_SHARP = "CSharp"
        OBJECTIVE_C = "Objective-C"
        OBJECTIVE_CPP = "Objective-Cpp"
        CPP = "Cpp"
        C = "C"
        SWIFT = "Swift"
        JAVA = "Java"
        UNKNOWN = "Unknown"

    className: Optional[str]  # name of the class
    method: Optional[str]  # name of the method
    classMethod: Optional[bool]  # is a class method
    file: Optional[str]  # name of the file
    line: Optional[int]  # line number
    appCode: Optional[bool]  # this line isn't from any framework
    frameworkName: Optional[str]  # Name of the framework
    codeFormatted: Optional[str]  # Formatted frame string
    codeRaw: Optional[str]  # Unformatted Frame string
    methodParams: Optional[str]  # parameters of the frames method
    exceptionType: Optional[str]  # Exception type.
    osExceptionType: Optional[str]  # OS exception type. (aka. SIGNAL)
    language: Optional[ProgrammingLanguage]  # programming language of the frame


class ErrorGroupState(enum.Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    IGNORED = "Ignored"


@deserialize.parser("firstOccurrence", iso8601parse)
@deserialize.parser("lastOccurrence", iso8601parse)
class ErrorGroupListItem:

    state: ErrorGroupState
    annotation: Optional[str]
    errorGroupId: str
    appVersion: str
    appBuild: Optional[str]
    count: int
    deviceCount: int
    firstOccurrence: datetime.datetime
    lastOccurrence: datetime.datetime
    exceptionType: Optional[str]
    exceptionMessage: Optional[str]
    exceptionClassName: Optional[str]
    exceptionClassMethod: Optional[bool]
    exceptionMethod: Optional[str]
    exceptionAppCode: Optional[bool]
    exceptionFile: Optional[str]
    exceptionLine: Optional[str]
    codeRaw: Optional[str]
    reasonFrames: Optional[List[HandledErrorReasonFrame]]


class ErrorGroups:

    nextLink: Optional[str]
    errorGroups: Optional[List[ErrorGroupListItem]]


@deserialize.parser("firstOccurrence", iso8601parse)
@deserialize.parser("lastOccurrence", iso8601parse)
class ErrorGroup:

    state: ErrorGroupState
    annotation: Optional[str]
    errorGroupId: str
    appVersion: str
    appBuild: Optional[str]
    count: int
    deviceCount: int
    firstOccurrence: datetime.datetime
    lastOccurrence: datetime.datetime
    exceptionType: Optional[str]
    exceptionMessage: Optional[str]
    exceptionClassName: Optional[str]
    exceptionClassMethod: Optional[bool]
    exceptionMethod: Optional[str]
    exceptionAppCode: Optional[bool]
    exceptionFile: Optional[str]
    exceptionLine: Optional[str]
    codeRaw: Optional[str]
    reasonFrames: Optional[List[HandledErrorReasonFrame]]


@deserialize.parser("timestamp", iso8601parse)
class HandledError:

    errorId: Optional[str]
    timestamp: Optional[datetime.datetime]
    deviceName: Optional[str]
    osVersion: Optional[str]
    osType: Optional[str]
    country: Optional[str]
    language: Optional[str]
    userId: Optional[str]


class HandledErrors:

    nextLink: Optional[str]
    errors: Optional[List[HandledError]]


@deserialize.parser("timestamp", iso8601parse)
@deserialize.parser("appLaunchTimestamp", iso8601parse)
class HandledErrorDetails:

    errorId: Optional[str]
    timestamp: Optional[datetime.datetime]
    deviceName: Optional[str]
    osVersion: Optional[str]
    osType: Optional[str]
    country: Optional[str]
    language: Optional[str]
    userId: Optional[str]
    name: Optional[str]
    reasonFrames: Optional[List[HandledErrorReasonFrame]]
    appLaunchTimestamp: Optional[datetime.datetime]
    carrierName: Optional[str]
    jailbreak: Optional[bool]
    properties: Optional[Dict[str, str]]


class ReleaseOrigin(enum.Enum):
    HOCKEY = "hockeyapp"
    APP_CENTER = "appcenter"


class BuildInfo:
    branch_name: Optional[str]
    commit_hash: Optional[str]
    commit_message: Optional[str]

    def __init__(
        self,
        branch_name: Optional[str] = None,
        commit_hash: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> None:
        self.branch_name = branch_name
        self.commit_hash = commit_hash
        self.commit_message = commit_message

    def json(self) -> Dict[str, Any]:
        result = {}

        if self.branch_name is not None:
            result["branch_name"] = self.branch_name

        if self.commit_hash is not None:
            result["commit_hash"] = self.commit_hash

        if self.commit_message is not None:
            result["commit_message"] = self.commit_message

        return result


class StoreType(enum.Enum):
    INTUNE = "intune"
    GOOGLE_PLAY = "googleplay"
    APPLE = "apple"
    NONE = "none"


class DestinationType(enum.Enum):
    GROUP = "group"
    STORE = "store"
    TESTER = "tester"


@deserialize.key("identifier", "id")
@deserialize.key("store_type", "type")
class Destination:
    identifier: str
    name: Optional[str]
    is_latest: Optional[bool]
    store_type: Optional[StoreType]
    publishing_status: Optional[str]
    destination_type: Optional[DestinationType]
    display_name: Optional[str]


@deserialize.key("identifier", "id")
@deserialize.parser("uploaded_at", iso8601parse)
class BasicReleaseDetailsResponse:

    identifier: int
    version: str
    origin: Optional[ReleaseOrigin]
    short_version: str
    enabled: bool
    uploaded_at: datetime.datetime
    destinations: Optional[List[Destination]]
    build: Optional[BuildInfo]


class ProvisioningProfileType(enum.Enum):
    ADHOC = "adhoc"
    ENTERPRISE = "enterprise"
    OTHER = "other"


@deserialize.key("identifier", "id")
@deserialize.parser("provisioning_profile_expiry_date", iso8601parse)
@deserialize.parser("uploaded_at", iso8601parse)
class ReleaseDetailsResponse:

    # ID identifying this unique release.
    identifier: int

    # The app's name (extracted from the uploaded release).
    app_name: str

    # The app's display name.
    app_display_name: str

    # The app's OS.
    app_os: Optional[str]

    # The release's version.
    version: str

    # The release's origin
    origin: Optional[ReleaseOrigin]

    # The release's short version.
    short_version: str

    # The release's release notes.
    release_notes: Optional[str]

    # The release's provisioning profile name.
    provisioning_profile_name: Optional[str]

    # The type of the provisioning profile for the requested app version.
    provisioning_profile_type: Optional[ProvisioningProfileType]

    # expiration date of provisioning profile in UTC format.
    provisioning_profile_expiry_date: Optional[datetime.datetime]

    # A flag that determines whether the release's provisioning profile is still extracted or not.
    is_provisioning_profile_syncing: Optional[bool]

    # The release's size in bytes.
    size: Optional[int]

    # The release's minimum required operating system.
    min_os: Optional[str]

    # The release's device family.
    device_family: Optional[str]

    # The release's minimum required Android API level.
    android_min_api_level: Optional[str]

    # The identifier of the apps bundle.
    bundle_identifier: Optional[str]

    # Hashes for the packages
    package_hashes: Optional[List[str]]

    # MD5 checksum of the release binary.
    fingerprint: Optional[str]

    # The uploaded time.
    uploaded_at: datetime.datetime

    # The URL that hosts the binary for this release.
    download_url: Optional[str]

    # A URL to the app's icon.
    app_icon_url: Optional[str]

    # The href required to install a release on a mobile device. On iOS devices will be prefixed
    # with itms-services://?action=download-manifest&url=
    install_url: Optional[str]

    destinations: Optional[List[Destination]]

    # In calls that allow passing udid in the query string, this value will hold the provisioning
    # status of that UDID in this release. Will be ignored for non-iOS platforms.
    is_udid_provisioned: Optional[bool]

    # In calls that allow passing udid in the query string, this value determines if a release can
    # be re-signed. When true, after a re-sign, the tester will be able to install the release from
    # his registered devices. Will not be returned for non-iOS platforms.
    can_resign: Optional[bool]

    build: Optional[BuildInfo]

    # This value determines the whether a release currently is enabled or disabled.
    enabled: bool

    # Status of the release.
    status: Optional[str]


class ReleaseWithDistributionGroup:

    release: int  # The release ID
    distribution_group: str  # The distribution group ID

    def __init__(self, release: int, distribution_group: str) -> None:
        self.release = release
        self.distribution_group = distribution_group


class ReleaseCount:
    release_id: str
    distribution_group: Optional[str]
    unique_count: int
    total_count: int


class ReleaseCounts:
    total: Optional[int]
    counts: List[ReleaseCount]


@deserialize.key("identifier", "id")
class SetUploadMetadataResponse:
    identifier: str
    error: bool
    chunk_size: int
    resume_restart: bool
    chunk_list: List[int]
    blob_partitions: int
    status_code: str


class ChunkUploadResponse:
    error: bool
    chunk_num: int
    error_code: str


@deserialize.key("identifier", "id")
class CreateReleaseUploadResponse:
    identifier: str
    upload_domain: str
    token: str
    url_encoded_token: str
    package_asset_id: str


@deserialize.key("identifier", "id")
class CommitUploadResponse:
    identifier: str
    upload_status: str
    release_distinct_id: Optional[int]


@deserialize.key("identifier", "id")
class UploadCompleteResponse:
    absolute_uri: str
    chunk_num: int
    error: bool
    error_code: Optional[str]
    location: str
    message: str
    raw_location: str
    state: str


@deserialize.key("identifier", "id")
class ReleaseDestinationResponse:
    identifier: str
    mandatory_update: bool
    provisioning_status_url: Optional[str]


@deserialize.key("identifier", "id")
class DestinationId:
    name: Optional[str]
    identifier: Optional[str]

    def __init__(self, *, name: Optional[str] = None, identifier: Optional[str] = None) -> None:
        self.name = name
        self.identifier = identifier

    def json(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        if self.name is not None:
            result["name"] = self.name

        if self.identifier is not None:
            result["id"] = self.identifier

        return result


class ReleaseUpdateRequest:

    release_notes: Optional[str]
    mandatory_update: Optional[bool]
    destinations: Optional[List[DestinationId]]
    build: Optional[BuildInfo]
    notify_testers: Optional[bool]

    def __init__(
        self,
        *,
        release_notes: Optional[str] = None,
        mandatory_update: Optional[bool] = None,
        destinations: Optional[List[DestinationId]] = None,
        build: Optional[BuildInfo] = None,
        notify_testers: Optional[bool] = None,
    ) -> None:
        self.release_notes = release_notes
        self.mandatory_update = mandatory_update
        self.destinations = destinations
        self.build = build
        self.notify_testers = notify_testers

    def json(self) -> Dict[str, Any]:
        output: Dict[str, Any] = {}

        if self.release_notes is not None:
            output["release_notes"] = self.release_notes

        if self.mandatory_update is not None:
            output["mandatory_update"] = self.mandatory_update

        if self.destinations is not None:
            output["destinations"] = [destination.json() for destination in self.destinations]

        if self.build is not None:
            output["build"] = self.build.json()

        if self.notify_testers is not None:
            output["notify_testers"] = self.notify_testers

        return output


class SymbolType(enum.Enum):
    APPLE = "Apple"
    JAVASCRIPT = "JavaScript"
    BREAKPAD = "Breakpad"
    PROGUARD = "AndroidProguard"
    UWP = "UWP"


@deserialize.parser("expiration_date", iso8601parse)
class SymbolUploadBeginResponse:
    symbol_upload_id: str
    upload_url: str
    expiration_date: datetime.datetime


class SymbolUploadStatus(enum.Enum):
    COMMITTED = "committed"
    ABORTED = "aborted"


class SymbolUploadEndRequest:
    status: SymbolUploadStatus


class Origin(enum.Enum):
    APP_CENTER = "appcenter"
    HOCKEY = "hockeyapp"
    CODEPUSH = "codepush"


class Permission(enum.Enum):
    MANAGER = "manager"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    TESTER = "tester"


class Role(enum.Enum):
    ADMIN = "admin"
    COLLABORATOR = "collaborator"
    MEMBER = "member"


@deserialize.key("identifier", "id")
class User:

    # The unique ID of the user
    identifier: str

    # The avatar URL of the user
    avatar_url: Optional[str]

    # User is required to send an old password in order to change the password
    can_change_password: Optional[bool]

    # The full name of the user. Might for example be first and last name
    display_name: str

    # The email address of the user
    email: str

    # The unique name that is used to identify the user
    name: str

    # The permissions the user has for the app
    permissions: List[Permission]

    # The creation origin of this user
    origin: Origin


@deserialize.key("identifier", "id")
@deserialize.parser("created_at", iso8601parse)
class UserToken:

    # The unique ID of the token
    identifier: str

    # The user supplied description for the token
    description: str

    # The scope the token has
    scope: List[str]

    # The creation date
    created_at: datetime.datetime

    # The value of the token - Only set when creating a new tokern
    api_token: Optional[str]
