#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time
import sys
from collections import namedtuple
from copy import deepcopy

from colorama import Style
from dhis2 import setup_logger, logger, load_csv, APIException

try:
    import utils
except (SystemError, ImportError):
    from . import utils

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
    description = "{}Set Attribute Values sourced from CSV file.{}".format(Style.BRIGHT, Style.RESET_ALL)

    usage = """
{}Example:{} dhis2-pk-attribute-setter -s=play.dhis2.org/dev -u=admin -p=district -c=file.csv -t=organisationUnits -a=pt5Ll9bb2oP

{}CSV file structure:{}
uid   | attributeValue
------|---------------
UID   | myValue
""".format(Style.BRIGHT, Style.RESET_ALL, Style.BRIGHT, Style.RESET_ALL)

    parser = argparse.ArgumentParser(usage=usage, description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    required.add_argument('-t',
                          dest='object_type',
                          action='store',
                          required=True,
                          help="Object type to set attributeValues to: {organisationUnits, dataElements, ...}")
    required.add_argument('-c',
                          dest='source_csv',
                          action='store',
                          required=True,
                          help="Path to CSV file with Attribute Values")
    required.add_argument('-a',
                          dest='attribute_uid',
                          action='store',
                          help='Attribute UID',
                          required=True)

    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('-s',
                          dest='server',
                          action='store',
                          help="DHIS2 server URL")
    optional.add_argument('-u',
                          dest='username',
                          action='store',
                          help="DHIS2 username")
    optional.add_argument('-p',
                          dest='password',
                          action='store',
                          help="DHIS2 password")

    args = parser.parse_args()
    if args.object_type not in OBJ_TYPES:
        utils.log_and_exit("argument -t must be a valid object_type - one of:\n{}".format(', '.join(sorted(OBJ_TYPES))))
    if not utils.valid_uid(args.attribute_uid):
        utils.log_and_exit("Attribute {} is not a valid UID".format(args.attribute_uid))
    return args


def validate_csv(data):
    if not data[0].get('uid', None) or not data[0].get('attributeValue', None):
        raise ValueError("CSV not valid: CSV must have 'uid' and 'attributeValue' as headers")

    object_uids = [obj['uid'] for obj in data]
    for uid in object_uids:
        if not utils.valid_uid(uid):
            raise ValueError("Object '{}' is not a valid UID in the CSV".format(uid))
    if len(object_uids) != len(set(object_uids)):
        raise ValueError("Duplicate Objects (rows) found in the CSV.")
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


def get_attribute_name(api, uid):
    try:
        return api.get('attributes/{}'.format(uid))
    except APIException as e:
        if e.code == 404:
            raise ValueError("Attribute {} could not be found".format(uid))
        else:
            raise ValueError("Error: {}".format(e))


def attribute_is_on_model(api, attribute, typ):
    attr_get = {'fields': 'id,name,{}Attribute'.format(typ[:-1])}
    attr = api.get('attributes/{}'.format(attribute.uid), params=attr_get)
    if attr['{}Attribute'.format(typ[:-1])] is False:
        raise ValueError("Attribute {} ({}) is not assigned to type {}".format(attribute.name, attribute.uid, typ[:-1]))


def main():
    setup_logger()
    args = parse_args()
    api = utils.create_api(server=args.server, username=args.username, password=args.password)

    Attribute = namedtuple('Attribute', 'uid name')
    Attribute.uid = args.attribute_uid
    Attribute.name = get_attribute_name(api, args.attribute_uid)
    typ = args.object_type

    try:
        attribute_is_on_model(api, Attribute, typ)
    except ValueError as e:
        logger.error(e)
        sys.exit(1)

    data = load_csv(args.source_csv)
    try:
        validate_csv(data)
    except ValueError as e:
        logger.error(e)
        sys.exit(1)

    print(u"[{}] - Updating Attribute Values '{}' ({}) for {} {} ...".format(args.server, Attribute.name, Attribute.uid, len(data), typ))
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        logger.warn("{}".format("Aborted!"))
        pass

    for i, obj in enumerate(data, 1):
        obj_uid = obj['uid']
        attribute_value = obj['attributeValue']

        obj_old = api.get('{}/{}'.format(args.object_type, obj_uid), params={'fields': ':owner'})
        obj_updated = create_or_update_attribute_values(obj_old, Attribute.uid, attribute_value)

        try:
            api.put('{}/{}'.format(typ, obj_uid), data=obj_updated)
        except APIException as e:
            logger.error(e)
            sys.exit(1)
        else:
            print(u"{}/{} - Updated AttributeValue: {} - {}: {}".format(i, len(data), attribute_value, typ[:-1], obj_uid))


if __name__ == "__main__":
    main()
