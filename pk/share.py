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


class DhisAccess(dhis.Dhis):
    """Class for accessing DHIS2"""

    def share_object(self, sharing_object):
        params = {'type': sharing_object.object_type, 'id': sharing_object.uid}
        data = sharing_object.to_json()
        self.post(endpoint="sharing", params=params, payload=data)

    def set_delimiter(self, argument, version=None):
        """
        Operator and rootJunction Alias validation
        :param argument: Argument as received from parser
        :param version: optional dhis2 version as Integer
        :return: tuple(delimiter, rootJunction)
        """
        if not version:
            version = super(DhisAccess, self).dhis_version()
        if '^' in argument:
            if version >= 28:
                raise exceptions.ArgumentException("operator '^' is replaced with '$' in 2.28 onwards. Nothing shared.")
        if '||' in argument:
            if version < 25:
                raise exceptions.ArgumentException("rootJunction 'OR' is only supported 2.25 onwards. Nothing shared.")
            if '&&' in argument:
                raise exceptions.ArgumentException("Not allowed to combine delimiters '&&' and '||'. Nothing shared")
            return '||', 'OR'

        return '&&', 'AND'


class UserGroupHandler(object):
    """Class for handling UserGroups (readonly and readwrite)"""

    def __init__(self, api, usergroup_readwrite, usergroup_readonly):
        self.user_group_accesses = set()
        self.api = api
        self.fill_args(("readwrite", usergroup_readwrite), ("readonly", usergroup_readonly))

    def get_usergroup_uids(self, permission, filter_list, root_junction):
        """
        Get UserGroup UIDs
        :param permission: readwrite or readonly (for printing)
        :param filter_list: List of filters, e.g. ['name:like:ABC', 'code:eq:XYZ']
        :param root_junction: AND or OR
        :return: List of UserGroup UIDs
        """
        params = {
            'fields': 'id,name',
            'paging': False,
            'filter': filter_list
        }

        if root_junction == 'OR':
            params['rootJunction'] = root_junction

        endpoint = 'userGroups'
        logger.info(u"{} {} with filter [{}]".format(permission.upper(), endpoint,
                                                     " {} ".format(root_junction).join(filter_list)))
        response = self.api.get(endpoint=endpoint, file_type='json', params=params)
        if len(response['userGroups']) > 0:
            usergroup_dict = {ug['id']: ug['name'] for ug in response['userGroups']}
            for (key, value) in iteritems(usergroup_dict):
                logger.info(u"- {} {}".format(key, value))
            return usergroup_dict.keys()
        else:
            raise exceptions.UserGroupNotFoundException("No userGroup(s) found. Check your filter / DHIS2")

    def fill_args(self, *args):
        """ Set UserGroupAccesses for readonly and readwrite
        :param args: Tuple of (permission, filter)
        """
        for permission, group in args:
            if group:
                delimiter, root_junction = self.api.set_delimiter(group)
                filter_list = group.split(delimiter)
                usergroups = self.get_usergroup_uids(permission, filter_list, root_junction)
                for ug in usergroups:
                    self.user_group_accesses.add(UserGroupAccess(uid=ug, access=permissions[permission]))


class ObjectHandler(object):
    """Class for handling DHIS2 objects which should be shared"""

    def __init__(self, api, object_type, object_filter, object_public_access):
        self.api = api
        self.obj_name, self.obj_plural = self.get_object_type(object_type)
        self.delimiter, self.root_junction = self.api.set_delimiter(object_filter)
        self.object_filter = object_filter
        self.public_access = object_public_access
        self.container = self.get_objects().get(self.obj_plural)

    def get_object_type(self, argument):
        return self.api.match_shareable(argument)

    def get_objects(self):
        logger.info("PUBLIC ACCESS: {}".format(self.public_access))
        split = self.object_filter.split(self.delimiter)
        params = {
            'fields': 'id,name,code,publicAccess,userGroupAccesses',
            'filter': split,
            'paging': False
        }
        if self.root_junction == 'OR':
            params['rootJunction'] = self.root_junction
        print_msg = u"sharing {} with filter [{}] ..."
        logger.info(print_msg.format(self.obj_plural, " {} ".format(self.root_junction).join(split)))
        response = self.api.get(endpoint=self.obj_plural, file_type='json', params=params)
        if response:
            if len(response[self.obj_plural]) > 0:
                return response
        logger.exception('No objects found. Wrong filter?')


