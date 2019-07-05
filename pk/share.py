#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
share
~~~~~~~~~~~~~~~~~
Assigns sharing to shareable DHIS2 objects like userGroups and publicAccess by calling the /api/sharing endpoint.
"""

import argparse
import json
import operator
import sys
import os
import textwrap
import time
import getpass
from logging import DEBUG

from colorama import Style
from dhis2 import setup_logger, logger
from six import iteritems

try:
    from pk.common.utils import create_api
    from pk.common.exceptions import PKClientException
except (SystemError, ImportError):
    from common.utils import create_api
    from common.exceptions import PKClientException

access = {
    'none': u'--',
    'readonly': u'r-',
    'readwrite': u'rw'
}

NEW_SYNTAX = 29

PUBLIC_ACCESS_INHERITED = '<inherited>'

if os.name == 'nt':
    ARROW = u'=>'  # Windows
else:
    ARROW = u'➡️️'  # ➡


class Permission(object):
    """Class to handle access strings for metadata and data"""
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
        """
        Class method to init an instance from Public Access argument
        :param args: the argparse argument
        :return: class instance or constant
        """
        if args:
            metadata = args[0][0]
            try:
                data = args[0][1]
            except IndexError:
                data = None
            return cls(metadata, data)
        else:
            return PUBLIC_ACCESS_INHERITED

    @classmethod
    def from_symbol(cls, symbol):
        """
        Class method to init an instance from UNIX-style access string (e.g. rw------)
        :param symbol: the unix-style string
        :return: class instance
        """
        if symbol not in Permission.symbolic_notation:
            raise ValueError("Permission symbol '{}' not valid!".format(symbol))
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
        """
        Class method to init an instance from User Group argument(s)
        :param args: the argparse arguments
        :return: class instance
        """
        metadata = args[1]
        try:
            data = args[2]
        except IndexError:
            data = None
        return cls(metadata, data)

    def to_symbol(self):
        """
        Convert to UNIX-style access string (e.g. rw------)
        :return: unix-style string
        """
        m = access.get(self.metadata, '--')
        d = access.get(self.data, '--')
        return '{}{}----'.format(m, d)

    def __str__(self):
        if self.data:
            return '[metadata:{}] [data:{}]'.format(str(self.metadata).lower(), str(self.data).lower())
        else:
            return '[metadata:{}]'.format(str(self.metadata).lower())

    def __repr__(self):
        return '{} {}'.format(self.metadata, self.data)


class ShareableObjectCollection(object):
    """A collection of shareable objects, e.g. a set of data elements"""
    def __init__(self, api, obj_type, filters):
        self.api = api
        self.name, self.plural = self.get_name(obj_type)
        self.filters = filters
        self.delimiter, self.root_junction = set_delimiter(api.version_int, filters)
        self.data_sharing_enabled = self.is_data_shareable()

        from_server = self.get_objects().json().get(self.plural)
        self.elements = set(self.create_obj(from_server))

    def add(self, other):
        self.elements.add(other)

    def schema(self, schema_property):
        """
        Return dict of allowed names for object depending if it's (metadata-) shareable or data-shareable
        :param schema_property: shareable or dataShareable
        :return: dict of a mapping of name to its plural name
        """
        params = {
            'fields': 'name,plural,shareable,dataShareable'
        }

        r = self.api.get(endpoint='schemas', params=params).json()

        if schema_property == 'shareable':
            return {x['name']: x['plural'] for x in r['schemas'] if x['shareable']}
        if schema_property == 'dataShareable':
            try:
                return {x['name']: x['plural'] for x in r['schemas'] if x['dataShareable']}
            except KeyError:
                return None

    def get_name(self, obj_type):
        """
        Get an object collection's name and it's plural name
        :param obj_type: type of object, e.g. dataelement
        :return: tuple of name and its plural name, e.g. dataElement, dataElements
        """
        shareable = self.schema('shareable')
        for name, plural in iteritems(shareable):
            if obj_type.lower() in (name.lower(), plural.lower()):
                return name, plural
        raise PKClientException("No DHIS2 object type for '{}'".format(obj_type))

    def is_data_shareable(self):
        """
        Assess if object type can be DATA shared (e.g. data sets)
        :return: true if it's data shareable, False otherwise
        """
        data_shareable = self.schema('dataShareable')
        if not data_shareable:
            return False
        for name, plural in iteritems(data_shareable):
            if self.name in (name, plural):
                return True
        return False

    def get_objects(self):
        """
        Get the actual objects from DHIS 2
        :return: requests response
        """
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
            amount = len(response.json()[self.plural])
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
                    logger.warning(print_msg.format(amount, name))
                    time.sleep(10)
                return response
            else:
                logger.warning(u'No {} found - check your filter'.format(self.plural))
                sys.exit(0)

    def create_obj(self, response):
        """
        Create ShareableObjects from the response
        :param response: server response
        :return yielded ShareableObjects
        """
        for elem in response:
            try:
                public_access = Permission.from_symbol(elem['publicAccess'])
            except ValueError as e:
                raise PKClientException(e)
            except KeyError:
                raise PKClientException("ServerError: Public access is not set "
                                        "for {} {} '{}'".format(self.name, elem['id'], elem['name']))
            else:
                yield ShareableObject(obj_type=self.name,
                                      uid=elem['id'],
                                      name=elem['name'],
                                      code=elem.get('code'),
                                      public_access=public_access,
                                      usergroup_accesses={UserGroupAccess.from_dict(d) for d in
                                                          elem['userGroupAccesses']})

    def __str__(self):
        s = ''
        for obj in self.elements:
            s += str(obj)
        return s


class ShareableObject(object):
    """Class to handle one DHIS2 object's sharing"""
    def __init__(self, obj_type, uid, name, public_access, usergroup_accesses=None, code=None):
        self.obj_type = obj_type
        self.uid = uid
        self.name = name
        self.public_access = public_access if public_access else 'none'
        self.usergroup_accesses = usergroup_accesses if usergroup_accesses else set()
        self.code = code
        self.external_access = False
        self.user = {}
        self.log_identifier = self.identifier()

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.obj_type == other.obj_type and
                self.uid == other.uid and
                self.name == other.name and
                str(self.public_access).lower() == str(other.public_access).lower() and
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
        s = "<{}" \
            " objectType='{}'" \
            " id='{}'" \
            " publicAccess='{}'" \
            " userGroupAccess='{}'>".format(self.__class__.__name__,
                                            self.obj_type,
                                            self.uid,
                                            self.public_access.to_symbol(),
                                            ','.join([json.dumps(x.to_json()) for x in self.usergroup_accesses]))
        return s

    def identifier(self):
        """Pretty-print the object for logging"""
        if self.name:
            return u"'{}'".format(self.name)
        if self.code:
            return u"'{}'".format(self.code)
        else:
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
        """Class method to create instance from UNIX-style access string"""
        try:
            permission = Permission.from_symbol(data['access'])
        except (ValueError, KeyError):
            permission = Permission(None, None)
        return cls(data['id'], permission)

    @classmethod
    def from_ugam(cls, obj):
        """Class method to cast from UserGroupAccessMerge instance"""
        if not isinstance(obj, UserGroupAccessMerge):
            raise TypeError("Not an object of type UserGroupAccessMerge")
        return cls(obj.uid, obj.permission)

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

    def __repr__(self):
        return "<UserGroupAccess uid='{}' permission='{}'>".format(self.uid, self.permission)

    def to_json(self):
        return {"id": self.uid, "access": self.permission.to_symbol()}


