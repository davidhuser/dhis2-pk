#!/usr/bin/env python

"""
indicator-definitions
~~~~~~~~~~~~~~~~~
Creates a CSV with indicator definitions (names of dataelement.catoptioncombo, constants, orgunitgroups)
"""

import argparse

import unicodecsv as csv
from logzero import logger
try:
    from pk.core import log
    from pk.core import dhis
    from pk.core import exceptions
except ImportError:
    from core import log
    from core import dhis
    from core import exceptions


def replace_definitions(definition, obj_map):
    """replace numerator/denominators with readable objects"""
    for i, j in obj_map.items():
        definition = definition.replace(i, obj_map[i]['desc'])
    return definition


def object_map(api):
    """get all relevant objects from the server and put it in a single dictionary"""
    uid_mapping = {}

    params1 = {'paging': False}
    resp1 = api.get(endpoint='indicatorTypes', file_type='json', params=params1)
    for elem in resp1['indicatorTypes']:
        uid_mapping[elem['id']] = {'desc': u"{}".format(elem['displayName'])}

    params2 = {'fields': 'id,name,value', 'paging': False}
    resp2 = api.get(endpoint='constants', file_type='json', params=params2)
    for elem in resp2['constants']:
        uid_mapping[elem['id']] = {'desc': u"[Name: {} - Value: {}]".format(elem['name'], elem['value'])}

    params3 = {'fields': 'id,name,organisationUnits', 'paging': False}
    resp3 = api.get(endpoint='organisationUnitGroups', file_type='json', params=params3)
    for elem in resp3['organisationUnitGroups']:
        uid_mapping[elem['id']] = {
            'desc': u"[Name: {} - OUG Size: {}]".format(elem['name'], len(elem['organisationUnits']))}

    params4 = {'fields': 'id,name', 'paging': False}
    resp4 = api.get(endpoint='dataElements', file_type='json', params=params4)
    for elem in resp4['dataElements']:
        uid_mapping[elem['id']] = {'desc': u"{}".format(elem['name'])}

    params5 = {'fields': 'id,name', 'paging': False}
    resp5 = api.get(endpoint='categoryOptionCombos', file_type='json', params=params5)
    for elem in resp5['categoryOptionCombos']:
        uid_mapping[elem['id']] = {'desc': u"{}".format(elem['name'])}

    params6 = {'fields': 'id,name', 'paging': False}
    resp6 = api.get(endpoint='programs', file_type='json', params=params6)
    for elem in resp6['programs']:
        uid_mapping[elem['id']] = {'desc': u"{}".format(elem['name'])}

    params7 = {'fields': 'id,name', 'paging': False}
    resp7 = api.get(endpoint='programIndicators', file_type='json', params=params7)
    for elem in resp7['programIndicators']:
        uid_mapping[elem['id']] = {'desc': u"{}".format(elem['name'])}

    params8 = {'fields': 'id,name', 'paging': False}
    resp8 = api.get(endpoint='trackedEntityAttributes', file_type='json', params=params8)
    for elem in resp8['trackedEntityAttributes']:
        uid_mapping[elem['id']] = {'desc': u"{}".format(elem['name'])}

    return uid_mapping


def parse_args():
    parser = argparse.ArgumentParser(description="Create CSV with indicator definitions/expressions")
    parser.add_argument('-s', dest='server', action='store',
                        help="DHIS2 server URL without /api/, e.g. -s='play.dhis2.org/demo'")
    parser.add_argument('-f', dest='indicator_filter', action='store',
                        help="Indicator filter, e.g. -f='name:^like:HIV'", required=False)
    parser.add_argument('-u', dest='username', action='store', help="DHIS2 username")
    parser.add_argument('-p', dest='password', action='store', help="DHIS2 password")
    parser.add_argument('-v', dest='api_version', action='store', required=False, type=int,
                        help='DHIS2 API version e.g. -v=24')
    parser.add_argument('-d', dest='debug', action='store_true', default=False, required=False,
                        help="Debug flag - writes more info to log file")
    return parser.parse_args()


def get_params(argument_filter):
    fields = 'id,name,shortName,description,denominatorDescription,numeratorDescription,numerator,denominator,' \
             'annualized,decimals,indicatorType'
    params = {
        'paging': False,
        'fields': fields
    }
    if argument_filter:
        params['filter'] = argument_filter
    return params


def analyze_result(indicators, indicator_filter):
    no_of_indicators = len(indicators['indicators'])
    if no_of_indicators == 0:
        if indicator_filter:
            msg = "No indicators found - check your filter."
        else:
            msg = "No indicators found - are there any?"
        raise exceptions.ClientException(msg)
    else:
        if indicator_filter:
            msg = "Found {} indicators with filter {}".format(no_of_indicators, indicator_filter)
        else:
            msg = "Found {} indicators".format(no_of_indicators)
    return msg


def write_to_csv(indicators, object_mapping, file_name):
    with open(file_name, 'wb') as csvfile:
        writer = csv.writer(csvfile, encoding='utf-8', delimiter=',', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(
            ['uid', 'name', 'shortName', 'numerator', 'numeratorDescription', 'denominator', 'denominatorDescription',
             'annualized', 'indicatorType', 'decimals'])

        for ind in indicators['indicators']:
            num = replace_definitions(ind['numerator'], object_mapping)
            den = replace_definitions(ind['denominator'], object_mapping)
            logger.debug(u"Replaced numerators: {}".format(num))
            logger.debug(u"Replaced denominators: {}".format(den))

            uid = ind['id']
            name = ind['name']
            shortname = ind['shortName']
            num_desc = ind.get('numeratorDescription', None)
            den_desc = ind.get('denominatorDescription', None)
            annualized = str(ind.get('annualized', 'False')).decode('utf-8')
            ind_type_desc = object_mapping[ind['indicatorType']['id']].get('desc')
            decimals = ind.get('decimals', u'default')

            row = [uid, name, shortname, num, num_desc, den, den_desc, annualized, ind_type_desc, decimals]

            # convert all elements in row to unicode before writing it to csv
            for elem in row:
                if type(elem) in {unicode, str}:
                    elem = elem.encode('utf-8')
                elif type(elem) is bool:
                    elem = str(elem)
            writer.writerow(row)

        logger.info("Success! CSV file exported to {}".format(file_name))


def main():
    args = parse_args()

    api = dhis.Dhis(server=args.server, username=args.username, password=args.password, api_version=args.api_version)
    log.init(args.debug)

    indicators = api.get(endpoint='indicators', file_type='json', params=get_params(args.indicator_filter))

    message = analyze_result(indicators, args.indicator_filter)
    logger.info(message)
    logger.info("Downloading other UIDs <-> Names...")
    object_mapping = object_map(api)
    file_name = 'indicators-{}.csv'.format(api.file_timestamp)
    write_to_csv(indicators, object_mapping, file_name)


if __name__ == "__main__":
    main()
