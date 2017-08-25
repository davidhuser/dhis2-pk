import argparse
import sys
import time

import unicodecsv as csv

from src.core.dhis import Dhis
from src.core.logger import *

PRODUCTIVITY_UID = 'pt5Ll9bb2oP'


def parse_args():
    parser = argparse.ArgumentParser(
        description="Post Orgunit Attribute Values sourced from CSV file")
    parser.add_argument('-s', dest='server', action='store',
                        help="DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo")
    parser.add_argument('-c', dest='source_csv', action='store', help="CSV file with Attribute values",
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

    if '.psi-mis.org' not in args.server:
        log_info("This script is intended only for *.psi-mis.org")
        sys.exit()

    with open(args.source_csv) as f:
        reader = csv.DictReader(f)
        data = [row for row in reader]

        if not data[0].get('orgunit', None) or not data[0].get('value', None):
            log_info("+++ CSV not valid: CSV must have 'orgunit' and 'value' as headers")
            sys.exit()

    cnt = 1
    print("Updating OrgUnit attributes for {} Orgunits on {}...".format(len(data), args.server))
    time.sleep(3)
    for orgunit in data:
        orgunit_uid = orgunit.get('orgunit')
        attribute_value = orgunit.get('value')
        params_get = {'fields': ':owner'}
        ou_obj = dhis.get('organisationUnits/{}'.format(orgunit_uid), params=params_get)
        payload = {
            "value": attribute_value,
            "attribute": {
                "id": PRODUCTIVITY_UID,
            }
        }
        ou_obj['attributeValues'].append(payload)

        dhis.validate(obj_type='organisationUnit', payload=ou_obj)
        dhis.put('organisationUnits/{}'.format(orgunit_uid), params=None, payload=ou_obj)

        print("{} / {} - OrgUnit: {} Value: {} for ProductivityAttribute {}".format(cnt, len(data), orgunit_uid,
                                                                                    attribute_value, PRODUCTIVITY_UID))
        cnt += 1


if __name__ == "__main__":
    main()
