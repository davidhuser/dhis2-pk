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
import operator
import time

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

NEW_SYNTAX = 29


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

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.metadata == other.metadata and
                self.data == other.data)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.metadata, self.data))

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
        logger.debug(self.to_symbol())
        if self.data:
            return '[metadata:{}] [data:{}]'.format(self.metadata, self.data)
        else:
            return '[metadata:{}]'.format(self.metadata)


class ShareableObjectCollection(object):

    def __init__(self, api, obj_type, filters):
        self.api = api
        self.name, self.plural = self.get_name(obj_type)
        self.filters = filters
        self.delimiter, self.root_junction = set_delimiter(api, filters)
        self.data_sharing_enabled = self.is_data_shareable()

        from_server = self.get_objects().get(self.plural)
        self.elements = set(self.create_obj(from_server))

    def add(self, other):
        self.elements.add(other)

    def schema(self, schema_property):

        params = {
            'fields': 'name,plural,shareable,dataShareable'
        }

        r = self.api.get(endpoint='schemas', params=params)

        if schema_property == 'shareable':
            return {x['name']: x['plural'] for x in r['schemas'] if x['shareable']}
        if schema_property == 'dataShareable':
            try:
                return {x['name']: x['plural'] for x in r['schemas'] if x['dataShareable']}
            except KeyError:
                return None

    def get_name(self, obj_type):
        shareable = self.schema('shareable')
        for name, plural in iteritems(shareable):
            if obj_type.lower() in (name.lower(), plural.lower()):
                return name, plural
        logger.error("No DHIS2 object type for '{}'".format(obj_type))
        sys.exit(1)

    def is_data_shareable(self):
        data_shareable = self.schema('dataShareable')
        if not data_shareable:
            return False
        for name, plural in iteritems(data_shareable):
            if self.name in (name, plural):
                return True
        return False

    def get_objects(self):

        params = {
            'fields': 'id,name,code,publicAccess,userGroupAccesses',
            'paging': False
        }
        split = None
        if self.filters:
            split = self.filters.split(self.delimiter)
            params['filter'] = split

        if self.root_junction == 'OR':
            params['rootJunction'] = self.root_junction
        response = self.api.get(self.plural, params=params)
        if response:
            amount = len(response[self.plural])
            if amount > 0:
                if amount == 1:
                    name = self.name
                else:
                    name = self.plural
                if self.filters:
                    print_msg = u"Sharing {} {} with filter [{}]"
                    logger.info(print_msg.format(amount, name, " {} ".format(self.root_junction).join(split)))
                else:
                    print_msg = u"Sharing *ALL* {} {} (no filters set!). Continuing in 10 seconds..."
                    logger.warn(print_msg.format(amount, name))
                    time.sleep(10)
                return response
            else:
                logger.warning(u'No {} found - check your filter'.format(self.plural))
                import sys
                sys.exit(0)

    def create_obj(self, response):
        for elem in response:
            try:
                public_access = Permission.from_symbol(elem['publicAccess'])
            except KeyError:
                logger.error("ServerError: Public access is not set for {} {} '{}'".format(self.name, elem['id'], elem['name']))
            else:
                yield ShareableObject(obj_type=self.name,
                                      uid=elem['id'],
                                      name=elem['name'],
                                      code=elem.get('code'),
                                      public_access=public_access,
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
        self.log_identifier = self.identifier()

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.obj_type == other.obj_type and
                self.uid == other.uid and
                self.name == other.name and
                self.public_access == other.public_access and
                sorted(self.usergroup_accesses, key=operator.attrgetter('uid')) ==
                sorted(other.usergroup_accesses, key=operator.attrgetter('uid')) and
                self.code == other.code)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.obj_type, self.uid, self.name, self.public_access, tuple(self.usergroup_accesses)))

    def __str__(self):
        s = '\n{} {} ({}) PA: {} UGA: {}\n'.format(
            self.obj_type,
            self.name,
            self.uid,
            self.public_access,
            self.usergroup_accesses)
        return s

    def __repr__(self):
        s = "<{} id='{}'" \
            " publicAccess='{}'" \
            " userGroupAccess='{}'>".format(self.obj_type,
                                            self.uid,
                                            self.public_access.to_symbol(),
                                            ','.join([json.dumps(x.to_json()) for x in self.usergroup_accesses]))
        return s

    def identifier(self):
        try:
            return u"'{}'".format(self.name)
        except KeyError:
            try:
                return u"'{}'".format(self.code)
            except KeyError:
                return u''

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
        try:
            permission = Permission.from_symbol(data['access'])
        except (ValueError, KeyError):
            permission = Permission(None, None)
        return cls(data['id'], permission)

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