class UserGroupAccessMerge(UserGroupAccess):
    """
    Class inheriting from UserGroupAccess for Sets
    Useful to prevent double-adding in a Set to prevent double specification of sharing settings
    when it's defined but with a different permission
    """
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.uid == other.uid

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.uid)

    def __repr__(self):
        return "<UserGroupAccessMerge uid='{}' permission='{}'>".format(self.uid, self.permission)


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

                delimiter, root_junction = set_delimiter(api.version_int, group_filter)
                filter_list = group_filter.split(delimiter)
                usergroups = self.get_usergroup_uids(filter_list, root_junction)
                log_msg = u"User Groups with filter [{}]"
                logger.info(log_msg.format(u" {} ".format(root_junction).join(filter_list)))

                for uid, name in iteritems(usergroups):
                    logger.info(u"- {} '{}' {} {}".format(uid, name, ARROW, permission))
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
        response = self.api.get(endpoint, params=params).json()
        if len(response['userGroups']) > 0:
            return {ug['id']: ug['name'] for ug in response['userGroups']}
        else:
            raise PKClientException("No userGroup found with {}".format(filter_list))


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
    """Argument parsing"""
    description = "{}Share DHIS2 objects with userGroups via filters.{}".format(Style.BRIGHT, Style.RESET_ALL)
    usage = """
{}Example:{} dhis2-pk-share -s play.dhis2.org/dev -u admin -p district -f 'id:eq:P3jJH5Tu5VC' -t dataelement -a readonly -g 'name:like:Admin' readwrite -g 'name:like:Research' readwrite
""".format(Style.BRIGHT, Style.RESET_ALL)
    parser = argparse.ArgumentParser(usage=usage,
                                     description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')

    required.add_argument('-t',
                          dest='object_type',
                          action='store',
                          required=True,
                          help="DHIS2 object type to apply sharing, e.g. -t sqlView")

    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('-a',
                          dest='public_access',
                          action='append',
                          required=False,
                          nargs='+',
                          metavar='PUBLICACCESS',
                          choices=access.keys(),
                          help=textwrap.dedent('''\
                            Public Access for all objects. 
                            Valid choices are: {{{}}}
                            For setting DATA access, add second argument, e.g. -a readwrite readonly
                          '''.format(', '.join(access.keys()))))
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
    optional.add_argument('-e',
                          dest='extend',
                          action='store_true',
                          required=False,
                          default=False,
                          help="Extend existing sharing settings")
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
    optional.add_argument('-s',
                          dest='server',
                          action='store',
                          metavar='URL',
                          help="DHIS2 server URL")
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
    args = parser.parse_args()

    if not args.password:
        if not args.username:
            raise PKClientException("ArgumentError: Must provide a username via argument -u")
        password = getpass.getpass(prompt="Password for {} @ {}: ".format(args.username, args.server))
    else:
        password = args.password
    return args, password


def validate_args(args, dhis_version):
    """
    Validate arguments. Raises Exception if invalid
    :param args: the argparse arguments
    :param dhis_version: DHIS 2 version as an integer (e.g. 32)
    :return: None
    """
    if args.extend:
        if not args.groups and not args.public_access:
            raise PKClientException("ArgumentError: Must supply user groups when extending sharing - check your argument (-g)")
    else:
        if not args.public_access or len(args.public_access) not in (1, 2):
            raise PKClientException("ArgumentError: Must use -a METADATA [DATA] - max. 2 arguments")

    if args.groups:
        for group in args.groups:
            try:
                metadata_permission = group[1]
            except IndexError:
                raise PKClientException("ArgumentError: Missing User Group permission for METADATA access")
            if metadata_permission not in access.keys():
                raise PKClientException('ArgumentError: User Group permission for METADATA access not valid: "{}"'.format(metadata_permission))
            if dhis_version >= NEW_SYNTAX:
                try:
                    data_permission = group[2]
                except IndexError:
                    pass
                else:
                    if data_permission not in access.keys():
                        raise PKClientException(
                            'ArgumentError: User Group permission for DATA access not valid: "{}"'.format(
                                data_permission))


def validate_data_access(public_access, collection, usergroups, dhis_version):
    """
    Validate DATA access against public access, the collection and user groups. Raises Exception if invalid.
    :param public_access: Permission instance
    :param collection: ShareableObjectCollection instance
    :param usergroups: UserGroupsCollection instance
    :param dhis_version: DHIS 2 version as an integer (e.g. 32)
    :return: None
    """
    if dhis_version < NEW_SYNTAX:
        if public_access and public_access != PUBLIC_ACCESS_INHERITED and public_access.data\
                or any([group.permission.data for group in usergroups.accesses]):
            raise PKClientException("ArgumentError: You cannot set DATA access on DHIS2 versions below 2.29 "
                                    "- check your arguments (-a) and (-g)")
    elif public_access != PUBLIC_ACCESS_INHERITED:
        if collection.data_sharing_enabled:
            log_msg = "ArgumentError: Missing {} permission for DATA access for '{}' (argument {})"
            if not public_access.data:
                raise PKClientException(log_msg.format('Public Access', collection.name, '-a'))
            if not all([group.permission.data for group in usergroups.accesses]):
                raise PKClientException(log_msg.format('User Groups', collection.name, '-g'))
        else:
            log_msg = "ArgumentError: Not possible to set {} permission for DATA access for '{}' (argument {})"
            if public_access.data:
                raise PKClientException(log_msg.format('Public Access', collection.name, '-a'))
            if any([group.permission.data for group in usergroups.accesses]):
                raise PKClientException(log_msg.format('User Group', collection.name, '-g'))


def set_delimiter(dhis_version, object_filter):
    """
    Operator and rootJunction alias validation for the DHIS2 API (see DHIS2 developer docs)
    :param dhis_version: DHIS 2 version as an integer (e.g. 32):
    :param object_filter: Metadata object filter
    :return: tuple of aliases for OR / AND
    """
    if not object_filter:
        return None, None
    if '^' in object_filter:
        if dhis_version >= 28:
            raise PKClientException("ArgumentError: Operator '^' was replaced with '$' in 2.28 onwards. Nothing shared.")
    if '||' in object_filter:
        if dhis_version < 25:
            raise PKClientException(
                "ArgumentError: rootJunction 'OR' / '||' is only supported 2.25 onwards. Nothing shared.")
        if '&&' in object_filter:
            raise PKClientException("ArgumentError: Not allowed to combine delimiters '&&' and '||'. Nothing shared")
        return '||', 'OR'
    return '&&', 'AND'


def share(api, sharing_object):
    """
    API POST request to share the object
    :param api: the dhis2.py Api object
    :param sharing_object: ShareableObject instance
    :return: None
    """
    params = {'type': sharing_object.obj_type, 'id': sharing_object.uid}
    api.post('sharing', params=params, data=sharing_object.to_json())


def merge(server_uga, local_uga):
    """
    Merging User Group Accesses on the server with local User Group Accesses (in arguments)
    :param server_uga: An object's server-side User Group Access definitions
    :param local_uga:  An object's locally-defined User Group Access definitions
    :return: set of User Group Accesses
    """
    # if nothing is defined on the server just use what's provided locally
    if not server_uga:
        return local_uga

    # create a set of UserGroupAccessMerge objects
    # Local User Group Access definitions for the same user group
    # have higher priority than those on the server
    merged_ugam = {
        UserGroupAccessMerge(uid=ug.uid, permission=ug.permission)
        for ug
        in list(local_uga) + list(server_uga)
    }

    # need to convert it to UserGroupAccess instances for later comparison of equality
    # and remove metadata=none data=none user group accesses
    return {
        UserGroupAccess.from_ugam(ugam)
        for ugam in merged_ugam
        if any([ugam.permission.metadata, ugam.permission.data])
    }


def main():
    setup_logger(include_caller=False)
    args, password = parse_args()
    if args.logging_to_file:
        if args.debug:
            setup_logger(logfile=args.logging_to_file, log_level=DEBUG, include_caller=True)
        else:
            setup_logger(logfile=args.logging_to_file, include_caller=False)
    elif args.debug:
        setup_logger(log_level=DEBUG, include_caller=True)

    api = create_api(server=args.server, username=args.username, password=password, api_version=args.api_version)
    validate_args(args, api.version_int)

    public_access_permission = Permission.from_public_args(args.public_access)
    collection = ShareableObjectCollection(api, args.object_type, args.filter)
    usergroups = UserGroupsCollection(api, args.groups)
    validate_data_access(public_access_permission, collection, usergroups, api.version_int)

    # sort by name
    try:
        elements = sorted(collection.elements, key=operator.attrgetter('name'))
    except AttributeError:
        elements = collection.elements

    # handle log messages and collection-wide public access and usergroup access if applicable
    if args.extend:
        if not args.public_access:
            logger.warning(u"Public access {} INHERIT".format(ARROW))
        else:
            logger.info(u"Public access {} {}".format(ARROW, public_access_permission))
            public_access = Permission.from_public_args(args.public_access)
        logger.warning(u"Extending with additional User Groups...")

    else:
        logger.info(u"Public access {} {}".format(ARROW, public_access_permission))
        public_access = Permission.from_public_args(args.public_access)
        usergroup_accesses = usergroups.accesses

    time.sleep(2)

    for i, element in enumerate(elements, 1):
        if args.extend:
            # merge user group accesses
            usergroup_accesses = merge(server_uga=element.usergroup_accesses, local_uga=usergroups.accesses)
            # if public access is not provided via argument, re-use public access from object on server
            if not args.public_access:
                public_access = element.public_access

        # no issue for public_access and usergroup_accesses since it's set above with same if/else check
        # to improve performance and allow for logical logging message placement
        # noinspection PyUnboundLocalVariable
        update = ShareableObject(obj_type=element.obj_type,
                                 uid=element.uid,
                                 name=element.name,
                                 code=element.code,
                                 public_access=public_access,
                                 usergroup_accesses=usergroup_accesses)

        pointer = u"{0}/{1} {2} {3}".format(i, len(collection.elements), collection.name, element.uid)

        if not skip(args.overwrite, element, update):
            logger.info(u"{0} {1}".format(pointer, element.log_identifier))
            share(api, update)

        else:
            logger.warning(u'Skipping (already shared): {0} {1}'.format(pointer, element.log_identifier))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Aborted.")
    except PKClientException as e:
        logger.error(e)
    except Exception as e:
        logger.exception(e)
