import csv
import sys
from datetime import datetime

from dhis2 import Api, logger

try:
    from __version__ import __version__
except (SystemError, ImportError):
    from pk.__version__ import __version__


def create_api(server=None, username=None, password=None, api_version=None):
    """Return a fully configured dhis2.Dhis instance"""
    if not any([server, username, password]):
        api = Api.from_auth_file(api_version=api_version, user_agent='dhis2-pk/{}'.format(__version__))
        logger.info("Found a file for server {}".format(api.base_url))
        return api
    else:
        return Api(server, username, password, api_version, 'dhis2-pk/{}'.format(__version__))


def write_csv(data, filename, header_row):
    """Write CSV data for both Python2 and Python3"""
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
    """Create string that can be used as file name including server URL and timestamp"""
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return '{}_{}'.format(now, url.replace('https://', '').replace('.', '-').replace('/', '-'))