class UserGroupsCollection(object):
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

                delimiter, root_junction = set_delimiter(api, group_filter)
                filter_list = group_filter.split(delimiter)
                usergroups = self.get_usergroup_uids(filter_list, root_junction)
                log_msg = u"User Groups with filter [{}]"
                logger.info(log_msg.format(u" {} ".format(root_junction).join(filter_list)))

                for uid, name in iteritems(usergroups):
                    logger.info(u"- {} '{}' ➔ {}".format(uid, name, permission))
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
    parser = argparse.ArgumentParser(usage="(example) dhis2-pk-share -s play.dhis2.org/dev -u admin -p district "
                                           "-f 'id:eq:P3jJH5Tu5VC' -t dataelement -a readonly "
                                           "-g 'name:like:Admin' readwrite "
                                           "-g 'name:like:Research' readwrite",
                                     description="Share DHIS2 objects with userGroups via filters.",
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
                          help="DHIS2 object type to apply sharing, e.g. -t sqlView")

    required.add_argument('-a',
                          dest='public_access',
                          action='append',
                          required=True,
                          nargs='+',
                          metavar='PUBLICACCESS',
                          choices=access.keys(),
                          help=textwrap.dedent('''\
                            Public Access for all objects. 
                            Valid choices are: {{{}}}
                            For setting DATA access, add second argument, e.g. -a readwrite readonly
                          '''.format(', '.join(access.keys()))))

    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('-f',
                          dest='filter',
                          action='store',
                          required=False,
                          help=textwrap.dedent('''\
                                Filter on objects with DHIS2 field filter.
                                To add multiple filters:
                                - '&&' joins filters with AND
                                - '||' joins filters with OR
                                Example:  -f 'name:like:ABC||code:eq:X'
                                   '''))
    optional.add_argument('-g',
                          dest='groups',
                          action='append',
                          required=False,
                          metavar='USERGROUP',
                          nargs='+',
                          help=textwrap.dedent('''\
                            User Group to share objects with: FILTER METADATA [DATA]
                            - FILTER: Filter all User Groups. See -f for filtering mechanism
                            - METADATA: Metadata access for this User Group. {readwrite, none, readonly}
                            - DATA: Data access for this User Group. {readwrite, none, readonly}
                            Example:  -g 'id:eq:OeFJOqprom6' readwrite none
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
                          metavar='FILEPATH',
                          help="Path to Log file (default level: INFO, pass -d for DEBUG)")
    optional.add_argument('-v',
                          dest='api_version',
                          action='store',
                          required=False,
                          type=int,
                          help='DHIS2 API version e.g. -v 28')
    optional.add_argument('-u',
                          dest='username',
                          action='store',
                          help='DHIS2 username, e.g. -u admin')
    optional.add_argument('-p',
                          dest='password',
                          action='store',
                          help='DHIS2 password, e.g. -p district')
    optional.add_argument('-d',
                          dest='debug',
                          action='store_true',
                          default=False,
                          required=False,
                          help="Debug flag")
    return parser.parse_args()


def validate_args(args, dhis_version):
    if len(args.public_access) not in (1, 2):
        log_and_exit("ArgumentError: Must use -a METADATA [DATA] - max. 2 arguments")
    if args.groups:
        for group in args.groups:
            try:
                metadata_permission = group[1]
            except IndexError:
                metadata_permission = None
                log_and_exit("ArgumentError: Missing User Group permission for METADATA access")
            if metadata_permission not in access.keys():
                log_and_exit('ArgumentError: User Group permission for METADATA access not valid: "{}"'.format(
                    metadata_permission))
            if dhis_version >= NEW_SYNTAX:
                try:
                    data_permission = group[2]
                except IndexError:
                    pass
                else:
                    if data_permission not in access.keys():
                        log_and_exit('ArgumentError: User Group permission for DATA access not valid: "{}"'.format(
                            data_permission))


def validate_data_access(public_access, collection, usergroups, dhis_version):
    if dhis_version < NEW_SYNTAX:
        if public_access.data or any([group.permission.data for group in usergroups.accesses]):
            log_and_exit("ArgumentError: You cannot set DATA access on DHIS2 versions below 2.29"
                         " - check your arguments (-a) and (-g)")
    else:
        if collection.data_sharing_enabled:
            log_msg = "ArgumentError: Missing {} permission for DATA access for '{}' (Argument {})"
            if not public_access.data:
                log_and_exit(log_msg.format('Public Access', collection.name, '-a'))
            if not all([group.permission.data for group in usergroups.accesses]):
                log_and_exit(log_msg.format('User Groups', collection.name, '-g'))
        else:
            log_msg = "ArgumentError: Not possible to set {} permission for DATA access for '{}' (Argument {})"
            if public_access.data:
                log_and_exit(log_msg.format('Public Access', collection.name, '-a'))
            if any([group.permission.data for group in usergroups.accesses]):
                log_and_exit(log_msg.format('User Group', collection.name, '-g'))


def set_delimiter(api, argument, version=None):
    """
    Operator and rootJunction Alias validation
    :type api: Dhis object
    :param version: DHIS2 version
    :param argument: Argument as received from parser
    :return: tuple(delimiter, rootJunction)
    """
    if not argument:
        return None, None
    if not version:
        version = api.get_dhis_version()
    if '^' in argument:
        if version >= 28:
            log_and_exit("ArgumentError: Operator '^' was replaced with '$' in 2.28 onwards. Nothing shared.")
    if '||' in argument:
        if version < 25:
            log_and_exit("ArgumentError: rootJunction 'OR' / '||' is only supported 2.25 onwards. Nothing shared.")
        if '&&' in argument:
            log_and_exit("ArgumentError: Not allowed to combine delimiters '&&' and '||'. Nothing shared")
        return '||', 'OR'
    return '&&', 'AND'


def log_and_exit(message):
    logger.error(message)
    sys.exit(1)


def main():
    args = parse_args()
    log.init(args.logging_to_file, args.debug)
    api = dhis.Dhis(args.server, args.username, args.password, args.api_version)
    dhis_version = api.assert_version(range(20, 30 + 1))
    validate_args(args, dhis_version)

    public_access = Permission.from_public_args(args.public_access)
    collection = ShareableObjectCollection(api, args.object_type, args.filter)
    usergroups = UserGroupsCollection(api, args.groups)
    validate_data_access(public_access, collection, usergroups, dhis_version)

    logger.info("Public access ➔ {}".format(public_access))

    for i, element in enumerate(collection.elements, 1):
        update = ShareableObject(obj_type=element.obj_type,
                                 uid=element.uid,
                                 name=element.name,
                                 code=element.code,
                                 public_access=public_access,
                                 usergroup_accesses=usergroups.accesses)

        pointer = u"{0}/{1} {2} {3}".format(i, len(collection.elements), collection.name, element.uid)

        if not skip(args.overwrite, element, update):
            logger.info(u"{0} {1}".format(pointer, element.log_identifier))
            api.share(update)

        else:
            logger.warning(u'Not overwriting: {0} {1}'.format(pointer, element.log_identifier))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warn("Aborted.")
