#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re

from dhis2 import setup_logger, logger, RequestException

try:
    from src.common.utils import create_api, file_timestamp, write_csv
    from src.common.exceptions import PKClientException
except (SystemError, ImportError):
    from common.utils import create_api, file_timestamp, write_csv
    from common.exceptions import PKClientException


def extract_uids(rule):
    expressions = rule['leftSide']['expression'] + rule['rightSide']['expression']
    list_of_uids = re.findall(r'[A-Za-z][A-Za-z0-9]{10}', expressions)
    if not list_of_uids:
        logger.warn('Expression without UIDs. Check rule {}'.format(json.dumps(rule)))
    return list_of_uids


def check_validation_rules(api):
    p = {'fields': 'id,name,description,leftSide[expression],rightSide[expression]', 'paging': False}
    data = api.get('validationRules', params=p).json()

    logger.info("*** CHECKING {} VALIDATION RULES... ***".format(len(data['validationRules'])))

    for rule in data['validationRules']:
        uid_cache = set()

        uids_in_expressions = extract_uids(rule)
        for uid in uids_in_expressions:
            if uid not in uid_cache:
                try:
                    api.get('identifiableObjects/{}'.format(uid)).json()
                except RequestException as exc:
                    if exc.code == 404:
                        logger.warn("Validation Rule '{}' ({}) - "
                                    "UID in expression not identified: {}".format(rule['name'], rule['id'], uid))
                        uid_cache.add(uid)
                    else:
                        logger.error(exc)
                else:
                    uid_cache.add(uid)


def check_option_sets(api):
    option_sets = api.get_paged(
        'optionSets',
        params={'fields': 'id,name,options[id,name,code,sortOrder]'},
        merge=True,
        page_size=20
    )

    logger.info("*** CHECKING {} OPTION SETS... ***".format(len(option_sets['optionSets'])))

    if not option_sets.get('optionSets'):
        logger.warn("No Option Sets found.")

    for os in option_sets['optionSets']:
        amount_of_options = len(os.get('options', []))
        if amount_of_options == 0:
            logger.warn("Option Set '{}' ({}) has no options".format(os['name'], os['id']))
        else:
            sort_order_range = [int(option['sortOrder']) for option in os['options']]
            expected = list(range(1, amount_of_options + 1))
            if sort_order_range != expected:
                logger.warn("Option Set '{}' ({}) has non-sequential sort order in its options".format(os['name'], os['id']))

            codes = [option['code'] for option in os['options']]
            if len(codes) != len(set(codes)):
                logger.warn("Option Set '{}' ({}) has duplicate codes in its options")

        data_elements_with_optionset = api.get('dataElements', params={
            'fields': 'id,name',
            'filter': 'optionSet.id:eq:{}'.format(os['id']),
            'paging': 'false'
        }).json()['dataElements']

        tea_with_optionset = api.get('trackedEntityAttributes', params={
            'fields': 'id,name',
            'filter': 'optionSet.id:eq:{}'.format(os['id']),
            'paging': 'false'
        }).json()['trackedEntityAttributes']

        attributes_with_optionset = api.get('attributes', params={
            'fields': 'id,name',
            'filter': 'optionSet.id:eq:{}'.format(os['id']),
            'paging': 'false'
        }).json()['attributes']

        if not any([data_elements_with_optionset, tea_with_optionset, attributes_with_optionset]):
            logger.warn("Option Set '{}' ({}) is not assigned "
                        "to any Data Element, Tracked Entity Attribute or Attribute".format(os['name'], os['id']))


def check_category_options(api):
    category_options = api.get('categoryOptions', params={'fields': 'id,name,categories', 'paging': False}).json()

    logger.info("*** CHECKING {} CATEGORY OPTIONS... ***".format(len(category_options['categoryOptions'])))

    [
        logger.warn("Category Option '{}' ({}) is not in any Category".format(co['name'], co['id']))
        for co in category_options['categoryOptions']
        if not co.get('categories')
    ]


def check_categories(api):
    categories = api.get('categories', params={'fields': 'id,name,categoryCombos', 'paging': False}).json()

    logger.info("*** CHECKING {} CATEGORIES... ***".format(len(categories['categories'])))

    [
        logger.warn("Category '{}' ({}) is not in any Category Combo".format(c['name'], c['id']))
        for c in categories['categories']
        if not c.get('categoryCombos')
    ]


def check_category_combos(api):
    cat_combo = api.get('categoryCombos', params={'fields': 'id,name', 'paging': False}).json()

    logger.info("*** CHECKING {} CATEGORY COMBOS... ***".format(len(cat_combo['categoryCombos'])))

    for cc in cat_combo['categoryCombos']:
        data_elements_with_cc = api.get('dataElements', params={
            'fields': 'id,name',
            'filter': 'categoryCombo.id:eq:{}'.format(cc['id'])
        }).json()['dataElements']

        data_set_elements_with_cc = api.get('dataElements', params={
            'fields': 'id,name',
            'filter': 'dataSetElements.categoryCombo.id:eq:{}'.format(cc['id'])
        }).json()['dataElements']

        programs_with_cc = api.get('programs', params={
            'fields': 'id,name',
            'filter': 'categoryCombo.id:eq:{}'.format(cc['id'])
        }).json()['programs']

        datasets_with_cc = api.get('dataSets', params={
            'fields': 'id,name',
            'filter': 'categoryCombo.id:eq:{}'.format(cc['id'])
        }).json()['dataSets']

        if not any([data_elements_with_cc, data_set_elements_with_cc, programs_with_cc, datasets_with_cc]):
            logger.warn("Category Combo '{}' ({}) is not assigned "
                        "to any Data Element, Data Set Element, Program or Data Set".format(cc['name'], cc['id']))


def main(args, password):
    setup_logger(include_caller=False)

    api = create_api(server=args.server, username=args.username, password=password)

    check_validation_rules(api)
    check_option_sets(api)
    check_category_options(api)
    check_categories(api)
    check_category_combos(api)