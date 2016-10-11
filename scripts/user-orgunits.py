#!/usr/bin/env python

"""
user-orgunits
~~~~~~~~~~~~~~~~~
This script checks each user assigned to an organisation unit if he/she is assigned to both organisation unit
and its sub-organisation units and prints them with their UID.
"""

import requests, argparse

parser = argparse.ArgumentParser(description="Return all users of orgunit who also have sub-orgunits assigned")
parser.add_argument('--server', action='store', help='Server, e.g. play.dhis2.org/demo')
parser.add_argument('--orgunit', action='store', help='Root orgunit UID to check its users')
parser.add_argument('--username', action='store', help='DHIS2 username')
parser.add_argument('--password', action='store', help='DHIS2 password')
args = parser.parse_args()

# ====================================
server = "https://" + args.server
orgunit_root_uid = args.orgunit

# get root orgunit
req1 = requests.get(server + "/api/organisationUnits/" + orgunit_root_uid + ".json?fields=id,name,path,users",
                    auth=(args.username, args.password))
orgunit_root = req1.json()

# get path of root orgunit
path = orgunit_root['path']

# get all descendant orgunit UIDs (excluding self) via 'path' field filter
req2 = requests.get(
    server + "/api/organisationUnits.json?filter=path:^like:" + path
    + "&filter=id:!eq:" + orgunit_root_uid
    + "&fields=id&paging=false",
    auth=(args.username, args.password))
resp2 = req2.json()

no_of_users = len(orgunit_root['users'])

# put the descendant orgunit uids in a list
descendant_uids = []
for ou in resp2['organisationUnits']:
    descendant_uids.append(ou['id'])
print "Checking " + str(no_of_users) + " users against sub-orgunit assignments of root orgunit " + orgunit_root['name']

# check each user of root orgunit
# print user if: [has more than 1 orgunit associated] AND [any other user orgunit is descendant of root_orgunit]
counter = 0
for user in orgunit_root['users']:
    problem = False
    req3 = requests.get(server + "/api/users/" + user['id'] + ".json?fields=id,name,organisationUnits",
                        auth=(args.username, args.password))
    single_user = req3.json()

    user_orgunits = single_user['organisationUnits']
    if len(user_orgunits) > 1:
        for i in xrange(len(user_orgunits)):
            ou_uid = user_orgunits[i]['id']
            if ou_uid is not orgunit_root_uid and ou_uid in descendant_uids:
                problem = True

    if problem:
        print single_user['name'] + " - UID: " + single_user['id']