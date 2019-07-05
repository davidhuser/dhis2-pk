#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import re
import getpass

from colorama import Style
from dhis2 import setup_logger, logger, RequestException

try:
    from pk.common.utils import create_api, file_timestamp, write_csv
    from pk.common.exceptions import PKClientException
except (SystemError, ImportError):
    from common.utils import create_api, file_timestamp, write_csv
    from common.exceptions import PKClientException


def parse_args():
    description = "{}Analyze data integrity.{}".format(Style.BRIGHT, Style.RESET_ALL)
    usage = "\n{}Example:{} dhis2-pk-data-integrity -s play.dhis2.org/demo -u admin -p district".format(
        Style.BRIGHT, Style.RESET_ALL)

    parser = argparse.ArgumentParser(usage=usage, description=description)
    parser.add_argument('-s', dest='server', action='store',
                        help="DHIS2 server URL")
    parser.add_argument('-u', dest='username', action='store', help="DHIS2 username")
    parser.add_argument('-p', dest='password', action='store', help="DHIS2 password")
    parser.add_argument('-v', dest='api_version', action='store', required=False, type=int,
                        help='DHIS2 API version e.g. -v=28')
    args = parser.parse_args()

    if not args.password:
        if not args.username:
            raise PKClientException("ArgumentError: Must provide a username via argument -u")
        password = getpass.getpass(prompt="Password for {} @ {}: ".format(args.username, args.server))
    else:
        password = args.password
    return args, password


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
    option_sets = api.get('optionSets', params={'fields': 'id,name,options', 'paging': False}).json()

    logger.info("*** CHECKING {} OPTION SETS... ***".format(len(option_sets['optionSets'])))

    [
        logger.warn("Option Set '{}' ({}) has no options".format(o['name'], o['id']))
        for o in option_sets['optionSets']
        if not o.get('options')
    ]

    for option_set in option_sets['optionSets']:
        data_elements_with_optionset = api.get('dataElements', params={
            'fields': 'id,name',
            'filter': 'optionSet.id:eq:{}'.format(option_set['id'])
        }).json()['dataElements']

        tea_with_optionset = api.get('trackedEntityAttributes', params={
            'fields': 'id,name',
            'filter': 'optionSet.id:eq:{}'.format(option_set['id'])
        }).json()['trackedEntityAttributes']

        attributes_with_optionset = api.get('attributes', params={
            'fields': 'id,name',
            'filter': 'optionSet.id:eq:{}'.format(option_set['id'])
        }).json()['attributes']

        if not any([data_elements_with_optionset, tea_with_optionset, attributes_with_optionset]):
            logger.warn("Option Set '{}' ({}) is not assigned "
                        "to any Data Element, Tracked Entity Attribute or Attribute".format(option_set['name'],
                                                                                            option_set['id']))


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


def main():
    setup_logger(include_caller=False)
    args, password = parse_args()

    api = create_api(server=args.server, username=args.username, password=password)

    check_validation_rules(api)
    check_option_sets(api)
    check_category_options(api)
    check_categories(api)
    check_category_combos(api)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warn("Aborted.")
    except PKClientException as e:
        logger.error(e)
    except Exception as e:
        logger.exception(e)
