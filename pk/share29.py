#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

"""
share-objects
~~~~~~~~~~~~~~~~~
Assigns sharing to shareable DHIS2 objects like userGroups and publicAccess by calling the /api/sharing endpoint.
"""

import argparse
import textwrap
import json
import sys

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
    'none': u'--',
    'readonly': u'r-',
    'readwrite': u'rw'
}


def set_delimiter(argument):
    """
    Operator and rootJunction Alias validation
    :param argument: Argument as received from parser
    :return: tuple(delimiter, rootJunction)
    """
    if '^' in argument:
        raise exceptions.ArgumentException("operator '^' is replaced with '$' in 2.28 onwards. Nothing shared.")
    if '||' in argument:
        if '&&' in argument:
            raise exceptions.ArgumentException("Not allowed to combine delimiters '&&' and '||'. Nothing shared")
        return '||', 'OR'

    return '&&', 'AND'


class Permission(object):

    symbolic_notation = {
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

    def __init__(self, metadata, data):
        self.metadata = metadata
        self.data = data

    @classmethod
    def from_public_args(cls, args):
        metadata = args[0][0]
        try:
            data = args[0][1]
        except IndexError:
            data = None
        return cls(metadata, data)

    @classmethod
    def from_symbol(cls, symbol):
        if symbol not in Permission.symbolic_notation:
            raise ValueError("Permission symbol {} not valid!".format(symbol))
        metadata_str = symbol[:2]
        if metadata_str == 'rw':
            metadata = 'readwrite'
        elif metadata_str == 'r-':
            metadata = 'readonly'
        else:
            metadata = None

        data_str = symbol[2:-4]
        if data_str == 'rw':
            data = 'readwrite'
        elif data_str == 'r-':
            data = 'readonly'
        else:
            data = None

        return cls(metadata, data)

    @classmethod
    def from_group_args(cls, args):
        metadata = args[1]
        try:
            data = args[2]
        except IndexError:
            data = None
        return cls(metadata, data)

    def to_symbol(self):
        m = access.get(self.metadata, '--')
        d = access.get(self.data, '--')
        return '{}{}----'.format(m, d)

    def __str__(self):
        return 'METADATA: {}, DATA: {}'.format(self.metadata, self.data)


class ShareableObjectCollection(object):

    def __init__(self, api, obj_type, filters):
        self.api = api
        self.name, self.plural = self.get_name(obj_type)
        self.filters = filters
        self.delimiter, self.root_junction = set_delimiter(filters)
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
            if obj_type.lower() in (name.lower(), plural.lower()):
                return name, plural
        logger.error("Could not find {}".format(obj_type))
        sys.exit(1)

    def is_data_shareable(self):
        data_shareable = self.schema('dataShareable')
        for name, plural in iteritems(data_shareable):
            if self.name in (name, plural):
                return True
        return False

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
                                  public_access=Permission.from_symbol(elem['publicAccess']),
                                  usergroup_accesses={UserGroupAccess.from_dict(d) for d in elem['userGroupAccesses']})

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
        self.public_access = public_access
        self.usergroup_accesses = usergroup_accesses
        self.code = code
        self.external_access = False
        self.user = {}

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
        s = "<ShareableObject id='{}', publicAccess='{}', userGroupAccess='{}'>".format(self.uid,
                                                                                        self.public_access.to_symbol(),
                                                                                        ','.join(
                                                                                            [json.dumps(x.to_json())
                                                                                             for x in
                                                                                             self.usergroup_accesses]))
        return s

    def to_json(self):
        return {
            'object': {
                'publicAccess': self.public_access.to_symbol(),
                'externalAccess': self.external_access,
                'user': self.user,
                'userGroupAccesses': [x.to_json() for x in self.usergroup_accesses]
            }
        }


class UserGroupAccess(object):
    """ Class for handling a UserGroupAccess object linked to a DHIS2 object containing a UserGroup UID and access"""

    def __init__(self, uid, permission):
        self.uid = u'{}'.format(uid)
        self.permission = permission

    @classmethod
    def from_dict(cls, data):
        return cls(data['id'], Permission.from_symbol(data['access']))

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.uid == other.uid and
                self.permission == other.permission)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.uid, self.permission))

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        return {"id": self.uid, "access": self.permission.to_symbol()}


class UserGroupsHandler(object):
    """Class for handling existing UserGroups (readonly and readwrite)"""

    def __init__(self, api, groups):
        self.api = api
        self.accesses = set()
        if not groups:
            logger.info("No User Groups specified, only setting Public Access.")
        else:
            for group in groups:
                group_filter = group[0]
                permission = Permission.from_group_args(group)

                delimiter, root_junction = set_delimiter(group_filter)
                filter_list = group_filter.split(delimiter)
                usergroups = self.get_usergroup_uids(filter_list, root_junction)
                logger.info(u"UserGroups with filter [{}]".format(" {} ".format(root_junction).join(filter_list)))

                for uid, name in iteritems(usergroups):
                    logger.info(u"- {} {} - {}".format(uid, name, permission))
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
            return {ug['id']: ug['name'] for ug in response['userGroups']}
        else:
            logger.debug(endpoint, params)
            raise exceptions.UserGroupNotFoundException("No userGroup found with {}".format(filter_list))


def skip(overwrite, on_server, update):
    """
    Determine if object should be skipped or overwritten by comparing the state on the server
    with the state as submitted
    :param overwrite: if it should be overwritten regardless of congruent state
    :param on_server: the existing object on the server to assess
    :param update: ObjectSharing object sourced from arguments
    :return: True if skip, False if overwrite
    """
    if overwrite:
        return False
    else:
        return on_server == update


