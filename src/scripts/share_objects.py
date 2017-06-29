#!/usr/bin/env python

from __future__ import print_function

"""
share-objects
~~~~~~~~~~~~~~~~~
Assigns sharing to shareable DHIS2 objects like userGroups and publicAccess by  calling the /api/sharing endpoint.
"""

import argparse
import sys

from six import iteritems

from src.core.dhis import Dhis
from src.core.logger import *


class Sharer(Dhis):
    """Inherited from core Dhis class to extend functionalities"""

    def get_usergroup_uids(self, filter_list, access):
        """Get UID(s) of userGroup(s) based on object filter"""
        params = {
            'fields': 'id,name',
            'paging': False,
            'filter': filter_list
        }

        print(("\n+++ GET userGroup(s) for filter {} ({})".format(filter_list, access)))

        endpoint = 'userGroups'
        response = self.get(endpoint=endpoint, file_type='json', params=params)

        if len(response['userGroups']) > 0:
            # zip it into a dict { id: name, id:name }
            ugmap = {ug['id']: ug['name'] for ug in response['userGroups']}
            for (key, value) in iteritems(ugmap):
                log_info(u"{} - {}".format(key, value))
            return ugmap.keys()
        else:
            log_info(u"+++ No userGroup(s) found. Check your filter / DHIS2")
            sys.exit()

    def get_objects(self, objects, objects_filter, delimiter):
        """Returns filtered DHIS2 objects"""

        params = {
            'fields': 'id,name,code',
            'filter': objects_filter,
            'paging': False
        }
        if delimiter:
            params['rootJunction'] = 'OR'

        print("\n+++ GET {} with filter(s) {}".format(objects, objects_filter))
        response = self.get(endpoint=objects, file_type='json', params=params)

        if response:
            if len(response[objects]) > 0:
                return response
        log_info(u'+++ No objects found. Wrong filter?')
        log_debug(u'objects: {}'.format(objects.encode('utf-8')))
        sys.exit()

    def share_object(self, pload, pmeters):
        """Share object by using sharing enpoint"""
        self.post(endpoint="sharing", params=pmeters, payload=pload)

    def get_object_type(self, argument):
        return super(Sharer, self).get_shareable_object_type(argument)


def parse_args():
    parser = argparse.ArgumentParser(usage='%(prog)s [-h] -s -t -f [-w] [-r] -a [-v] -u -p -d',
                                     description="PURPOSE: Share DHIS2 objects (dataElements, programs, ...) "
                                                 "with userGroups")
    parser.add_argument('-s', dest='server', action='store', required=True,
                        help="DHIS2 server URL, e.g. 'play.dhis2.org/demo'")
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
    parser.add_argument('-a', dest='publicaccess', action='store', required=True, choices=Dhis.public_access.keys(),
                        help="publicAccess (with login), e.g. -a=readwrite")
    parser.add_argument('-v', dest='api_version', action='store', required=False, type=int,
                        help='DHIS2 API version e.g. -v=24')
    parser.add_argument('-u', dest='username', action='store', required=True, help='DHIS2 username, e.g. -u=admin')
    parser.add_argument('-p', dest='password', action='store', required=True, help='DHIS2 password, e.g. -p=district')
    parser.add_argument('-d', dest='debug', action='store_true', default=False, required=False,
                        help="Debug flag - writes more info to log file, e.g. -d")
    return parser.parse_args()


def filter_delimiter(argument, dhis_version):

    if '||' in argument:
        if dhis_version < 25:
            sys.exit("rootJunction=OR is only supported 2.25 onwards. Exiting.")
        return '||'
    else:
        return '&&'


def main():
    args = parse_args()
    init_logger(args.debug)
    log_start_info(__file__)
    dhis = Sharer(server=args.server, username=args.username, password=args.password, api_version=args.api_version)

    dhis_version = dhis.get_dhis_version()

    # get the real valid object type name
    object_type = dhis.get_object_type(args.object_type)

    user_group_accesses = []
    if args.usergroup_readwrite:

        delimiter = filter_delimiter(args.usergroup_readwrite, dhis_version)
        # split filter of arguments into list
        rw_ug_filter_list = args.usergroup_readwrite.split(delimiter)
        # get UIDs of usergroups with RW access
        readwrite_usergroup_uids = dhis.get_usergroup_uids(rw_ug_filter_list, 'readwrite')
        for ug in readwrite_usergroup_uids:
            acc = {
                'id': ug,
                'access': dhis.public_access['readwrite']
            }
            user_group_accesses.append(acc)

    if args.usergroup_readonly:
        delimiter = filter_delimiter(args.usergroup_readonly, dhis_version)
        ro_ug_filter_list = args.usergroup_readonly.split(delimiter)
        # get UID(s) of usergroups with RO access
        readonly_usergroup_uids = dhis.get_usergroup_uids(ro_ug_filter_list, 'readonly')
        for ug in readonly_usergroup_uids:
            acc = {
                'id': ug,
                'access': dhis.public_access['readonly']
            }
            user_group_accesses.append(acc)

    # split arguments for multiple filters for to-be-shared objects
    delimiter = filter_delimiter(args.filter, dhis_version)
    object_filter_list = args.filter.split(delimiter)

    # pull objects for which to apply sharing
    data = dhis.get_objects(object_type, object_filter_list, delimiter)

    no_of_obj = len(data[object_type])
    counter = 1
    for obj in data[object_type]:
        payload = {
            'object': {
                'publicAccess': dhis.public_access[args.publicaccess],
                'externalAccess': False,
                'user': {},
                'userGroupAccesses': user_group_accesses
            }
        }
        # strip name to match API (e.g. dataElements -> dataElement)
        if object_type == 'categories':
            object_type_singular = 'category'
        else:
            object_type_singular = object_type[:-1]
        parameters = {
            'type': object_type_singular,
            'id': obj['id']
        }

        # apply sharing
        dhis.share_object(payload, parameters)

        try:
            log_info(u"({}/{}) [OK] {} {}".format(counter, no_of_obj, obj['id'], obj['name'].encode('utf-8')))
        except UnicodeEncodeError:
            try:
                log_info(u"({}/{}) [OK] {} {}".format(counter, no_of_obj, obj['id'], obj['code']))
            except KeyError:
                log_info(u"({}/{}) [OK] {}".format(counter, no_of_obj, obj['id']))

        counter += 1

if __name__ == "__main__":
    main()
