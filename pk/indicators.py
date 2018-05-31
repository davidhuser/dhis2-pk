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

    params9 = {'fields': 'id,name', 'paging': False}
    resp9 = api.get(endpoint='programStages', file_type='json', params=params9)
    for elem in resp9['programStages']:
        uid_mapping[elem['id']] = {'desc': u"{}".format(elem['name'])}

    return uid_mapping


def parse_args():
    types = {'programIndicators', 'indicators'}
    parser = argparse.ArgumentParser(description="Create CSV with indicator definitions/expressions")
    parser.add_argument('-s',
                        dest='server',
                        action='store',
                        help="DHIS2 server URL without /api/, e.g. -s='play.dhis2.org/demo'")
    parser.add_argument('-f',
                        dest='indicator_filter',
                        action='store',
                        help="Indicator filter, e.g. -f='name:$like:HIV'",
                        required=False)
    parser.add_argument('-t',
                        dest='indicator_type',
                        action='store',
                        metavar='INDICATOR_TYPE',
                        help="Type of indicator: '{}'".format("' or '".join(types)),
                        choices=types,
                        required=True)
    parser.add_argument('-u',
                        dest='username',
                        action='store',
                        help="DHIS2 username")
    parser.add_argument('-p',
                        dest='password',
                        action='store',
                        help="DHIS2 password")
    parser.add_argument('-v',
                        dest='api_version',
                        action='store',
                        required=False,
                        type=int,
                        help='DHIS2 API version e.g. -v=24')
    parser.add_argument('-d',
                        dest='debug',
                        action='store_true',
                        default=False,
                        required=False,
                        help="Debug flag - writes more info to log file")
    return parser.parse_args()


def get_params(argument_filter, fields):

    params = {
        'paging': False,
        'fields': fields
    }
    if argument_filter:
        params['filter'] = argument_filter
    return params


def analyze_result(typ, indicators, indicator_filter):
    no_of_indicators = len(indicators[typ])
    if no_of_indicators == 0:
        if indicator_filter:
            msg = "No {} found - check your filter.".format(typ)
        else:
            msg = "No {} found - are there any?".format(typ)
        raise exceptions.ClientException(msg)
    else:
        if indicator_filter:
            msg = "Found {} {} with filter {}".format(no_of_indicators, typ, indicator_filter)
        else:
            msg = "Found {} {}".format(no_of_indicators, typ)
    return msg


def utf8ify(row):
    l = []
    for elem in row:
        if type(elem) in {unicode, str}:
            l.append(elem.encode('utf-8'))
        elif type(elem) is bool:
            l.append(str(elem))
    return l


def write_to_csv(typ, indicators, object_mapping, file_name):
    with open(file_name, 'wb') as csvfile:
        if typ == 'indicators':
            header_row = ['type', 'uid', 'name', 'shortName', 'numerator', 'numeratorDescription', 'denominator',
                          'denominatorDescription', 'annualized', 'indicatorType', 'decimals', 'lastUpdated']
            writer = csv.writer(csvfile, encoding='utf-8', delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(header_row)
            for ind in indicators[typ]:
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
                last_updated = ind['lastUpdated']

                row = [typ, uid, name, shortname, num, num_desc, den,
                       den_desc, annualized, ind_type_desc, decimals, last_updated]
                writer.writerow(utf8ify(row))
            logger.info("Success! CSV file exported to {}".format(file_name))

        elif typ == 'programIndicators':
            header_row = ['type', 'uid', 'name', 'shortName', 'expression', 'filter', 'aggregationType',
                          'analyticsType', 'program', 'programName', 'lastUpdated']
            writer = csv.writer(csvfile, encoding='utf-8', delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(header_row)
            for ind in indicators[typ]:
                uid = ind['id']
                name = ind['name']
                shortname = ind['shortName']
                expression = replace_definitions(ind['expression'], object_mapping)
                if ind.get('filter'):
                    filters = replace_definitions(ind['filter'], object_mapping)
                else:
                    filters = 'no filter'
                aggregation_type = ind['aggregationType']
                analytics_type = ind['analyticsType']
                program = ind['program']['id']
                program_name = ind['program']['name']
                last_updated = ind['lastUpdated']
                row = [typ, uid, name, shortname, expression, filters, aggregation_type,
                       analytics_type, program, program_name, last_updated]
                writer.writerow(utf8ify(row))
            logger.info("Success! CSV file exported to {}".format(file_name))

        else:
            raise exceptions.ClientException("cannot process type {}".format(typ))


def main():
    args = parse_args()

    api = dhis.Dhis(server=args.server, username=args.username, password=args.password, api_version=args.api_version)
    log.init(debug=args.debug)

    if args.indicator_type == 'indicators':
        fields = 'id,name,shortName,description,denominatorDescription,numeratorDescription,numerator,denominator,' \
                 'annualized,decimals,indicatorType,lastUpdated'
        indicators = api.get(endpoint='indicators',
                             file_type='json',
                             params=get_params(args.indicator_filter, fields))
        message = analyze_result('indicators', indicators, args.indicator_filter)
        logger.info(message)
        file_name = 'indicators-{}.csv'.format(api.file_timestamp)
        logger.info("Downloading other UIDs <-> Names...")
        object_mapping = object_map(api)
        write_to_csv('indicators', indicators, object_mapping, file_name)

    elif args.indicator_type == 'programIndicators':
        fields = 'id,name,shortName,expression,filter,aggregationType,analyticsType,program[id,name],lastUpdated'
        program_indicators = api.get(endpoint='programIndicators',
                                     file_type='json',
                                     params=get_params(args.indicator_filter, fields))
        message = analyze_result('programIndicators', program_indicators, args.indicator_filter)
        logger.info(message)
        file_name = 'programIndicators-{}.csv'.format(api.file_timestamp)
        logger.info("Downloading other UIDs <-> Names...")
        object_mapping = object_map(api)
        write_to_csv('programIndicators', program_indicators, object_mapping, file_name)


if __name__ == "__main__":
    main()
