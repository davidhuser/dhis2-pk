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


def format_user(users, ou_map, uid_export=False):
    if not uid_export:
        # export readable names
        User = namedtuple('User', 'uid name first_name surname username phone_number email last_login '
                                  'user_groups user_roles org_units dv_org_units search_org_units')
        logger.info('Exporting {} users...'.format(len(users['users'])))

        for user in users['users']:
            User.uid = u'{}'.format(user['id'])
            User.name = u'{}'.format(user['name'])
            User.first_name = u'{}'.format(user['userCredentials']['userInfo']['firstName'])
            User.surname = u'{}'.format(user['userCredentials']['userInfo']['surname'])
            User.username = u'{}'.format(user['userCredentials']['username'])
            User.phone_number = u'{}'.format(user['userCredentials']['userInfo'].get('phoneNumber', '-'))
            User.email = u'{}'.format(user.get('email', '-'))
            User.last_login = u'{}'.format(user['userCredentials'].get('lastLogin', '-'))
            User.user_groups = u", ".join([ug['name'] for ug in user['userGroups']])
            User.user_roles = u", ".join([ur['name'] for ur in user['userCredentials']['userRoles']])
            User.org_units = u"\n".join(
                [replace_path(ou_map, elem) for elem in [ou['path'] for ou in user['organisationUnits']]])
            User.dv_org_units = u"\n".join(
                [replace_path(ou_map, elem) for elem in [ou['path'] for ou in user['dataViewOrganisationUnits']]])
            User.search_org_units = u"\n".join(
                [replace_path(ou_map, elem) for elem in [ou['path'] for ou in user['teiSearchOrganisationUnits']]])
            yield User

    else:
        # export readable names PLUS UIDs
        User = namedtuple('User', 'uid name first_name surname username phone_number email last_login '
                                  'user_groups user_groups_uid '
                                  'user_roles user_roles_uid '
                                  'org_units org_units_uid '
                                  'dv_org_units dv_org_units_uid '
                                  'search_org_units search_org_units_uid')
        logger.info('Exporting {} users including UIDs'.format(len(users['users'])))

        for user in users['users']:
            User.uid = u'{}'.format(user['id'])
            User.name = u'{}'.format(user['name'])
            User.first_name = u'{}'.format(user['userCredentials']['userInfo']['firstName'])
            User.surname = u'{}'.format(user['userCredentials']['userInfo']['surname'])
            User.username = u'{}'.format(user['userCredentials']['username'])
            User.phone_number = u'{}'.format(user['userCredentials']['userInfo'].get('phoneNumber', '-'))
            User.email = u'{}'.format(user.get('email', '-'))
            User.last_login = u'{}'.format(user['userCredentials'].get('lastLogin', '-'))
            User.user_groups = u", ".join([ug['name'] for ug in user['userGroups']])
            User.user_groups_uid = u",".join([ug['id'] for ug in user['userGroups']])
            User.user_roles = u", ".join([ur['name'] for ur in user['userCredentials']['userRoles']])
            User.user_roles_uid = u",".join([ur['id'] for ur in user['userCredentials']['userRoles']])
            User.org_units = u"\n".join(
                [replace_path(ou_map, elem) for elem in [ou['path'] for ou in user['organisationUnits']]])
            User.org_units_uid = u"\n".join([ou['path'] for ou in user['organisationUnits']])
            User.dv_org_units = u"\n".join(
                [replace_path(ou_map, elem) for elem in [ou['path'] for ou in user['dataViewOrganisationUnits']]])
            User.dv_org_units_uid = u"\n".join([ou['path'] for ou in user['dataViewOrganisationUnits']])
            User.search_org_units = u"\n".join(
                [replace_path(ou_map, elem) for elem in [ou['path'] for ou in user['teiSearchOrganisationUnits']]])
            User.search_org_units_uid = u"\n".join([ou['path'] for ou in user['teiSearchOrganisationUnits']])
            yield User


def main(args, password):
    setup_logger()

    api = create_api(server=args.server, username=args.username, password=password)

    params1 = {
        'fields':
            'id,name,email,'
            'userCredentials[username,lastLogin,userRoles[id,name],userInfo[phoneNumber,firstName,surname]],'
            'organisationUnits[path],userGroups[id,name],dataViewOrganisationUnits[path],teiSearchOrganisationUnits[path]',
        'paging': False
    }
    users = api.get(endpoint='users', params=params1).json()

    params2 = {
        'fields': 'id,name',
        'paging': False
    }

    ou_map = {
        ou['id']: ou['name']
        for ou in api.get_paged(
            endpoint='organisationUnits',
            params={'fields': 'id,name'},
            page_size=1000,
            merge=True
        ).get('organisationUnits')
    }

    file_name = "userinfo-{}.csv".format(file_timestamp(api.base_url))
    data = []

    if not args.uid_export:
        header_row = ['uid', 'name', 'firstName', 'surname', 'username', 'phoneNumber', 'email', 'lastLogin',
                      'userGroups',
                      'userRoles', 'orgunitPaths', 'dataViewOrgunitPaths', 'teiSearchOrganisationUnits']

        for user in format_user(users, ou_map, uid_export=args.uid_export):
            data.append([
                user.uid,
                user.name,
                user.first_name,
                user.surname,
                user.username,
                user.phone_number,
                user.email,
                user.last_login,
                user.user_groups,
                user.user_roles,
                user.org_units,
                user.dv_org_units,
                user.search_org_units
            ])
    else:
        header_row = ['uid', 'name', 'firstName', 'surname', 'username', 'phoneNumber', 'email', 'lastLogin',
                      'userGroups', 'userGroups_uid',
                      'userRoles', 'userRoles_uid',
                      'orgunitPaths', 'orgunitPaths_uid',
                      'dataViewOrgunitPaths', 'dataViewOrgunitPaths_uid',
                      'teiSearchOrganisationUnits', 'teiSearchOrganisationUnits_uid']

        for user in format_user(users, ou_map, uid_export=args.uid_export):
            data.append([
                user.uid,
                user.name,
                user.first_name,
                user.surname,
                user.username,
                user.phone_number,
                user.email,
                user.last_login,
                user.user_groups,
                user.user_groups_uid,
                user.user_roles,
                user.user_roles_uid,
                user.org_units,
                user.org_units_uid,
                user.dv_org_units,
                user.dv_org_units_uid,
                user.search_org_units,
                user.search_org_units_uid
            ])

    write_csv(data, file_name, header_row)
    logger.info("Success! CSV file exported to {}".format(file_name))
