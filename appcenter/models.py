"""Data type models"""

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import datetime
import enum
from typing import Any

import deserialize


def iso8601parse(date_string: str | None) -> datetime.datetime | None:
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

    className: str | None  # name of the class
    method: str | None  # name of the method
    classMethod: bool | None  # is a class method
    file: str | None  # name of the file
    line: int | None  # line number
    appCode: bool | None  # this line isn't from any framework
    frameworkName: str | None  # Name of the framework
    codeFormatted: str | None  # Formatted frame string
    codeRaw: str | None  # Unformatted Frame string
    methodParams: str | None  # parameters of the frames method
    exceptionType: str | None  # Exception type.
    osExceptionType: str | None  # OS exception type. (aka. SIGNAL)
    language: ProgrammingLanguage | None  # programming language of the frame


class ErrorGroupState(enum.Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    IGNORED = "Ignored"


@deserialize.parser("firstOccurrence", iso8601parse)
@deserialize.parser("lastOccurrence", iso8601parse)
class ErrorGroupListItem:
    state: ErrorGroupState
    annotation: str | None
    errorGroupId: str
    appVersion: str
    appBuild: str | None
    count: int
    deviceCount: int
    firstOccurrence: datetime.datetime
    lastOccurrence: datetime.datetime
    exceptionType: str | None
    exceptionMessage: str | None
    exceptionClassName: str | None
    exceptionClassMethod: bool | None
    exceptionMethod: str | None
    exceptionAppCode: bool | None
    exceptionFile: str | None
    exceptionLine: str | None
    codeRaw: str | None
    reasonFrames: list[HandledErrorReasonFrame] | None


class ErrorGroups:
    nextLink: str | None
    errorGroups: list[ErrorGroupListItem] | None


@deserialize.parser("firstOccurrence", iso8601parse)
@deserialize.parser("lastOccurrence", iso8601parse)
class ErrorGroup:
    state: ErrorGroupState
    annotation: str | None
    errorGroupId: str
    appVersion: str
    appBuild: str | None
    count: int
    deviceCount: int
    firstOccurrence: datetime.datetime
    lastOccurrence: datetime.datetime
    exceptionType: str | None
    exceptionMessage: str | None
    exceptionClassName: str | None
    exceptionClassMethod: bool | None
    exceptionMethod: str | None
    exceptionAppCode: bool | None
    exceptionFile: str | None
    exceptionLine: str | None
    codeRaw: str | None
    reasonFrames: list[HandledErrorReasonFrame] | None


@deserialize.parser("timestamp", iso8601parse)
class HandledError:
    errorId: str | None
    timestamp: datetime.datetime | None
    deviceName: str | None
    osVersion: str | None
    osType: str | None
    country: str | None
    language: str | None
    userId: str | None


class HandledErrors:
    nextLink: str | None
    errors: list[HandledError] | None


@deserialize.parser("timestamp", iso8601parse)
@deserialize.parser("appLaunchTimestamp", iso8601parse)
class HandledErrorDetails:
    errorId: str | None
    timestamp: datetime.datetime | None
    deviceName: str | None
    osVersion: str | None
    osType: str | None
    country: str | None
    language: str | None
    userId: str | None
    name: str | None
    reasonFrames: list[HandledErrorReasonFrame] | None
    appLaunchTimestamp: datetime.datetime | None
    carrierName: str | None
    jailbreak: bool | None
    properties: dict[str, str | None]


class ReleaseOrigin(enum.Enum):
    HOCKEY = "hockeyapp"
    APP_CENTER = "appcenter"


@deserialize.auto_snake()
class BuildInfo:
    branch_name: str | None
    commit_hash: str | None
    commit_message: str | None

    def __init__(
        self,
        branch_name: str | None = None,
        commit_hash: str | None = None,
        commit_message: str | None = None,
    ) -> None:
        self.branch_name = branch_name
        self.commit_hash = commit_hash
        self.commit_message = commit_message

    def json(self) -> dict[str, Any]:
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
    name: str | None
    is_latest: bool | None
    store_type: StoreType | None
    publishing_status: str | None
    destination_type: DestinationType | None
    display_name: str | None


@deserialize.key("identifier", "id")
@deserialize.parser("uploaded_at", iso8601parse)
class BasicReleaseDetailsResponse:
    identifier: int
    version: str
    origin: ReleaseOrigin | None
    short_version: str
    enabled: bool
    uploaded_at: datetime.datetime
    destinations: list[Destination] | None
    build: BuildInfo | None


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
    app_os: str | None

    # The release's version.
    version: str

    # The release's origin
    origin: ReleaseOrigin | None

    # The release's short version.
    short_version: str

    # The release's release notes.
    release_notes: str | None

    # The release's provisioning profile name.
    provisioning_profile_name: str | None

    # The type of the provisioning profile for the requested app version.
    provisioning_profile_type: ProvisioningProfileType | None

    # expiration date of provisioning profile in UTC format.
    provisioning_profile_expiry_date: datetime.datetime | None

    # A flag that determines whether the release's provisioning profile is still extracted or not.
    is_provisioning_profile_syncing: bool | None

    # The release's size in bytes.
    size: int | None

    # The release's minimum required operating system.
    min_os: str | None

    # The release's device family.
    device_family: str | None

    # The release's minimum required Android API level.
    android_min_api_level: str | None

    # The identifier of the apps bundle.
    bundle_identifier: str | None

    # Hashes for the packages
    package_hashes: list[str | None]

    # MD5 checksum of the release binary.
    fingerprint: str | None

    # The uploaded time.
    uploaded_at: datetime.datetime

    # The URL that hosts the binary for this release.
    download_url: str | None

    # A URL to the app's icon.
    app_icon_url: str | None

    # The href required to install a release on a mobile device. On iOS devices will be prefixed
    # with itms-services://?action=download-manifest&url=
    install_url: str | None

    destinations: list[Destination] | None

    # In calls that allow passing udid in the query string, this value will hold the provisioning
    # status of that UDID in this release. Will be ignored for non-iOS platforms.
    is_udid_provisioned: bool | None

    # In calls that allow passing udid in the query string, this value determines if a release can
    # be re-signed. When true, after a re-sign, the tester will be able to install the release from
    # his registered devices. Will not be returned for non-iOS platforms.
    can_resign: bool | None

    build: BuildInfo | None

    # This value determines the whether a release currently is enabled or disabled.
    enabled: bool

    # Status of the release.
    status: str | None


class ReleaseWithDistributionGroup:
    release: int  # The release ID
    distribution_group: str  # The distribution group ID

    def __init__(self, release: int, distribution_group: str) -> None:
        self.release = release
        self.distribution_group = distribution_group


class ReleaseCount:
    release_id: str
    distribution_group: str | None
    unique_count: int
    total_count: int


class ReleaseCounts:
    total: int | None
    counts: list[ReleaseCount]


@deserialize.key("identifier", "id")
class SetUploadMetadataResponse:
    identifier: str
    error: bool
    chunk_size: int
    resume_restart: bool
    chunk_list: list[int]
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
    release_distinct_id: int | None


@deserialize.key("identifier", "id")
class UploadCompleteResponse:
    absolute_uri: str
    chunk_num: int
    error: bool
    error_code: str | None
    location: str
    message: str
    raw_location: str
    state: str


@deserialize.key("identifier", "id")
class ReleaseDestinationResponse:
    identifier: str
    mandatory_update: bool
    provisioning_status_url: str | None


@deserialize.key("identifier", "id")
class DestinationId:
    name: str | None
    identifier: str | None

    def __init__(self, *, name: str | None = None, identifier: str | None = None) -> None:
        self.name = name
        self.identifier = identifier

    def json(self) -> dict[str, Any]:
        result: dict[str, Any] = {}

        if self.name is not None:
            result["name"] = self.name

        if self.identifier is not None:
            result["id"] = self.identifier

        return result


class ReleaseUpdateRequest:
    release_notes: str | None
    mandatory_update: bool | None
    destinations: list[DestinationId] | None
    build: BuildInfo | None
    notify_testers: bool | None

    def __init__(
        self,
        *,
        release_notes: str | None = None,
        mandatory_update: bool | None = None,
        destinations: list[DestinationId] | None = None,
        build: BuildInfo | None = None,
        notify_testers: bool | None = None,
    ) -> None:
        self.release_notes = release_notes
        self.mandatory_update = mandatory_update
        self.destinations = destinations
        self.build = build
        self.notify_testers = notify_testers

    def json(self) -> dict[str, Any]:
        output: dict[str, Any] = {}

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
    MAINTAINER = "maintainer"


@deserialize.key("identifier", "id")
class User:
    # The unique ID of the user
    identifier: str

    # The avatar URL of the user
    avatar_url: str | None

    # User is required to send an old password in order to change the password
    can_change_password: bool | None

    # The full name of the user. Might for example be first and last name
    display_name: str

    # The email address of the user
    email: str

    # The unique name that is used to identify the user
    name: str

    # The permissions the user has for the app
    permissions: list[Permission]

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
    scope: list[str]

    # The creation date
    created_at: datetime.datetime

    # The value of the token - Only set when creating a new tokern
    api_token: str | None


@deserialize.parser("joined_at", iso8601parse)
class OrganizationUserResponse:
    # The email address of the user
    email: str

    # The full name of the user. Might for example be first and last name
    display_name: str

    # The date when the user joined the organization
    joined_at: datetime.datetime | None

    # The unique name that is used to identify the user.
    name: str

    # The role the user has within the organization
    role: Role


@deserialize.key("identifier", "id")
class TeamResponse:
    # The unique ID of the team
    identifier: str

    # The name of the team
    name: str

    # The display name of the team
    display_name: str

    # The description of the team
    description: str | None


class OwnerType(enum.Enum):
    ORG = "org"
    USER = "user"


@deserialize.key("identifier", "id")
class Owner:
    # The unique id (UUID) of the owner
    id: str

    # The avatar URL of the owner
    avatar_url: str | None

    # The owner's display name
    display_name: str

    # The owner's email address
    email: str | None

    # The unique name that used to identify the owner
    name: str

    # The owner type. Can either be 'org' or 'user'
    type: OwnerType


class AzureSubscriptionResponse:

    # The azure subscription id
    subscription_id: str

    # The tenant id of the azure subscription belongs to
    tenant_id: str

    # The name of the azure subscription
    subscription_name: str

    # If the subscription is used for billing
    is_billing: bool | None

    # If the subscription can be used for billing
    is_billable: bool | None

    # If the subscription is internal Microsoft subscription
    is_microsoft_internal: bool | None


@deserialize.parser("created_at", iso8601parse)
@deserialize.parser("updated_at", iso8601parse)
class AppResponse:

    # The unique ID (UUID) of the app
    id: str

    # The description of the app
    description: str | None

    # The display name of the app
    display_name: str

    # A one-word descriptive release-type value that starts with a capital letter but is otherwise lowercase
    release_type: str | None

    # The string representation of the URL pointing to the app's icon
    icon_url: str | None

    # The string representation of the source of the app's icon
    icon_source: str | None

    # The name of the app used in URLs
    name: str

    # The OS the app will be running on
    os: str

    # The information about the app's owner
    owner: Owner

    # A unique and secret key used to identify the app in communication with the ingestion endpoint for crash reporting
    # and analytics
    app_secret: str

    #
    azure_subscription: AzureSubscriptionResponse | None

    # The platform of the app
    platform: str

    # The creation origin of the app
    origin: ReleaseOrigin

    # The created date of this app
    created_at: datetime.datetime | None

    # The last updated date of this app
    updated_at: datetime.datetime | None

    # The permissions of the calling user
    member_permissions: list[Permission]