class ObjectSharing(object):

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
    parser = argparse.ArgumentParser(usage='%(prog)s [-h] [-s] -t -f [-w] [-r] -a [-k] [-l] [-v] [-u] [-p] [-d]',
                                     description="PURPOSE: Share DHIS2 objects (dataElements, programs, ...) "
                                                 "with userGroups")
    parser.add_argument('-s', dest='server', action='store', help="DHIS2 server URL, e.g. 'play.dhis2.org/demo'")
    parser.add_argument('-t', dest='object_type', action='store', required=True,
                        help="DHIS2 object type to apply sharing, e.g. -t=sqlViews")
    parser.add_argument('-f', dest='filter', action='store', required=True,
                        help="Filter on objects with DHIS2 field filter (add "
                             "multiple filters with '&&' or '||') e.g. -f='name:like:ABC||code:eq:X'")
    parser.add_argument('-w', dest='usergroup_readwrite', action='store', required=False,
                        help="UserGroup filter for Read-Write access (add "
                             "multiple filters with '&&' or '||') e.g. -w='name:$ilike:aUserGroup7&&id:!eq:aBc123XyZ0u'")
    parser.add_argument('-r', dest='usergroup_readonly', action='store', required=False,
                        help="UserGroup filter for Read-Only access, (add "
                             "multiple filters with '&&' or '||') e.g. -r='id:eq:aBc123XyZ0u'")
    parser.add_argument('-a', dest='public_access', action='store', required=True, choices=permissions.keys(),
                        help="publicAccess (with login), e.g. -a=readwrite")
    parser.add_argument('-k', dest='keep', action='store_true', required=False,
                        help="keep current sharing & only replace if not congruent to prevent change "
                             "to lastUpdated field, e.g. -k")
    parser.add_argument('-l', dest='logging_to_file', action='store', required=False,
                        help="Path to Log file (default level: INFO, pass -d for DEBUG), e.g. l='/var/log/pk.log'")
    parser.add_argument('-v', dest='api_version', action='store', required=False, type=int,
                        help='DHIS2 API version e.g. -v=28')
    parser.add_argument('-u', dest='username', action='store', help='DHIS2 username, e.g. -u=admin')
    parser.add_argument('-p', dest='password', action='store', help='DHIS2 password, e.g. -p=district')
    parser.add_argument('-d', dest='debug', action='store_true', default=False, required=False,
                        help="Debug flag - writes more info to log file, e.g. -d")
    return parser.parse_args()


def skip_or_overwrite(argument_keep, object_type, obj, submitted):
    """
    Determine if object should be skipped or overwritten
    :param argument_keep: False if it should re-shared
    :param object_type: type of DHIS2 object
    :param obj: the existing object on the server to assess
    :param submitted: ObjectSharing object sourced from arguments
    :return: Tuple(Skip object, overwrite object)
    """
    if argument_keep:
        overwrite = False
        existing = None
        try:
            # check if publicAccess property is existing (might be missing)
            pub_access = obj['publicAccess']
        except KeyError:
            overwrite = True
        else:
            # create a ObjectSharing based on what is already on the server
            existing = ObjectSharing(uid=obj['id'], object_type=object_type, pub_access=pub_access)
            if obj.get('userGroupAccesses'):
                try:
                    # check if access property of userGroupAccess is existing (it might be missing)
                    uga = set(UserGroupAccess(uid=x['id'], access=x['access']) for x in obj['userGroupAccesses'])
                except KeyError:
                    overwrite = True
                else:
                    existing.usergroup_accesses = uga
        if existing == submitted:
            return True, False
        if overwrite:
            return False, True
    return False, False


def main():
    args = parse_args()
    log.init(args.logging_to_file, args.debug)
    api = DhisAccess(server=args.server, username=args.username, password=args.password, api_version=args.api_version)

    usergroups = UserGroupHandler(api, args.usergroup_readwrite, args.usergroup_readonly)
    objects = ObjectHandler(api, args.object_type, args.filter, args.public_access)

    no_of_obj = len(objects.container)
    for i, obj in enumerate(objects.container, 1):
        submitted = ObjectSharing(uid=obj['id'],
                                  object_type=objects.obj_name,
                                  pub_access=permissions[args.public_access],
                                  usergroup_accesses=usergroups.user_group_accesses)

        skip_it, overwrite_it = skip_or_overwrite(args.keep, objects.obj_name, obj, submitted)

        status_message = u"{}/{} {} {} {}"
        print_prop = ''
        if skip_it:
            logger.warn(status_message.format(i, no_of_obj, objects.obj_name, obj['id'],
                                              print_prop) + "not re-shared to prevent updating lastUpdated field")
        else:
            # apply sharing
            api.share_object(submitted)
            try:
                print_prop = u"'{}'".format(obj['name'])
            except KeyError:
                try:
                    print_prop = u"'{}'".format(obj['code'])
                except KeyError:
                    print_prop = u''
            if overwrite_it:
                logger.warning(status_message.format(i, no_of_obj, objects.obj_name, obj['id'],
                                                     print_prop) + " overwritten because userGroupAccess.publicAccess "
                                                                   "or userGroupAccess.UID "
                                                                   "or object.publicAccess was missing")
            else:
                logger.info(status_message.format(i, no_of_obj, objects.obj_name, obj['id'], print_prop))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warn("Aborted.")
