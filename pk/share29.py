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
try:
    from pk.core import log
    from pk.core import dhis
    from pk.core import exceptions
except ImportError:
    from core import log
    from core import dhis
    from core import exceptions

access = {
    u'rwrw----',
    u'rwr-----',
    u'rw------',
    u'r-rw----',
    u'r-r-----',
    u'r-------',
    u'--rw----',
    u'--r-----',
    u'--------'
}

access_short = {
    'none': u'--',
    'readonly': u'r-',
    'readwrite': u'rw'
}


def permission_converter(value, data=None):
    if isinstance(value, list):
        metadata_str = access_short.get(value[0], '--')
        data_str = access_short.get(value[1], '--')
        return u'{}{}----'.format(metadata_str, data_str)
    elif value in access:
        return value
    else:
        metadata_str = access_short.get(value, '--')
        data_str = access_short.get(data, '--')
        return u'{}{}----'.format(metadata_str, data_str)


class DhisWrapper(dhis.Dhis):
    """Class for accessing DHIS2: validating metadata field filters and actual sharing of objects"""

    def share_object(self, sharing_object):
        params = {'type': sharing_object.obj_type, 'id': sharing_object.uid}
        self.post('sharing', params=params, payload=sharing_object.to_json())

    def set_delimiter(self, argument, version=None):
        """
        Operator and rootJunction Alias validation
        :param argument: Argument as received from parser
        :param version: optional dhis2 version as Integer
        :return: tuple(delimiter, rootJunction)
        """
        if not version:
            version = self.dhis_version
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


class ShareableObjectCollection(object):

    def __init__(self, api, obj_type, filters):
        self.api = api
        self.name, self.plural = self.get_name(obj_type)
        self.filters = filters
        self.delimiter, self.root_junction = self.api.set_delimiter(filters)
        self.share_data = self.is_data_shareable()

        from_server = self.get_objects().get(self.plural)
        self.elements = set(self.create_obj(from_server))

    def add(self, other):
        self.elements.add(other)

    def schema(self, schema_property):

        params = {
            'fields': 'name,plural,shareable,dataShareable'
        }
        r = self.api.get(endpoint='schemas', params=params)
        return {x['name']: x['plural'] for x in r['schemas'] if x[schema_property]}

    def get_name(self, obj_type):
        shareable = self.schema('shareable')
        for name, plural in iteritems(shareable):
            if obj_type in (name, plural):
                return name, plural

    def is_data_shareable(self):
        data_shareable = self.schema('dataShareable')
        for name, plural in iteritems(data_shareable):
            if self.name in (name, plural):
                return True
        raise ValueError("{} cannot share data, only metadata")

    def get_objects(self):
        split = self.filters.split(self.delimiter)
        params = {
            'fields': 'id,name,code,publicAccess,userGroupAccesses',
            'filter': split,
            'paging': False
        }
        if self.root_junction == 'OR':
            params['rootJunction'] = self.root_junction
        print_msg = u"Sharing {} with filter [{}] ..."
        logger.info(print_msg.format(self.plural, " {} ".format(self.root_junction).join(split)))
        response = self.api.get(self.plural, params=params)
        if response:
            if len(response[self.plural]) > 0:
                return response
            else:
                logger.warning(u'No {} found.'.format(self.plural))
                import sys
                sys.exit(0)

    def create_obj(self, response):
        for elem in response:
            yield ShareableObject(obj_type=self.name,
                                  uid=elem['id'],
                                  name=elem['name'],
                                  code=elem.get('code'),
                                  public_access=elem['publicAccess'],
                                  usergroup_accesses=elem.get('userGroupAccesses'))

    def __str__(self):
        s = ''
        for obj in self.elements:
            s += str(obj)
        return s


