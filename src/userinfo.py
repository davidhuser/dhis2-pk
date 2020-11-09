#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from collections import namedtuple

from dhis2 import setup_logger, logger

try:
    from common.utils import create_api, file_timestamp, write_csv
    from common.exceptions import PKClientException
except (SystemError, ImportError):
    from src.common.utils import create_api, file_timestamp, write_csv
    from src.common.exceptions import PKClientException


def replace_path(oumap, path):
    """ Replace path UIDs with readable OU names"""
    pattern = re.compile(r'\b(' + '|'.join(oumap.keys()) + r')\b')
    result = pattern.sub(lambda x: oumap[x.group()], path)
    return u'{}'.format(result)


def format_user(users, ou_map):
    User = namedtuple('User', 'name first_name surname username phone_number '
                              'last_login user_groups user_roles org_units dv_org_units')
    logger.info('Exporting {} users...'.format(len(users['users'])))

    for user in users['users']:
        User.name = u'{}'.format(user['name'])
        User.first_name = u'{}'.format(user['userCredentials']['userInfo']['firstName'])
        User.surname = u'{}'.format(user['userCredentials']['userInfo']['surname'])
        User.username = u'{}'.format(user['userCredentials']['username'])
        User.phone_number = u'{}'.format(user['userCredentials']['userInfo'].get('phoneNumber', '-'))
        User.last_login = u'{}'.format(user['userCredentials'].get('lastLogin', '-'))
        User.user_groups = ", ".join([ug['name'] for ug in user['userGroups']])
        User.user_roles = ", ".join([ur['name'] for ur in user['userCredentials']['userRoles']])
        User.org_units = u"\n".join([replace_path(ou_map, elem) for elem in [ou['path'] for ou in user['organisationUnits']]])
        User.dv_org_units = u"\n".join([replace_path(ou_map, elem) for elem in [ou['path'] for ou in user['dataViewOrganisationUnits']]])
        yield User


def main(args, password):
    setup_logger()

    api = create_api(server=args.server, username=args.username, password=password)

    params1 = {
        'fields':
            'name,'
            'userCredentials[username,lastLogin,userRoles[name],userInfo[phoneNumber,firstName,surname]],'
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

    file_name = "userinfo-{}.csv".format(file_timestamp(api.api_url))
    data = []
    header_row = ['name', 'firstName', 'surname', 'username', 'phoneNumber', 'lastLogin', 'userGroups',
                  'userRoles', 'orgunitPaths', 'dataViewOrgunitPaths']

    for user in format_user(users, ou_map):
        data.append([
            user.name,
            user.first_name,
            user.surname,
            user.username,
            user.phone_number,
            user.last_login,
            user.user_groups,
            user.user_roles,
            user.org_units,
            user.dv_org_units
        ])

    write_csv(data, file_name, header_row)
    logger.info("Success! CSV file exported to {}".format(file_name))