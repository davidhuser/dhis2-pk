#!/usr/bin/env python

import argparse
import re

import unicodecsv as csv

from src.core.dhis import Dhis
from src.core.logger import *


def parse_args():
    parser = argparse.ArgumentParser(description="Create CSV of orgunits / usergroups of users")
    parser.add_argument('-s', dest='server', action='store',
                        help="DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo", required=True)
    parser.add_argument('-u', dest='username', action='store', help="DHIS2 username", required=True)
    parser.add_argument('-p', dest='password', action='store', help="DHIS2 password", required=True)
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
    init_logger(args.debug)
    log_start_info(__file__)

    dhis = Dhis(server=args.server, username=args.username, password=args.password, api_version=args.api_version)
    params1 = {
        'fields': 'dataViewOrganisationUnits[path],userCredentials[username],name,'
                  'organisationUnits[path],userGroups[name],userRoles[name]',
        'paging': False
    }
    users = dhis.get(endpoint='users', file_type='json', params=params1)

    params2 = {
        'fields': 'id,name',
        'paging': False
    }
    orgunits = dhis.get(endpoint='organisationUnits', file_type='json', params=params2)
    oumap = {ou['id']: ou['name'] for ou in orgunits['organisationUnits']}

    file_name = "userinfo-{}.csv".format(dhis.file_timestamp)

    with open(file_name, 'wb') as csvfile:
        fieldnames = ['name', 'username', 'userGroups', 'userRoles', 'orgunitPaths', 'dataViewOrgunitPaths']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, encoding='utf-8', delimiter=',',
                                quoting=csv.QUOTE_MINIMAL)

        writer.writeheader()
        for u in users['users']:
            export = {
                'name': u['name'],
                'username': u['userCredentials']['username'],
                'userGroups': ", ".join([ug['name'] for ug in u['userGroups']]),
                'userRoles': ", ".join([ug['name'] for ug in u['userRoles']])
            }
            orgunits = [ou['path'] for ou in u['organisationUnits']]
            export['orgunitPaths'] = "\n".join([replace_path(oumap, elem) for elem in orgunits])

            dvorgunits = [ou['path'] for ou in u['dataViewOrganisationUnits']]
            export['dataViewOrgunitPaths'] = "\n".join([replace_path(oumap, elem) for elem in dvorgunits])

            writer.writerow(export)
        log_info(u"+++ Success! CSV file exported to {}".format(file_name))


if __name__ == "__main__":
    main()
