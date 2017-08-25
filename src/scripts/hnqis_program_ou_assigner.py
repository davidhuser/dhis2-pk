import argparse
import sys
import json

from collections import defaultdict

import unicodecsv as csv

from src.core.dhis import Dhis
from src.core.logger import *


def parse_args():
    parser = argparse.ArgumentParser(
        description="Assign OrgUnits to Programs sourced from CSV file (REPLACE)")
    parser.add_argument('-s', dest='server', action='store',
                        help="DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo")
    parser.add_argument('-c', dest='source_csv', action='store', help="CSV file with Orgunits and their Program assignments",
                        required=True)
    parser.add_argument('-u', dest='username', action='store', help="DHIS2 username")
    parser.add_argument('-p', dest='password', action='store', help="DHIS2 password")
    parser.add_argument('-v', dest='api_version', action='store', required=False, type=int,
                        help='DHIS2 API version e.g. -v=24')
    parser.add_argument('-d', dest='debug', action='store_true', default=False, required=False,
                        help="Writes more info in log file")

    return parser.parse_args()


def main():
    args = parse_args()
    init_logger(args.debug)
    log_start_info(__file__)

    dhis = Dhis(server=args.server, username=args.username, password=args.password, api_version=args.api_version)

    #if '.psi-mis.org' not in args.server:
    #    log_info("This script is intended only for *.psi-mis.org")
    #    sys.exit()

    with open(args.source_csv) as f:
        reader = csv.DictReader(f)
        data = [row for row in reader]

    if not data[0].get('orgunit', None):
        log_info("+++ CSV not valid: CSV must have 'orgunit' header")
        sys.exit()

    if len(data[0]) <= 1:
        log_info("+++ No programs found in CSV")
        sys.exit()

    orgunit_uids = [ou['orgunit'] for ou in data]
    if len(orgunit_uids) != len(set(orgunit_uids)):
        print("Duplicate Orgunits (rows) found in the CSV")
        sys.exit()

    program_uids = [h.strip() for h in data[0] if h != 'orgunit']
    for p in program_uids:
        dhis.get('programs/{}'.format(p))

    program_orgunit_map = {}
    # pmap = {
    #  "programuid":["orgunitid1", ...],
    # }

    for a in data:
        for k, v in a.iteritems():
            if k != 'orgunit':
                if v.lower() == 'yes':
                    if k not in program_orgunit_map:
                        program_orgunit_map[k] = list()
                    program_orgunit_map[k].append(a['orgunit'])

    print("\n")
    print(json.dumps(program_orgunit_map))

    print("REPLACING Orgunit<->Program assignment...")

    metadata_payload = []
    final = {}

    for program_uid, orgunit_list in program_orgunit_map.iteritems():
        params_get = {'fields': ':owner'}
        program = dhis.get('programs/{}'.format(program_uid), params=params_get)
        tmp = []
        for ou in orgunit_list:
            tmp.append({"id": ou})

        program['organisationUnits'] = tmp

        metadata_payload.append(program)

    final['programs'] = metadata_payload

    dhis.validate(obj_type='program', payload=final)
    params_post = {
        "mergeMode": "REPLACE",
        "strategy": "UPDATE"
    }
    dhis.post(endpoint='metadata', params=params_post, payload=final)

if __name__ == "__main__":
    main()
