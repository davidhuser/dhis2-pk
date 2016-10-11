#!/usr/bin/env python

"""
delete-objects
~~~~~~~~~~~~~~~~~
This script deletes objects based on UIDs specified in a text file
"""

import requests, logging, argparse

parser = argparse.ArgumentParser(description="Delete objects (edit UIDs in file)")
parser.add_argument('--server', action='store', help='Server, e.g. play.dhis2.org/demo')
parser.add_argument('--object_type', action='store', help='API endpoint, e.g. dataElements, ...')
parser.add_argument('--uid_file', action='store', help='Text file with all UIDs to delete seperated by new lines')
parser.add_argument('--username', action='store', help='DHIS2 username')
parser.add_argument('--password', action='store', help='DHIS2 password')
args = parser.parse_args()

logging.basicConfig(filename="delete.out", format='%(levelname)s:%(message)s', filemode='w', level=logging.INFO)

with open(args.uid_file) as f:
    uids = f.read().splitlines()

logging.info("Read UIDs: " + str(uids) + "\n")

amount = str(len(uids))
for uid in uids:
    req = requests.delete("https://" + args.server + "/api/" + args.object_type + "/" + uid,
                          auth=(args.username, args.password))
    logging.info("(" + str(req.status_code) + ") - " + req.url)
    if not req.raise_for_status():
        msg = "(deleted) - " + str(uids.index(uid)) + " / " + amount
        print msg