class ShareableObject(object):

    def __init__(self, obj_type, uid, name, public_access, usergroup_accesses=set(), code=None):
        self.obj_type = obj_type
        self.uid = uid
        self.name = name
        self.public_access = permission_converter(public_access)
        if isinstance(usergroup_accesses, list):
            self.usergroup_accesses = {UserGroupAccess(x['id'], x['access']) for x in usergroup_accesses}
        else:
            self.usergroup_accesses = usergroup_accesses
        self.code = code

        self.external_access = False
        self.user = {}

    @classmethod
    def from_dict(cls, object_type, dict_data):
        return cls(dict_data['id'], object_type, dict_data['publicAccess'], dict_data['userGroupAccesses'])

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.obj_type == other.obj_type and
                self.uid == other.uid and
                self.name == other.name and
                self.public_access == other.public_access and
                self.usergroup_accesses == other.usergroup_accesses and
                self.code == other.code)

    def __ne__(self, other):
        return not self == other

    """
    def __hash__(self):
        return hash((self.uid, self.obj_type, self.public_access, tuple(self.usergroup_accesses)))
    """
    def __str__(self):
        s = '\n{} {} ({}) PA: {} UGA: {}\n'.format(
            self.obj_type,
            self.name,
            self.uid,
            self.public_access,
            self.usergroup_accesses)
        return s

    def __repr__(self):
        s = u"<ShareableObject id='{}', publicAccess='{}', userGroupAccess='{}'>".format(self.uid, self.public_access, ','.join([json.dumps(x.to_json()) for x in self.usergroup_accesses]))
        return s

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
    """ Class for handling a UserGroupAccess object linked to a DHIS2 object containing a UserGroup UID and access"""

    def __init__(self, uid, permission):
        self.uid = u'{}'.format(uid)
        self.access = permission

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


class UserGroupsHandler(object):
    """Class for handling existing UserGroups (readonly and readwrite)"""

    def __init__(self, api, groups):
        self.api = api
        self.accesses = set()
        for group_filter, metadata_permission, data_permission in groups:
            delimiter, root_junction = self.api.set_delimiter(group_filter)
            filter_list = group_filter.split(delimiter)
            usergroups = self.get_usergroup_uids(filter_list, root_junction)
            for uid in usergroups:
                permission = permission_converter(metadata_permission, data_permission)
                self.accesses.add(UserGroupAccess(uid, permission))

    def get_usergroup_uids(self, filter_list, root_junction='AND'):
        """
        Get UserGroup UIDs
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
        response = self.api.get(endpoint, params=params)
        if len(response['userGroups']) > 0:
            usergroup_dict = {ug['id']: ug['name'] for ug in response['userGroups']}
            for (key, value) in iteritems(usergroup_dict):
                logger.info(u"- {} {}".format(key, value))
            return usergroup_dict.keys()
        else:
            logger.debug(endpoint, params)
            raise exceptions.UserGroupNotFoundException("No userGroup found with {}".format(filter_list))


class ObjectsHandler(object):
    """Class for handling a collection of DHIS2 objects from a single object type (e.g. dataElements)"""

    def __init__(self, api, obj_type, obj_filter):
        self.api = api
        self.singular, self.plural = self.get_object_type(obj_type)
        self.delimiter, self.root_junction = self.api.set_delimiter(obj_filter)
        self.obj_filter = obj_filter
        self.elements = self.get_objects().get(self.plural)

    def get_object_type(self, argument):
        """
        Find a shareable DHIS2 class
        :param argument:
        :return:
        """
        return self.api.match_shareable(argument)

    def get_objects(self):
        split = self.obj_filter.split(self.delimiter)
        params = {
            'fields': 'id,name,code,publicAccess,userGroupAccesses',
            'filter': split,
            'paging': False
        }
        if self.root_junction == 'OR':
            params['rootJunction'] = self.root_junction
        print_msg = u"Sharing {} with filter [{}] ..."
        logger.info(print_msg.format(self.plural, " {} ".format(self.root_junction).join(split)))
        response = self.api.get(self.plural, params=params)
        if response:
            if len(response[self.plural]) > 0:
                return response
            else:
                logger.warning(u'No {} found.'.format(self.plural))
                import sys
                sys.exit(0)


class ObjectSharing(object):
    """ Class for identifying a single Objects's sharing configuration"""

    def __init__(self, uid, object_type, pub_access, usergroup_accesses=set()):
        self.uid = uid
        self.object_type = object_type
        if isinstance(pub_access, Permission):
            self.public_access = pub_access

        else:
            self.public_access = Permission(metadata=pub_access[0], data=pub_access[1])

        if isinstance(usergroup_accesses, list):
            self.usergroup_accesses = {UserGroupAccess(x['id'], x['access']) for x in usergroup_accesses}
        else:
            self.usergroup_accesses = usergroup_accesses

        self.external_access = False
        self.user = {}

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.uid == other.uid and
                self.object_type == other.object_type and
                self.public_access == other.public_access and
                self.usergroup_accesses == other.usergroup_accesses)

    @classmethod
    def from_server(cls, object_type, d):
        return cls(d['id'], object_type, d['publicAccess'], d['userGroupAccesses'])

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


