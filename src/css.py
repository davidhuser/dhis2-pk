#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
post-css
~~~~~~~~~~~~~~~~~
POST a CSS stylesheet to a server
"""

import os

from dhis2 import setup_logger, logger

try:
    from src.common.utils import create_api
    from src.common.exceptions import PKClientException
except (SystemError, ImportError):
    from common.utils import create_api
    from common.exceptions import PKClientException


def post_file(api, filename, content_type='text/css'):
    api.session.headers = {"Content-Type": content_type}
    file_read = open(filename, 'rb').read()
    api.session.post(url='{}/files/style'.format(api.api_url), data=file_read)


def validate_file(filename):
    if not os.path.exists(filename):
        raise PKClientException("File does not exist: {}".format(filename))
    if not os.path.getsize(filename) > 0:
        raise PKClientException("File is empty: {}".format(filename))


def main(args, password):
    setup_logger(include_caller=False)
    api = create_api(server=args.server, username=args.username, password=password)
    validate_file(args.css)
    post_file(api, filename=args.css)
    logger.info("{} CSS posted to {}. Clear your Browser cache / use Incognito.".format(args.css, api.api_url))