def parse_args():
    parser = argparse.ArgumentParser(usage='%(prog)s [-h] [-s] -t -f [-g] -a [-o] [-l] [-v] [-u] [-p] [-d]',
                                     description="Share DHIS2 objects with userGroups FOR 2.29 SERVERS or newer",
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    required.add_argument('-s',
                          dest='server',
                          action='store',
                          metavar='URL',
                          help="DHIS2 server URL, e.g. 'play.dhis2.org/demo'"
                          )
    required.add_argument('-t',
                          dest='object_type',
                          action='store',
                          required=True,
                          help="DHIS2 object type to apply sharing, e.g. sqlView")
    required.add_argument('-f',
                          dest='filter',
                          action='store',
                          required=True,
                          help=textwrap.dedent('''\
                            Filter on objects with DHIS2 field filter.
                            Add multiple filters with '&&' or '||'.
                            Example: -f 'name:like:ABC||code:eq:X'
                               '''))
    required.add_argument('-a',
                          dest='public_access',
                          action='append',
                          required=True,
                          nargs='+',
                          metavar='PUBLIC',
                          choices=access.keys(),
                          help=textwrap.dedent('''\
                          publicAccess (with login). 
                          Valid choices are: {}
                          '''.format(', '.join(access.keys()))))

    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('-g',
                          dest='groups',
                          action='append',
                          required=False,
                          metavar='USERGROUP',
                          nargs='+',
                          help=textwrap.dedent('''\
                            Usergroup setting: FILTER METADATA [DATA] - can be repeated any number of times."
                            FILTER: Filter all User Groups. See -f for filtering mechanism
                            METADATA: Metadata access for this User Group. See -a for allowed choices
                            DATA: Data access for this User Group. optional (only for objects that support data sharing). see -a for allowed choices.
                            Example: -g 'id:eq:OeFJOqprom6' readwrite none 
                            '''))
    optional.add_argument('-o',
                          dest='overwrite',
                          action='store_true',
                          required=False,
                          default=False,
                          help="Overwrite sharing - updates 'lastUpdated' field of all shared objects")
    optional.add_argument('-l',
                          dest='logging_to_file',
                          action='store',
                          required=False,
                          help="Path to Log file (default level: INFO, pass -d for DEBUG), e.g. l='/var/log/pk.log'")
    optional.add_argument('-v',
                          dest='api_version',
                          action='store',
                          required=False,
                          type=int,
                          help='DHIS2 API version e.g. -v=28')
    optional.add_argument('-u',
                          dest='username',
                          action='store',
                          help='DHIS2 username, e.g. -u=admin')
    optional.add_argument('-p',
                          dest='password',
                          action='store',
                          help='DHIS2 password, e.g. -p=district')
    optional.add_argument('-d',
                          dest='debug',
                          action='store_true',
                          default=False,
                          required=False,
                          help="Debug flag")

    args = parser.parse_args()
    if len(args.public_access) not in (1, 2):
        logger.error("Must use -a METADATA_SHARING [DATA_SHARING] - max 2 arguments")
        parser.print_help()
        sys.exit(1)
    if args.groups:
        for group in args.groups:
            if group[1] not in access.keys():
                logger.error("Set permission for METADATA access - one of {}, e.g. -g 'id:eq:UID' none readonly".format(
                    access.keys()))
                parser.print_help()
                sys.exit(1)
            try:
                data_permission = group[2]
            except IndexError:
                pass
            else:
                if data_permission not in access.keys():
                    logger.error("Set permission for DATA access - one of {}, e.g. -g 'id:eq:UID' none readonly".format(
                        access.keys()))
                    parser.print_help()
                    sys.exit(1)
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
    api = dhis.Dhis(args.server, args.username, args.password, args.api_version)
    api.assert_version(range(29, 31))

    public_access = Permission.from_public_args(args.public_access)
    logger.info("Public access - {}".format(public_access))

    usergroups = UserGroupsHandler(api, args.groups)
    coll = ShareableObjectCollection(api, args.object_type, args.filter)

    if not coll.share_data:
        if public_access.data:
            logger.error("Cannot share DATA with public access for object type '{}'".format(args.object_type))
            sys.exit(1)
        if [g.permission.data for g in usergroups.accesses]:
            logger.error("Cannot share DATA with userGroups access for object type '{}'".format(args.object_type))
            sys.exit(1)
    else:
        if not public_access.data:
            logger.error("Public access for DATA is not set")
            sys.exit(1)
        if not all([g.permission.data for g in usergroups.accesses]):
            logger.error("UserGroup access for DATA is not set")

    for i, srv_obj in enumerate(coll.elements, 1):
        update = ShareableObject(obj_type=srv_obj.obj_type,
                                 uid=srv_obj.uid,
                                 name=srv_obj.name,
                                 code=srv_obj.code,
                                 public_access=public_access,
                                 usergroup_accesses=usergroups.accesses)

        pointer = u"{0}/{1} {2} {3}".format(i, len(coll.elements), coll.name, srv_obj.uid)

        if not skip(args.overwrite, srv_obj, update):
            logger.info(u"{0} {1}".format(pointer, identifier(srv_obj)))
            api.share(update)

        else:
            logger.warning(u"Skipped: {0} {1}".format(pointer, identifier(srv_obj)))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warn("Aborted.")
