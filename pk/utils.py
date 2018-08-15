import csv
import sys
import re
from datetime import datetime

from dhis2 import Dhis, logger, ClientException

try:
    from __version__ import __version__
except (SystemError, ImportError):
    from .__version__ import __version__


def create_api(server=None, username=None, password=None, api_version=None):
    if not any([server, username, password]):
        try:
            api = Dhis.from_auth_file(api_version=api_version, user_agent='dhis2-pk/{}'.format(__version__))
        except ClientException:
            logger.exception("Problems accessing a dish.json file")
            sys.exit(1)
        else:
            logger.info("Found a file for server {}".format(api.base_url))
            return api
    else:
        try:
            return Dhis(server, username, password, api_version, 'dhis2-pk/{}'.format(__version__))
        except ClientException:
            logger.exception("Problem instantiating a dhis2.py instance")
            sys.exit(1)


def log_and_exit(message):
    logger.error(u'{}'.format(message))
    sys.exit(1)


def write_csv(data, filename, header_row):
    kwargs = {'newline': ''}
    mode = 'w'
    if sys.version_info < (3, 0):
        kwargs.pop('newline', None)
        mode = 'wb'

    with open(filename, mode, **kwargs) as fp:
        writer = csv.writer(fp, delimiter=str(','))
        writer.writerow(header_row)
        writer.writerows(data)


def file_timestamp(url):
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return '{}_{}'.format(now, url.replace('https://', '').replace('.', '-').replace('/', '-'))


def valid_uid(uid):
    """Check if string matches DHIS2 UID pattern"""
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9]{10}$", uid))