def skip(overwrite, on_server, update):
    """
    Determine if object should be skipped or overwritten by comparing the state on the server
    with the state as submitted
    :param overwrite: if it should be overwritten regardless of congruent state
    :param on_server: the existing object on the server to assess
    :param update: ObjectSharing object sourced from arguments
    :return: True if skip, False if overwrite
    """
    if not isinstance(on_server, ShareableObject or not isinstance(update, ShareableObject)):
        logger.error("Can't compare elem {} with new {}")

    # check if publicAccess property is existing (might be missing)
    pub_access = on_server.public_access
    if pub_access is None:
        logger.warning(u"Fix: Added 'publicAccess' for {} {} to value [{}]"
                       .format(update.obj_type, on_server.uid, update.public_access))
        overwrite = True
    elif overwrite:
        return False
    return on_server == update


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
    parser.add_argument('-g',
                        dest='groups',
                        action='append',
                        required=False,
                        nargs='+',
                        help="DHIS2 2.29 syntax: -g <filter> <metadata> <data> - can be repeated any number of times")
    parser.add_argument('-a',
                        dest='public_access',
                        action='append',
                        required=True,
                        nargs='+',
                        choices=access_short.keys(),
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
                        required=False,
                        type=int,
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

    args = parser.parse_args()
    if len(args.public_access) not in (1, 2):
        raise argparse.ArgumentError("Must use -a <metadata> <data>")
    return parser.parse_args()


def identifier(obj):
    try:
        x = u"'{}'".format(obj.name)
    except KeyError:
        try:
            x = u"'{}'".format(obj.code)
        except KeyError:
            x = u''
    return x


def main():
    args = parse_args()
    log.init(args.logging_to_file, args.debug)
    api = DhisWrapper(args.server, args.username, args.password, args.api_version)

    usergroups = UserGroupsHandler(api, args.groups)
    logger.info("Creating Collection from server...")
    coll = ShareableObjectCollection(api, args.object_type, args.filter)
    for i, srv_obj in enumerate(coll.elements, 1):
        logger.info("Creating Object via User Groups...")
        update = ShareableObject(obj_type=srv_obj.obj_type,
                                 uid=srv_obj.uid,
                                 name=srv_obj.name,
                                 code=srv_obj.code,
                                 public_access=args.public_access[0],
                                 usergroup_accesses=usergroups.accesses)

        pointer = u"{0}/{1} {2} {3}".format(i, len(coll.elements), coll.name, srv_obj.uid)

        if not skip(args.overwrite, srv_obj, update):
            logger.info(u"{0} {1}".format(pointer, identifier(srv_obj)))
            api.share_object(update)

        else:
            logger.warning(u"skipped: {0} {1}".format(pointer, identifier(srv_obj)))



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warn("Aborted.")