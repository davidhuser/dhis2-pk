#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
post-css
~~~~~~~~~~~~~~~~~
POST a CSS stylesheet to a server
"""

import argparse
import os
import getpass

from dhis2 import setup_logger, logger
from colorama import Style

try:
    from pk.common.utils import create_api
    from pk.common.exceptions import PKClientException
except (SystemError, ImportError):
    from common.utils import create_api
    from common.exceptions import PKClientException


def parse_args():
    description = "{}Post CSS stylesheet to a server.{}".format(Style.BRIGHT, Style.RESET_ALL)
    usage = "\n{}Example:{} dhis2-pk-post-css -s=play.dhis2.org/dev -u=admin -p=district -c=file.css".format(Style.BRIGHT, Style.RESET_ALL)
    parser = argparse.ArgumentParser(usage=usage, description=description)

    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    required.add_argument('-c', dest='css', action='store', required=True, help="Path to CSS file")

    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('-s', dest='server', action='store', help="DHIS2 server URL")
    optional.add_argument('-u', dest='username', action='store', help='DHIS2 username')
    optional.add_argument('-p', dest='password', action='store', help='DHIS2 password')
    args = parser.parse_args()

    if not args.password:
        if not args.username:
            raise PKClientException("ArgumentError: Must provide a username via argument -u")
        password = getpass.getpass(prompt="Password for {} @ {}: ".format(args.username, args.server))
    else:
        password = args.password
    return args, password


def post_file(api, filename, content_type='text/css'):
    api.session.headers = {"Content-Type": content_type}
    file_read = open(filename, 'rb').read()
    api.session.post(url='{}/files/style'.format(api.api_url), data=file_read)


def validate_file(filename):
    if not os.path.exists(filename):
        raise PKClientException("File does not exist: {}".format(filename))
    if not os.path.getsize(filename) > 0:
        raise PKClientException("File is empty: {}".format(filename))


def main():
    args, password = parse_args()
    setup_logger(include_caller=False)
    api = create_api(server=args.server, username=args.username, password=password)
    validate_file(args.css)
    post_file(api, filename=args.css)
    logger.info("{} CSS posted to {}. Clear your Browser cache / use Incognito.".format(args.css, api.api_url))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warn("Aborted.")
    except PKClientException as e:
        logger.error(e)
    except Exception as e:
        logger.exception(e)
