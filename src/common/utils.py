import csv
import sys
from datetime import datetime

from dhis2 import Api, logger

try:
    from __version__ import __version__
except (SystemError, ImportError):
    from src.__version__ import __version__


def create_api(server, username, password):
    """Return a fully configured dhis2.Dhis instance
    """
    return Api(server=server, username=username, password=password, user_agent='dhis2-src/{}'.format(__version__))


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

