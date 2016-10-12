#!/usr/bin/env python

"""
user-orgunits
~~~~~~~~~~~~~~~~~
Checks each user assigned to an organisation unit if he/she is assigned to both organisation unit
and its sub-organisation units and prints them with their UID.
"""

import argparse
import re

from src.core.core import Dhis


def valid_uid(uid):
    "Check if string matches DHIS2 UID pattern"
    return re.compile("[A-Za-z][A-Za-z0-9]{10}").match(uid)


parser = argparse.ArgumentParser(description="Print all users of an orgunit who also have sub-orgunits assigned")
parser.add_argument('-s', '--server', action='store', help='Server, e.g. play.dhis2.org/demo', required=True)
parser.add_argument('-o', '--orgunit', action='store', help='Root orgunit UID to check its users', required=True)
parser.add_argument('-u', '--username', action='store', help='DHIS2 username', required=True)
parser.add_argument('-p', '--password', action='store', help='DHIS2 password', required=True)
args = parser.parse_args()

dhis = Dhis(server=args.server, username=args.username, password=args.password)

if not valid_uid(args.orgunit):
    msg1 = 'Orgunit is not a valid DHIS2 UID'
    dhis.log.info(msg1)
    raise argparse.ArgumentError(args.orgunit, msg1)

orgunit_root_uid = args.orgunit

# get root orgunit
endpoint1 = "organisationUnits/" + orgunit_root_uid
params1 = {
    "fields": "id,name,path,users"
}
orgunit_root = dhis.get(endpoint=endpoint1, params=params1)

# get path of root orgunit
path = orgunit_root['path']

# get all descendant orgunit UIDs (excluding self) via 'path' field filter
endpoint2 = "organisationUnits"
params2 = {
    "filter": [
        "path:^like:" + path,
        "id:!eq:" + orgunit_root_uid
    ],
    "fields": "id",
    "paging": False
}
resp2 = dhis.get(endpoint=endpoint2, params=params2)

no_of_users = len(orgunit_root['users'])

# put the descendant orgunit uids in a list
descendant_uids = []
for ou in resp2['organisationUnits']:
    descendant_uids.append(ou['id'])
msg2 = "Checking " + str(no_of_users) + " users against sub-orgunit assignments of root orgunit " + orgunit_root['name']
print(msg2)
dhis.log.info(msg2)

# check each user of root orgunit
# print user if: [has more than 1 orgunit associated] AND [any other user orgunit is descendant of root_orgunit]
counter = 0
for user in orgunit_root['users']:
    problem = False
    endpoint3 = "users/" + user['id']
    params3 = {
        "fields": "id,name,organisationUnits"
    }
    single_user = dhis.get(endpoint=endpoint3, params=params3)

    user_orgunits = single_user['organisationUnits']

    if len(user_orgunits) > 1:
        # Python2 & 3 compatibility
        try:
            xrange
        except NameError:
            xrange = range
        for i in xrange(len(user_orgunits)):
            ou_uid = user_orgunits[i]['id']
            if ou_uid is not orgunit_root_uid and ou_uid in descendant_uids:
                problem = True

    if problem:
        msg3 = "Conflicting user found:  " + single_user['name'] + " - UID: " + single_user['id']
        print(msg3)
        dhis.log.info(msg3)
