#!/usr/bin/env python

"""
delete-objects
~~~~~~~~~~~~~~~~~
Deletes DHIS2 objects based on UIDs specified in a text file
"""

import argparse

import requests

objects_types = ['categories', 'categoryOptionGroupSets', 'categoryOptionGroups', 'categoryOptionSets',
                 'categoryOptions', 'charts', 'constants', 'dashboards', 'dataApprovalLevels',
                 'dataElementGroupSets', 'dataElementGroups', 'dataElements', 'dataSets', 'documents',
                 'eventCharts', 'eventReports', 'indicatorGroupSets', 'indicatorGroups', 'indicators',
                 'interpretations', 'maps', 'option', 'optionSets', 'organisationUnitGroupSets',
                 'organisationUnitGroups', 'programIndicators', 'programs', 'reportTables', 'reports',
                 'sqlViews', 'trackedEntityAttributes', 'userRoles', 'validationRuleGroups']

parser = argparse.ArgumentParser(description="Delete objects (edit UIDs in file)")
parser.add_argument('-s', '--server', action='store', help='Server, e.g. play.dhis2.org/demo')
parser.add_argument('-t', '--object_type', action='store', help='API endpoint, e.g. dataElements, ...',
                    choices=objects_types)
parser.add_argument('-f', '--uid_file', action='store', help='Text file with all UIDs to delete seperated by new lines')
parser.add_argument('-u', '--username', action='store', help='DHIS2 username')
parser.add_argument('-p', '--password', action='store', help='DHIS2 password')
args = parser.parse_args()

with open(args.uid_file) as f:
    uids = f.read().splitlines()

amount = str(len(uids))
for uid in uids:
    req = requests.delete("https://" + args.server + "/api/" + args.object_type + "/" + uid,
                          auth=(args.username, args.password))
    if not req.raise_for_status():
        msg = "(deleted) - " + str(uids.index(uid)) + " / " + amount
        print(msg)
