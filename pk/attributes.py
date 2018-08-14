#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
from copy import deepcopy

from dhis2 import setup_logger, logger, load_csv

import common

OBJ_TYPES = {
    'categories',
    'categoryOptionCombos',
    'categoryOptionGroupSets',
    'categoryOptionGroups',
    'categoryOptions',
    'constants',
    'dataElementGroupSets',
    'dataElementGroups',
    'dataElements',
    'dataSets',
    'documents',
    'indicatorGroups',
    'indicators',
    'legends',
    'legendSets',
    'optionSets',
    'options',
    'organisationUnitGroupSets',
    'organisationUnitGroups',
    'organisationUnits',
    'programIndicators',
    'programStages',
    'programs',
    'sections',
    'sqlViews',
    'trackedEntityAttributes',
    'trackedEntityTypes',
    'trackedEntities',
    'userGroups',
    'users',
    'validationRuleGroups',
    'validationRules'
}


def parse_args():
    usage = "dhis2-pk-attribute-setter [-s] [-u] [-p] -c -t -a" \
            "\n\n\033[1mExample:\033[0m " \
            "\ndhis2-pk-attribute-setter -s=play.dhis2.org -u=admin -p=district " \
            "-c=file.csv -t=organisationUnits -a=pt5Ll9bb2oP" \
            "\n\n\033[1mCSV file structure:\033[0m         " \
            "\nkey     | value                             " \
            "\n--------|--------                           " \
            "\nUID     | myValue                          " \
            "\n                                            "
    parser = argparse.ArgumentParser(
        description="Post Attribute Values sourced from CSV file", usage=usage)
    parser.add_argument('-s', dest='server', action='store',
                        help="DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo")
    parser.add_argument('-c', dest='source_csv', action='store', help="CSV file with Attribute values",
                        required=True)
    parser.add_argument('-t', dest='object_type', action='store', help="DHIS2 object type to set attribute values",
                        required=True, choices=OBJ_TYPES)
    parser.add_argument('-a', dest='attribute_uid', action='store', help='Attribute UID', required=True)
    parser.add_argument('-u', dest='username', action='store', help="DHIS2 username")
    parser.add_argument('-p', dest='password', action='store', help="DHIS2 password")
    parser.add_argument('-d', dest='debug', action='store_true', default=False, required=False,
                        help="Writes more info in log file")

    return parser.parse_args()


def validate_csv(data):
    if not data[0].get('key', None) or not data[0].get('value', None):
        common.log_and_exit("CSV not valid: CSV must have 'key' and 'value' as headers")

    object_uids = [obj['key'] for obj in data]
    for uid in object_uids:
        if not common.valid_uid(uid):
            common.log_and_exit("Object {} is not a valid UID in the CSV".format(uid))
    if len(object_uids) != len(set(object_uids)):
        common.log_and_exit("Duplicate Objects (rows) found in the CSV.")
    return True


def create_or_update_attribute_values(obj, attribute_uid, attribute_value):
    obj_copy = deepcopy(obj)
    updated = {
        "value": attribute_value,
        "attribute": {
            "id": attribute_uid,
        }
    }
    # if no single attribute is set
    if not obj.get('attributeValues', None):
        obj_copy['attributeValues'] = [updated]
        return obj_copy

    if len(obj['attributeValues']) == 1 and attribute_uid in [x['attribute']['id'] for x in obj['attributeValues']]:
        # just one attribute matching to target UID
        obj_copy['attributeValues'] = [updated]
        return obj_copy
    else:
        # there are more than 1 attribute values.
        # extract all values except target UID (if existing) and add target value.
        old = [x for x in obj['attributeValues'] if x['attribute']['id'] != attribute_uid]
        obj_copy['attributeValues'] = old
        obj_copy['attributeValues'].append(updated)
        return obj_copy


def main():
    args = parse_args()
    api = common.create_api(server=args.server, username=args.username, password=args.password)

    if not common.valid_uid(args.attribute_uid):
        common.log_and_exit("Attribute {} is not a valid UID".format(args.attribute_uid))

    setup_logger()

    data = load_csv(args.source_csv)
    validate_csv(data)

    attr_get = {'fields': 'id,name,{}Attribute'.format(args.object_type[:-1])}
    attr = api.get('attributes/{}'.format(args.attribute_uid), params=attr_get)
    if attr['{}Attribute'.format(args.object_type[:-1])] is False:
        common.log_and_exit("Attribute {} is not assigned to type {}".format(args.attribute_uid, args.object_type[:-1]))

    print(u"[{}] - Updating Attribute Values for Attribute '{}' for {} {} ...".format(args.server, args.attribute_uid, len(data), args.object_type))
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        logger.warn("{}".format("Aborted!"))
        pass

    for i, obj in enumerate(data, 1):
        obj_uid = obj.get('key')
        attribute_value = obj.get('value')

        params_get = {'fields': ':owner'}
        obj_old = api.get('{}/{}'.format(args.object_type, obj_uid), params=params_get)

        obj_updated = create_or_update_attribute_values(obj_old, args.attribute_uid, attribute_value)

        api.put('{}/{}'.format(args.object_type, obj_uid), data=obj_updated)
        print(u"{}/{} - Updated AttributeValue: {} - {}: {}".format(i, len(data), attribute_value, args.object_type[:-1], obj_uid))


if __name__ == "__main__":
    main()
