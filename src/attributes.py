#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from collections import namedtuple
from copy import deepcopy

from dhis2 import setup_logger, logger, load_csv, is_valid_uid, RequestException

try:
    from src.common.utils import create_api
    from src.common.exceptions import PKClientException
except (SystemError, ImportError):
    from common.utils import create_api
    from common.exceptions import PKClientException


def validate_csv(data):
    if not data[0].get('uid', None) or not data[0].get('attributeValue', None):
        raise PKClientException("CSV not valid: CSV must have 'uid' and 'attributeValue' as headers")

    object_uids = [obj['uid'] for obj in data]
    for uid in object_uids:
        if not is_valid_uid(uid):
            raise PKClientException("Object '{}' is not a valid UID in the CSV".format(uid))
    if len(object_uids) != len(set(object_uids)):
        raise PKClientException("Duplicate Objects (rows) found in the CSV.")
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
    if not obj.get('attributeValues'):
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
        return api.get('attributes/{}'.format(uid)).json()['name']
    except RequestException as exc:
        if exc.code == 404:
            raise PKClientException("Attribute {} could not be found".format(uid))
        else:
            raise PKClientException("Error: {}".format(exc))


def attribute_is_on_model(api, attribute, typ):
    attr_get = {'fields': 'id,name,{}Attribute'.format(typ[:-1])}
    attr = api.get('attributes/{}'.format(attribute.uid), params=attr_get).json()
    if attr['{}Attribute'.format(typ[:-1])] is False:
        raise PKClientException("Attribute {} ({}) is not assigned to type {}".format(attribute.name, attribute.uid, typ[:-1]))


def main(args, password):
    setup_logger()
    api = create_api(server=args.server, username=args.username, password=password)

    Attribute = namedtuple('Attribute', 'uid name')
    Attribute.uid = args.attribute_uid
    Attribute.name = get_attribute_name(api, args.attribute_uid)
    typ = args.object_type

    attribute_is_on_model(api, Attribute, typ)

    data = list(load_csv(args.source_csv))
    validate_csv(data)

    logger.info(u"Updating values for Attribute '{}' ({}) on {} {} ...".format(Attribute.name, Attribute.uid, len(data), typ))
    for i in range(3, 0, -1):
        time.sleep(i)
        print('Proceeding in {}...'.format(i))

    for i, obj in enumerate(data, 1):
        obj_uid = obj['uid']
        attribute_value = obj['attributeValue']

        obj_old = api.get('{}/{}'.format(args.object_type, obj_uid), params={'fields': ':owner'}).json()
        obj_updated = create_or_update_attribute_values(obj_old, Attribute.uid, attribute_value)

        api.put('{}/{}'.format(typ, obj_uid), data=obj_updated)
        logger.info(u"{}/{} - Updated AttributeValue: {} - {}: {}".format(i, len(data), attribute_value, typ[:-1], obj_uid))