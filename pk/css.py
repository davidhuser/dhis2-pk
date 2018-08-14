#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
post-css
~~~~~~~~~~~~~~~~~
POST a CSS stylesheet to a server
"""

import argparse

from dhis2 import setup_logger, logger
import common


def parse_args():
    parser = argparse.ArgumentParser(usage='%(prog)s [-h] [-s] -c [-u] [-p] [-d]',
                                     description="Post CSS stylesheet to a server")
    parser.add_argument('-s', dest='server', action='store', help="DHIS2 server URL, e.g. 'play.dhis2.org/demo'")
    parser.add_argument('-c', dest='css', action='store', required=True, help="CSS file")
    parser.add_argument('-u', dest='username', action='store', help='DHIS2 username, e.g. -u=admin')
    parser.add_argument('-p', dest='password', action='store', help='DHIS2 password, e.g. -p=district')
    return parser.parse_args()


def post_file(api, filename, content_type='text/css'):
    api.session.headers = {"Content-Type": content_type}
    file_read = open(filename, 'rb').read()
    api.session.post(url='{}/files/style'.format(api.api_url), data=file_read)


def main():
    args = parse_args()
    setup_logger()
    api = common.create_api(server=args.server, username=args.username, password=args.password)

    post_file(api, filename=args.css)
    logger.info("{} CSS posted to {}. Clear your Browser cache / use Incognito.".format(args.css, api.api_url))


if __name__ == "__main__":
    main()
