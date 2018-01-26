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

access = {
    'none': '--------',
    'readonly': 'r-------',
    'readwrite': 'rw------'
}


class Permission(object):
    """ Class for handling Access strings such as rw------ and readwrite"""

    def __init__(self, term):
        try:
            self.permission = access[term]
        except KeyError:
            if term in access.values():
                self.permission = term
            else:
                raise exceptions.ClientException("Value not in {}".format(json.dumps(access)))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.permission == other.permission

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.permission)

    def __repr__(self):
        return self.permission


class DhisAccess(dhis.Dhis):
    """Class for accessing DHIS2: validating metadata field filters and actual sharing of objects"""

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


class UserGroupAccess(object):
    """ Class for handling a UserGroupAccess object linked to a DHIS2 object containing a UserGroup UID and access"""

    def __init__(self, uid, access):
        self.uid = uid
        self.access = Permission(access)

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
        return {"id": self.uid, "access": self.access.__repr__()}


class UserGroupHandler(object):
    """Class for handling existing UserGroups (readonly and readwrite)"""

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
        response = self.api.get(endpoint, params=params)
        if len(response['userGroups']) > 0:
            usergroup_dict = {ug['id']: ug['name'] for ug in response['userGroups']}
            for (key, value) in iteritems(usergroup_dict):
                logger.info(u"- {} {}".format(key, value))
            return usergroup_dict.keys()
        else:
            logger.debug(endpoint, params)
            raise exceptions.UserGroupNotFoundException("No userGroup(s) found. Check filter, rootJunction or DHIS2")

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
                    self.user_group_accesses.add(UserGroupAccess(uid=ug, access=permission))


class ObjectHandler(object):
    """Class for handling multiple DHIS2 objects from a single object type (e.g. dataElements)"""

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
        response = self.api.get(self.obj_plural, params=params)
        if response:
            if len(response[self.obj_plural]) > 0:
                return response
            else:
                raise exceptions.ClientException('No objects found. Check filter, rootJunction or DHIS2')


class ObjectSharing(object):
    """ Class for identifying a single Objects's sharing configuration"""

    def __init__(self, uid, object_type, pub_access, usergroup_accesses=set()):
        self.uid = uid
        self.object_type = object_type
        self.public_access = Permission(pub_access)
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
                'publicAccess': self.public_access.__repr__(),
                'externalAccess': self.external_access,
                'user': self.user,
                'userGroupAccesses': [x.to_json() for x in self.usergroup_accesses]
            }
        }


def skip(overwrite, object_type, obj, new):
    """
    Determine if object should be skipped or overwritten
    :param overwrite: if it should be overwritten regardless of existing objects
    :param object_type: type of DHIS2 object
    :param obj: the existing object on the server to assess
    :param new: ObjectSharing object sourced from arguments
    :return: Tuple(Skip object, overwrite object)
    """
    existing = None
    try:
        # check if publicAccess property is existing (might be missing)
        pub_access = obj['publicAccess']
    except KeyError:
        logger.warning("Fix: Added 'publicAccess' for {} {} to value [{}]"
                       .format(object_type, obj['id'], new.public_access))
        overwrite = True
    else:
        # create a ObjectSharing based on what is already on the server
        existing = ObjectSharing(uid=obj['id'], object_type=object_type, pub_access=pub_access)
        if obj.get('userGroupAccesses'):
            try:
                # check if access property of userGroupAccess is existing (it might be missing)
                uga = set(UserGroupAccess(uid=x['id'], access=x['access']) for x in obj['userGroupAccesses'])
            except KeyError:
                logger.warning("Fix: Added 'UserGroupAccess.access' corrected for {} {} to value [{}]"
                               .format(object_type, obj['id'],
                                       ', '.join([x.to_json() for x in new.usergroup_accesses])))
                overwrite = True
            else:
                existing.usergroup_accesses = uga
    if overwrite:
        return False
    return existing == new


def parse_args():
    parser = argparse.ArgumentParser(usage='%(prog)s [-h] [-s] -t -f [-w] [-r] -a [-o] [-l] [-v] [-u] [-p] [-d]',
                                     description="PURPOSE: Share DHIS2 objects (dataElements, programs, ...) "
                                                 "with userGroups")
    parser.add_argument('-s',
                        dest='server',
                        action='store',
                        help="DHIS2 server URL, e.g. 'play.dhis2.org/demo'"
                        )
    parser.add_argument('-t',
                        dest='object_type',
                        action='store',
                        required=True,
                        help="DHIS2 object type to apply sharing, e.g. -t=sqlViews")
    parser.add_argument('-f',
                        dest='filter',
                        action='store',
                        required=True,
                        help="Filter on objects with DHIS2 field filter (add multiple filters with '&&' or '||') "
                             "e.g. -f='name:like:ABC||code:eq:X'")
    parser.add_argument('-w',
                        dest='usergroup_readwrite',
                        action='store',
                        required=False,
                        help="UserGroup filter for Read-Write access (add multiple filters with '&&' or '||') "
                             "e.g. -w='name:$ilike:aUserGroup7&&id:!eq:aBc123XyZ0u'")
    parser.add_argument('-r',
                        dest='usergroup_readonly',
                        action='store',
                        required=False,
                        help="UserGroup filter for Read-Only access, (add "
                             "multiple filters with '&&' or '||') e.g. -r='id:eq:aBc123XyZ0u'")
    parser.add_argument('-a',
                        dest='public_access',
                        action='store',
                        required=True,
                        choices=access.keys(),
                        help="publicAccess (with login), e.g. -a=readwrite")
    parser.add_argument('-o',
                        dest='overwrite',
                        action='store_true',
                        required=False,
                        default=False,
                        help="Overwrite sharing - updates 'lastUpdated' field of all shared objects")
    parser.add_argument('-l',
                        dest='logging_to_file',
                        action='store',
                        required=False,
                        help="Path to Log file (default level: INFO, pass -d for DEBUG), e.g. l='/var/log/pk.log'")
    parser.add_argument('-v',
                        dest='api_version',
                        action='store',
                        required=False, type=int,
                        help='DHIS2 API version e.g. -v=28')
    parser.add_argument('-u',
                        dest='username',
                        action='store',
                        help='DHIS2 username, e.g. -u=admin')
    parser.add_argument('-p',
                        dest='password',
                        action='store',
                        help='DHIS2 password, e.g. -p=district')
    parser.add_argument('-d',
                        dest='debug',
                        action='store_true',
                        default=False,
                        required=False,
                        help="Debug flag")
    return parser.parse_args()


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
                                  pub_access=args.public_access,
                                  usergroup_accesses=usergroups.user_group_accesses)

        # check if it should be skipped. Also checks for missing fields required for sharing (publicAccess, ...)
        skip_it = skip(args.overwrite, objects.obj_name, obj, submitted)
        status_message = u"{}/{} {} {} {}"
        try:
            print_prop = u"'{}'".format(obj['name'])
        except KeyError:
            try:
                print_prop = u"'{}'".format(obj['code'])
            except KeyError:
                print_prop = u''
        if not skip_it:
            api.share_object(submitted)
            logger.info(status_message.format(i, no_of_obj, objects.obj_name, obj['id'], print_prop))
        else:
            logger.warning("skipped: " + status_message.format(i, no_of_obj, objects.obj_name, obj['id'], print_prop))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warn("Aborted.")
