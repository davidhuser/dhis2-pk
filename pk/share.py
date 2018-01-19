#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

"""
share-objects
~~~~~~~~~~~~~~~~~
Assigns sharing to shareable DHIS2 objects like userGroups and publicAccess by calling the /api/sharing endpoint.
"""

import argparse
import json
import sys

from six import iteritems
from logzero import logger
import core.log as log
import core.dhis as dhis
import core.exceptions as exceptions

permissions = {
    'none': '--------',
    'readonly': 'r-------',
    'readwrite': 'rw------'
}


class DhisAccessShare(dhis.DhisAccess):

    def get_usergroup_uids(self, filter_list, access, delimiter):
        params = {
            'fields': 'id,name',
            'paging': False,
            'filter': filter_list
        }
        if delimiter == '||':
            root_junction = 'OR'
            params['rootJunction'] = root_junction
        else:
            root_junction = 'AND'

        endpoint = 'userGroups'
        logger.info(u"GET {} with filter [{}] ({})"
                    .format(endpoint, ' {} '.format(root_junction).join(filter_list), access))
        response = self.get(endpoint=endpoint, file_type='json', params=params)

        if len(response['userGroups']) > 0:
            # zip it into a dict { id: name, id:name }
            ugmap = {ug['id']: ug['name'] for ug in response['userGroups']}
            for (key, value) in iteritems(ugmap):
                logger.info(u"{} userGroup {} - {}".format(access, key, value))
            return ugmap.keys()
        else:
            raise exceptions.ClientException("No userGroup(s) found. Check your filter / DHIS2")

    def get_objects(self, objects, objects_filter, delimiter):

        params = {
            'fields': 'id,name,code,publicAccess,userGroupAccesses',
            'filter': objects_filter,
            'paging': False
        }

        if delimiter == '||':
            params['rootJunction'] = 'OR'
            print_junction = u"GET {} with filters [rootJunction: OR] {}"
        elif len(objects_filter) > 1:
            print_junction = u"GET {} with filters [rootJunction: AND] {}"
        else:
            print_junction = u"GET {} with filter {}"

        logger.info(print_junction.format(objects, objects_filter))
        response = self.get(endpoint=objects, file_type='json', params=params)

        if response:
            if len(response[objects]) > 0:
                return response
        logger.warning('No objects found. Wrong filter?')
        logger.debug(u'objects: {}'.format(objects))
        sys.exit()

    def share_object(self, sharing_object):
        params = {'type': sharing_object.object_type, 'id': sharing_object.uid}
        data = sharing_object.to_json()
        self.post(endpoint="sharing", params=params, payload=data)

    def get_object_type(self, argument):
        return super(DhisAccessShare, self).get_shareable_object_type(argument)


class SharingDefinition(object):

    def __init__(self, uid, object_type, pub_access, usergroup_accesses=set()):
        self.uid = uid
        self.object_type = object_type
        self.public_access = pub_access
        self.usergroup_accesses = usergroup_accesses
        self.external_access = False
        self.user = {}

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.uid == other.uid and
                self.object_type == other.object_type and
                self.public_access == other.public_access and
                self.usergroup_accesses == other.usergroup_accesses)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.uid, self.object_type, self.public_access, tuple(self.usergroup_accesses)))

    def __str__(self):
        return u"{} {} {} {}".format(self.object_type, self.uid, self.public_access,
                                     ' / '.join([json.dumps(x.to_json()) for x in self.usergroup_accesses]))

    def to_json(self):
        return {
            'object': {
                'publicAccess': self.public_access,
                'externalAccess': self.external_access,
                'user': self.user,
                'userGroupAccesses': [x.to_json() for x in self.usergroup_accesses]
            }
        }


class UserGroupAccess(object):

    def __init__(self, uid, access):
        self.uid = uid
        self.access = access

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.uid == other.uid and
                self.access == other.access)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.uid, self.access))

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        return {"id": self.uid, "access": self.access}


def parse_args():
    parser = argparse.ArgumentParser(usage='%(prog)s [-h] [-s] -t -f [-w] [-r] -a [-k] [-v] [-u] [-p] [-d]',
                                     description="PURPOSE: Share DHIS2 objects (dataElements, programs, ...) "
                                                 "with userGroups")
    parser.add_argument('-s', dest='server', action='store', help="DHIS2 server URL, e.g. 'play.dhis2.org/demo'")
    parser.add_argument('-t', dest='object_type', action='store', required=True,
                        help="DHIS2 object type to apply sharing, e.g. -t=sqlViews")
    parser.add_argument('-f', dest='filter', action='store', required=True,
                        help="Filter on objects with DHIS2 field filter (add "
                             "multiple filters with '&&') e.g. -f='name:like:ABC'")
    parser.add_argument('-w', dest='usergroup_readwrite', action='store', required=False,
                        help="UserGroup filter for Read-Write access (add "
                             "multiple filters with '&&') e.g. -w='name:$ilike:aUserGroup7&&id:!eq:aBc123XyZ0u'")
    parser.add_argument('-r', dest='usergroup_readonly', action='store', required=False,
                        help="UserGroup filter for Read-Only access, (add "
                             "multiple filters with '&&') e.g. -r='id:eq:aBc123XyZ0u'")
    parser.add_argument('-a', dest='publicaccess', action='store', required=True, choices=permissions.keys(),
                        help="publicAccess (with login), e.g. -a=readwrite")
    parser.add_argument('-k', dest='keep', action='store_true', required=False,
                        help="keep current sharing & only replace if not congruent to prevent change "
                             "to lastUpdated field")
    parser.add_argument('-l', dest='logging_to_file', action='store', required=False,
                        help="Path to Log file (level: INFO)")
    parser.add_argument('-v', dest='api_version', action='store', required=False, type=int,
                        help='DHIS2 API version e.g. -v=24')
    parser.add_argument('-u', dest='username', action='store', help='DHIS2 username, e.g. -u=admin')
    parser.add_argument('-p', dest='password', action='store', help='DHIS2 password, e.g. -p=district')
    parser.add_argument('-d', dest='debug', action='store_true', default=False, required=False,
                        help="Debug flag - writes more info to log file, e.g. -d")
    return parser.parse_args()


