#!/usr/bin/env python

import argparse
import re

import unicodecsv as csv
from logzero import logger

try:
    from pk.core import log
    from pk.core import dhis
    from pk.core import exceptions
except ImportError:
    from core import log
    from core import dhis
    from core import exceptions


def parse_args():
    parser = argparse.ArgumentParser(description="Create CSV of orgunits / usergroups of users")
    parser.add_argument('-s', dest='server', action='store',
                        help="DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo")
    parser.add_argument('-u', dest='username', action='store', help="DHIS2 username")
    parser.add_argument('-p', dest='password', action='store', help="DHIS2 password")
    parser.add_argument('-v', dest='api_version', action='store', required=False, type=int,
                        help='DHIS2 API version e.g. -v=24')
    parser.add_argument('-d', dest='debug', action='store_true', default=False, required=False,
                        help="Writes more info in log file")

    return parser.parse_args()


def replace_path(oumap, path):
    """ Replace path UIDs with readable OU names"""
    pattern = re.compile(r'\b(' + '|'.join(oumap.keys()) + r')\b')
    result = pattern.sub(lambda x: oumap[x.group()], path)
    return result


def main():
    args = parse_args()
    log.init(args.debug)

    api = dhis.Dhis(server=args.server, username=args.username, password=args.password, api_version=args.api_version)
    params1 = {
        'fields': 'dataViewOrganisationUnits[path],'
                  'userCredentials[username,'
                  'userRoles[name],'
                  'userInfo[phoneNumber,firstName,surname]],'
                  'name,'
                  'organisationUnits[path],userGroups[name]',
        'paging': False
    }
    users = api.get(endpoint='users', file_type='json', params=params1)

    params2 = {
        'fields': 'id,name',
        'paging': False
    }
    orgunits = api.get(endpoint='organisationUnits', file_type='json', params=params2)
    oumap = {ou['id']: ou['name'] for ou in orgunits['organisationUnits']}

    file_name = "userinfo-{}.csv".format(api.file_timestamp)

    with open(file_name, 'wb') as csvfile:
        fieldnames = ['name', 'firstName', 'surname', 'username', 'phoneNumber', 'userGroups',
                      'userRoles', 'orgunitPaths', 'dataViewOrgunitPaths']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, encoding='utf-8', delimiter=',',
                                quoting=csv.QUOTE_MINIMAL)

        writer.writeheader()
        for u in users['users']:
            export = {
                'name': u['name'],
                'firstName': u['userCredentials']['userInfo']['firstName'],
                'surname': u['userCredentials']['userInfo']['surname'],
                'phoneNumber': u['userCredentials']['userInfo'].get('phoneNumber', '-'),
                'username': u['userCredentials']['username'],
                'userGroups': ", ".join([ug['name'] for ug in u['userGroups']]),
                'userRoles': ", ".join([ur['name'] for ur in u['userCredentials']['userRoles']])
            }
            orgunits = [ou['path'] for ou in u['organisationUnits']]
            export['orgunitPaths'] = "\n".join([replace_path(oumap, elem) for elem in orgunits])

            dvorgunits = [ou['path'] for ou in u['dataViewOrganisationUnits']]
            export['dataViewOrgunitPaths'] = "\n".join([replace_path(oumap, elem) for elem in dvorgunits])

            writer.writerow(export)
        logger.info("Success! CSV file exported to {}".format(file_name))


if __name__ == "__main__":
    main()
