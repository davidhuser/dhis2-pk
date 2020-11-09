class DHIS2PocketKnifeException(Exception):
    """The base dhis2-src Exception that all other exception classes extend."""


class PKClientException(DHIS2PocketKnifeException):
    """Indicate exceptions that don't involve interaction with DHIS2's API."""
