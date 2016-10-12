#!/usr/bin/env python

"""
delete-objects
~~~~~~~~~~~~~~~~~
Deletes DHIS2 objects based on UIDs specified in a text file
"""

import argparse
import os

from src.core.core import Dhis, Logger

parser = argparse.ArgumentParser(description="Delete objects (edit UIDs in file)")
parser.add_argument('-s', '--server', action='store', help='Server, e.g. play.dhis2.org/demo', required=True)
parser.add_argument('-t', '--object_type', action='store', help='API endpoint, e.g. dataElements, ...',
                    required=True)
parser.add_argument('-i', '--uid_file', action='store', help='Text file with all UIDs to delete seperated by new lines',
                    required=True)
parser.add_argument('-u', '--username', action='store', help='DHIS2 username', required=True)
parser.add_argument('-p', '--password', action='store', help='DHIS2 password', required=True)
args = parser.parse_args()

dhis = Dhis(server=args.server, username=args.username, password=args.password)

with open(args.uid_file) as f:
    uids = f.read().splitlines()
amount = str(len(uids))

dhis.log.debug("Received UIDs: \n" + '\n'.join(uids))

for uid in uids:
    msg1 = "Deleting " + uid
    print(msg1)
    dhis.log.info(msg1)

    dhis.delete(endpoint=args.object_type, uid=uid)

    msg2 = "(deleted) - " + str(uids.index(uid)) + " / " + amount
    print(msg2)
    dhis.log.info(msg2)