def validate_filter(argument, dhis_version):
    if '^' in argument:
        if dhis_version >= 28:
            raise exceptions.ClientException("operator '^' is replaced with '$' in 2.28 onwards. Nothing shared.")
    if '||' in argument:
        if dhis_version < 25:
            raise exceptions.ClientException("rootJunction 'OR' is only supported 2.25 onwards. Nothing shared.")
        if '&&' in argument:
            raise exceptions.ClientException("Filter can't have both '&&' and '||'. Nothing shared")
        return '||'
    else:
        return '&&'


def main():
    args = parse_args()
    log.init(args.logging_to_file, args.debug)
    api = DhisAccessShare(server=args.server, username=args.username, password=args.password,
                          api_version=args.api_version)

    dhis_version = api.get_dhis_version()

    # get the real valid object type name
    object_type = api.get_object_type(args.object_type)

    user_group_accesses = set()
    if args.usergroup_readwrite:
        delimiter = validate_filter(args.usergroup_readwrite, dhis_version)
        # split filter of arguments into list
        rw_ug_filter_list = args.usergroup_readwrite.split(delimiter)
        # get UIDs of usergroups with RW access
        readwrite_usergroup_uids = api.get_usergroup_uids(rw_ug_filter_list, 'readwrite', delimiter)
        for ug in readwrite_usergroup_uids:
            user_group_accesses.add(UserGroupAccess(uid=ug, access=permissions['readwrite']))

    if args.usergroup_readonly:
        delimiter = validate_filter(args.usergroup_readonly, dhis_version)
        ro_ug_filter_list = args.usergroup_readonly.split(delimiter)
        # get UID(s) of usergroups with RO access
        readonly_usergroup_uids = api.get_usergroup_uids(ro_ug_filter_list, 'readonly', delimiter)
        for ug in readonly_usergroup_uids:
            user_group_accesses.add(UserGroupAccess(uid=ug, access=permissions['readonly']))

    # split arguments for multiple filters for to-be-shared objects
    delimiter = validate_filter(args.filter, dhis_version)
    object_filter_list = args.filter.split(delimiter)

    # pull objects for which to apply sharing
    data = api.get_objects(object_type, object_filter_list, delimiter)

    no_of_obj = len(data[object_type])
    for i, obj in enumerate(data[object_type], 1):
        uid = obj['id']
        skip = False
        # strip name to match API (e.g. dataElements -> dataElement)
        if object_type == 'categories':
            ot_single = 'category'
        else:
            ot_single = object_type[:-1]

        # create a SharingDefinition based on command-line arguments
        submitted = SharingDefinition(uid=uid,
                                      object_type=ot_single,
                                      pub_access=permissions[args.publicaccess],
                                      usergroup_accesses=user_group_accesses)
        if args.keep:
            # create a SharingDefinition based on what is already on the server
            existing = SharingDefinition(uid=uid,
                                         object_type=ot_single,
                                         pub_access=obj['publicAccess'])
            overwrite = False
            if obj.get('userGroupAccesses'):
                try:
                    # check if access property of userGroupAccess is existing (it might be missing)
                    uga = set(UserGroupAccess(uid=x['id'], access=x['access']) for x in obj['userGroupAccesses'])
                except KeyError:
                    overwrite = True
                else:
                    existing.usergroup_accesses = uga

            if not overwrite and existing == submitted:
                skip = True

        status_message = u"({}/{}) {} {} {}"
        print_prop = ''
        if not skip:
            # apply sharing
            api.share_object(submitted)
            try:
                print_prop = "'{}'".format(obj['name'])
            except KeyError:
                try:
                    print_prop = "'{}'".format(obj['code'])
                except KeyError:
                    print_prop = ''
            finally:
                if overwrite:
                    logger.warning(status_message.format(i, no_of_obj, ot_single, uid, print_prop) +
                                   " was overwritten because userGroupAccess.publicAccess or "
                                   "userGroupAccess.UID was missing")
                else:
                    logger.info(status_message.format(i, no_of_obj, ot_single, uid, print_prop))

        else:
            logger.warn(status_message.format(i, no_of_obj, ot_single, uid, print_prop) +
                        " not re-shared to prevent updating lastUpdated field")


if __name__ == "__main__":
    main()
