#!/usr/bin/env python

"""
share-objects
~~~~~~~~~~~~~~~~~
This script assigns sharing to shareable DHIS2 objects like userGroups and publicAccess.
"""

import json, requests, sys, logging, argparse


class Dhis:
    def __init__(self, server, username, password):
        if "http://" not in server and "https://" not in server:
            self.server = "https://" + server
        else:
            self.server = server
        self.auth = (username, password)

    def get_usergroup_uid(self, usergroup_name):
        """Get UID of userGroup based on userGroup.name"""

        url = self.server + "/api/userGroups.json"

        params = {
            'fields': 'id,name',
            'paging': False,
            'filter': 'name:like:' + usergroup_name
        }

        print "Getting " + usergroup_name + " UID..."
        req = requests.get(url, params=params, auth=self.auth)
        response = req.json()
        if not req.raise_for_status() and len(response['userGroups']) == 1:
            uid = response['userGroups'][0]['id']
            logging.info(usergroup_name + " UID: " + uid)
            return uid
        else:
            msg = 'Failure in getting (only one) userGroup UID for URL ' + req.url
            print msg
            logging.info(msg)
            sys.exit()

    def get_objects(self, objects, objects_filter):
        """Returns DHIS2 filtered objects"""

        url = self.server + "/api/" + objects + ".json"

        params = {
            'fields': 'id,name,code',
            'filter': [objects_filter],
            'paging': False
        }
        print "Getting " + objects + " with filter=" + objects_filter
        req = requests.get(url, params=params, auth=self.auth)
        data = req.json()
        if not req.raise_for_status():
            if len(data[objects]) > 0:
                return data
            else:
                print "No objects found. Wrong filter? URL used: " + req.url
                sys.exit()

    def share_object(self, payload, parameters):
        """Share object by using sharing enpoint"""
        req = requests.post(self.server + '/api/sharing', params=parameters, json=payload, auth=self.auth)
        req.raise_for_status()


def main():
    objects_types = ['categories', 'categoryOptionGroupSets', 'categoryOptionGroups', 'categoryOptionSets',
                     'categoryOptions', 'charts', 'constants', 'dashboards', 'dataApprovalLevels',
                     'dataElementGroupSets', 'dataElementGroups', 'dataElements', 'dataSets', 'documents',
                     'eventCharts', 'eventReports', 'indicatorGroupSets', 'indicatorGroups', 'indicators',
                     'interpretations', 'maps', 'option', 'optionSets', 'organisationUnitGroupSets',
                     'organisationUnitGroups', 'programIndicators', 'programs', 'reportTables', 'reports', 'sqlViews',
                     'trackedEntityAttributes', 'userRoles', 'validationRuleGroups']

    public_access = {
        'none': '--------',
        'readonly': 'r-------',
        'readwrite': 'rw------'
    }

    # argument parsing
    parser = argparse.ArgumentParser(description="Share DHIS2 objects (dataElements, programs, ...) with userGroups")
    parser.add_argument('--server', action='store', required=True, help='DHIS2 server, e.g. "play.dhis2.org/demo"')
    parser.add_argument('--object_type', action='store', required=True, choices=objects_types,
                        help='DHIS2 objects to apply sharing')
    parser.add_argument('--filter', action='store', required=True,
                        help='Filter on object name according to DHIS2 field filter')
    parser.add_argument('--usergroup_readwrite', action='store', required=False,
                        help='UserGroup Name with Read-Write rights')
    parser.add_argument('--usergroup_readonly', action='store', required=False,
                        help='UserGroup Name with Read-Only rights')
    parser.add_argument('--publicaccess', action='store', required=True, choices=public_access.keys(),
                        help='publicAccess (with login)')
    parser.add_argument('--username', action='store', required=True, help='DHIS2 username')
    parser.add_argument('--password', action='store', required=True, help='DHIS2 password')
    args = parser.parse_args()

    logging.basicConfig(filename="sharing.out", format='%(levelname)s:%(message)s', filemode='w', level=logging.INFO)

    # init DHIS
    dhis = Dhis(args.server, args.username, args.password)

    # get UID of usergroup with RW access
    readwrite_usergroup_uid = dhis.get_usergroup_uid(args.usergroup_readwrite)

    # get UID of usergroup with RO access
    readonly_usergroup_uid = dhis.get_usergroup_uid(args.usergroup_readonly)

    # pull objects for which to apply sharing
    data = dhis.get_objects(args.object_type, args.filter)

    no_of_obj = len(data[args.object_type])
    print "Fetched " + str(no_of_obj) + " " + args.object_type + " to apply sharing..."

    counter = 1
    for obj in data[args.object_type]:
        payload = {
            "meta": {
                "allowPublicAccess": True,
                "allowExternalAccess": False
            },
            "object": {
                "id": obj['id'],
                "name": obj['name'],
                "publicAccess": public_access[args.publicaccess],
                "externalAccess": False,
                "user": {},
                "userGroupAccesses": [
                    {
                        "id": readwrite_usergroup_uid,
                        "access": "rw------"
                    },
                    {
                        "id": readonly_usergroup_uid,
                        "access": "r-------"
                    }
                ]
            }
        }
        # strip name to match API (e.g. dataElements -> dataElement)
        parameters = {
            'type': args.object_type[:-1],
            'preheatCache': False,
            'id': obj['id']
        }

        logging.info(json.dumps(payload))

        # apply sharing
        dhis.share_object(payload, parameters)

        print "(" + str(counter) + "/" + str(no_of_obj) + ") [OK] " + obj['name']
        counter += 1


if __name__ == "__main__":
    main()