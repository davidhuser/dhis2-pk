"""dhis2-pk exception classes.
Includes two main exceptions: :class:`.APIException` for when something goes
wrong on the server side, and :class:`.ClientException` when something goes
wrong on the client side. Both of these classes extend :class:`.Dhis2PocketKnifeException`.
"""

from logzero import logger


class DHIS2PocketKnifeException(Exception):
    """The base dhis2-pk Exception that all other exception classes extend."""

    def __init__(self, message, response=None):
        self.message = message
        if response:
            logger.exception("{}\n{}".format(message, response))
        else:
            logger.exception(message)


class APIException(DHIS2PocketKnifeException):
    """Indicate exception that involve responses from DHIS2's API."""


class ClientException(DHIS2PocketKnifeException):
    """Indicate exceptions that don't involve interaction with DHIS2's API."""


class ArgumentException(ClientException):
    """ Indicate exception triggered by faulty arguments"""
    pass


class UserGroupNotFoundException(ArgumentException):
    """ User Group not found on DHIS2"""


class ObjectNotFoundException(ArgumentException):
    """ Share-able object not found"""
