#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import re

from colorama import Style
from dhis2 import setup_logger, logger, APIException

try:
    from pk.common.utils import create_api, file_timestamp, write_csv
    from pk.common.exceptions import PKClientException
except (SystemError, ImportError):
    from common.utils import create_api, file_timestamp, write_csv
    from common.exceptions import PKClientException


def parse_args():
    description = "{}Analyze validation rule expressions.{}".format(Style.BRIGHT, Style.RESET_ALL)
    usage = "\n{}Example:{} dhis2-pk-validation-rules -s play.dhis2.org/demo -u admin -p district".format(
        Style.BRIGHT, Style.RESET_ALL)

    parser = argparse.ArgumentParser(usage=usage, description=description)
    parser.add_argument('-s', dest='server', action='store',
                        help="DHIS2 server URL")
    parser.add_argument('-u', dest='username', action='store', help="DHIS2 username")
    parser.add_argument('-p', dest='password', action='store', help="DHIS2 password")
    parser.add_argument('-v', dest='api_version', action='store', required=False, type=int,
                        help='DHIS2 API version e.g. -v=28')
    return parser.parse_args()


def extract_uids(rule):
    expressions = rule['leftSide']['expression'] + rule['rightSide']['expression']
    list_of_uids = re.findall(r'[A-Za-z][A-Za-z0-9]{10}', expressions)
    if not list_of_uids:
        logger.warn('Expression without UIDs. Check rule {}'.format(json.dumps(rule)))
    return list_of_uids


def main():
    setup_logger()
    args = parse_args()

    api = create_api(server=args.server, username=args.username, password=args.password)

    p = {'fields': 'id,name,description,leftSide[expression],rightSide[expression]', 'paging': False}
    data = api.get('validationRules', params=p).json()

    uid_cache = set()
    for i, rule in enumerate(data['validationRules'], 1):
        info_msg = "{}/{} Analyzing Validation Rule '{}' ({})"
        logger.info(info_msg.format(i, len(data['validationRules']), rule['name'], rule['id']))

        uids_in_expressions = extract_uids(rule)
        for uid in uids_in_expressions:
            if uid not in uid_cache:
                try:
                    api.get('identifiableObjects/{}'.format(uid)).json()
                except APIException as exc:
                    if exc.code == 404:
                        logger.warn("UID in expression not identified: {}".format(uid))
                    else:
                        logger.error(exc)
                else:
                    uid_cache.add(uid)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warn("Aborted.")
    except PKClientException as e:
        logger.error(e)
    except Exception as e:
        logger.exception(e)
