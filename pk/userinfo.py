#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import re
from collections import namedtuple

from dhis2 import logger

import common


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
    return u'{}'.format(result)


def format_user(users, ou_map):
    User = namedtuple('User', 'name first_name surname username phone_number '
                              'user_groups user_roles org_units dv_org_units')
    logger.info('Exporting {} users...'.format(len(users['users'])))

    for user in users['users']:
        User.name = u'{}'.format(user['name'])
        User.first_name = u'{}'.format(user['userCredentials']['userInfo']['firstName'])
        User.surname = u'{}'.format(user['userCredentials']['userInfo']['surname'])
        User.username = u'{}'.format(user['userCredentials']['username'])
        User.phone_number = u'{}'.format(user['userCredentials']['userInfo'].get('phoneNumber', '-'))
        User.user_groups = ", ".join([ug['name'] for ug in user['userGroups']])
        User.user_roles = ", ".join([ur['name'] for ur in user['userCredentials']['userRoles']])
        User.org_units = u"\n".join([replace_path(ou_map, elem) for elem in [ou['path'] for ou in user['organisationUnits']]])
        User.dv_org_units = u"\n".join([replace_path(ou_map, elem) for elem in [ou['path'] for ou in user['dataViewOrganisationUnits']]])
        yield User


def main():
    args = parse_args()

    api = common.create_api(server=args.server, username=args.username, password=args.password)
    file_timestamp = common.file_timestamp(api.api_url)

    params1 = {
        'fields':
            'name,'
            'userCredentials[username,userRoles[name],userInfo[phoneNumber,firstName,surname]],'
            'organisationUnits[path],userGroups[name],'
            'dataViewOrganisationUnits[path]',
        'paging': False
    }
    users = api.get(endpoint='users', params=params1).json()

    params2 = {
        'fields': 'id,name',
        'paging': False
    }

    ou_map = {
        ou['id']: ou['name']
        for ou in api.get(endpoint='organisationUnits', params=params2).json()['organisationUnits']
    }

    file_name = "userinfo-{}.csv".format(file_timestamp)
    data = []
    header_row = ['name', 'firstName', 'surname', 'username', 'phoneNumber', 'userGroups',
                  'userRoles', 'orgunitPaths', 'dataViewOrgunitPaths']

    for user in format_user(users, ou_map):
        data.append([
            user.name,
            user.first_name,
            user.surname,
            user.username,
            user.phone_number,
            user.user_groups,
            user.user_roles,
            user.org_units,
            user.dv_org_units
        ])

    common.write_csv(data, file_name, header_row)
    logger.info("Success! CSV file exported to {}".format(file_name))


if __name__ == "__main__":
    main()
