#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
indicator-definitions
~~~~~~~~~~~~~~~~~
Creates a CSV with indicator definitions (names of dataelement.catoptioncombo, constants, orgunitgroups)
"""

import argparse
import getpass
from collections import namedtuple, OrderedDict

from colorama import Style
from dhis2 import setup_logger, logger

try:
    from pk.common.utils import create_api, write_csv, file_timestamp
    from pk.common.exceptions import PKClientException
except (SystemError, ImportError):
    from common.utils import create_api, write_csv, file_timestamp
    from common.exceptions import PKClientException



indicator_fields = OrderedDict([
    ('type', 'indicator'),
    ('uid', 'id'),
    ('name', 'name'),
    ('short_name', 'shortName'),
    ('numerator', 'numerator'),
    ('numerator_description', 'numeratorDescription'),
    ('denominator', 'denominator'),
    ('denominator_description', 'denominatorDescription'),
    ('annualized', 'annualized'),
    ('indicator_type', 'indicatorType'),
    ('decimals', 'decimals'),
    ('last_updated', 'lastUpdated'),
    ('numerator_valid', 'numeratorValid'),
    ('denominator_valid', 'denominatorValid')
])

Indicator = namedtuple('Indicator', ' '.join(indicator_fields.keys()))

program_indicator_fields = OrderedDict([
    ('type', 'programIndicator'),
    ('uid', 'id'),
    ('name', 'name'),
    ('short_name', 'shortName'),
    ('expression', 'expression'),
    ('filter', 'filter'),
    ('aggregation_type', 'aggregationType'),
    ('analytics_type', 'analyticsType'),
    ('program', 'program[id,name]'),
    ('program_name', 'program'),
    ('last_updated', 'lastUpdated'),
    ('expression_valid', 'expressionValid'),
    ('filter_valid', 'filter_valid')
])
ProgramIndicator = namedtuple('ProgramIndicator', ' '.join(program_indicator_fields.keys()))


def replace_definitions(definition, obj_map):
    """replace numerator/denominators with readable objects"""
    for i, j in obj_map.items():
        definition = definition.replace(i, u'{}'.format(obj_map[i]['desc']))
    return definition


def object_map(api):
    """get all relevant objects from the server and put it in a single dictionary"""
    uid_mapping = {}
    params1 = {'paging': False}
    resp1 = api.get(endpoint='indicatorTypes', params=params1).json()
    for elem in resp1['indicatorTypes']:
        uid_mapping[elem['id']] = {u'desc': u"{}".format(elem['displayName'])}

    params2 = {'fields': 'id,name,value', 'paging': False}
    resp2 = api.get(endpoint='constants', params=params2).json()
    for elem in resp2['constants']:
        uid_mapping[elem['id']] = {u'desc': u"[Name: {} - Value: {}]".format(elem['name'], elem['value'])}

    params3 = {'fields': 'id,name,organisationUnits', 'paging': False}
    resp3 = api.get(endpoint='organisationUnitGroups', params=params3).json()
    for elem in resp3['organisationUnitGroups']:
        uid_mapping[elem['id']] = {
            u'desc': u"[Name: {} - OUG Size: {}]".format(elem['name'], len(elem['organisationUnits']))}

    params4 = {'fields': 'id,name', 'paging': False}
    resp4 = api.get(endpoint='dataElements', params=params4).json()
    for elem in resp4['dataElements']:
        uid_mapping[elem['id']] = {u'desc': u"{}".format(elem['name'])}

    params5 = {'fields': 'id,name', 'paging': False}
    resp5 = api.get(endpoint='categoryOptionCombos', params=params5).json()
    for elem in resp5['categoryOptionCombos']:
        uid_mapping[elem['id']] = {u'desc': u"{}".format(elem['name'])}

    params6 = {'fields': 'id,name', 'paging': False}
    resp6 = api.get(endpoint='programs', params=params6).json()
    for elem in resp6['programs']:
        uid_mapping[elem['id']] = {u'desc': u"{}".format(elem['name'])}

    params7 = {'fields': 'id,name', 'paging': False}
    resp7 = api.get(endpoint='programIndicators', params=params7).json()
    for elem in resp7['programIndicators']:
        uid_mapping[elem['id']] = {u'desc': u"{}".format(elem['name'])}

    params8 = {'fields': 'id,name', 'paging': False}
    resp8 = api.get(endpoint='trackedEntityAttributes', params=params8).json()
    for elem in resp8['trackedEntityAttributes']:
        uid_mapping[elem['id']] = {u'desc': u"{}".format(elem['name'])}

    params9 = {'fields': 'id,name', 'paging': False}
    resp9 = api.get(endpoint='programStages', params=params9).json()
    for elem in resp9['programStages']:
        uid_mapping[elem['id']] = {u'desc': u"{}".format(elem['name'])}

    return uid_mapping


def parse_args():
    description = "{}Readable indicator definition to CSV.{}".format(Style.BRIGHT, Style.RESET_ALL)
    usage = "\n{}Example:{} dhis2-pk-indicator-definitions -s play.dhis2.org/demo -u admin -p district -t indicators".format(Style.BRIGHT, Style.RESET_ALL)

    types = {'programIndicators', 'indicators'}
    parser = argparse.ArgumentParser(usage=usage, description=description)
    parser._action_groups.pop()

    required = parser.add_argument_group('required arguments')
    required.add_argument('-t',
                          dest='indicator_type',
                          action='store',
                          metavar='INDICATOR_TYPE',
                          help="{}".format(" or ".join(types)),
                          choices=types,
                          required=True)

    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('-s',
                          dest='server',
                          action='store',
                          help="DHIS2 server URL")
    optional.add_argument('-f',
                          dest='indicator_filter',
                          action='store',
                          help="Indicator filter, e.g. -f 'name:like:HIV' - see dhis2-pk-share --help")
    optional.add_argument('-u',
                          dest='username',
                          action='store',
                          help="DHIS2 username")
    optional.add_argument('-p',
                          dest='password',
                          action='store',
                          help="DHIS2 password")
    optional.add_argument('-v',
                          dest='api_version',
                          action='store',
                          type=int,
                          help='DHIS2 API version e.g. -v=28')
    args = parser.parse_args()
    if not args.password:
        if not args.username:
            raise PKClientException("ArgumentError: Must provide a username via argument -u")
        password = getpass.getpass(prompt="Password for {} @ {}: ".format(args.username, args.server))
    else:
        password = args.password
    return args, password


def get_params(argument_filter, fields):
    params = {
        'paging': False,
        'fields': fields
    }
    if argument_filter:
        params['filter'] = argument_filter
    return params


def analyze_result(typ, indicators, indicator_filter):
    """Check response from API"""
    no_of_indicators = len(indicators[typ])
    if no_of_indicators == 0:
        if indicator_filter:
            msg = "check your filter."
        else:
            msg = "are there any?"
        raise SystemExit("No {} found - {}".format(typ, msg))
    else:
        if indicator_filter:
            msg = "Found {} {} with filter {}".format(no_of_indicators, typ, indicator_filter)
        else:
            msg = "Found {} {}".format(no_of_indicators, typ)
    return msg


def validate_expression(api, expression):
    r = api.session.post('{}/programIndicators/expression/description'.format(api.api_url), data=expression)
    return r.json()['message']

def validate_filter(api, filter):
    r = api.session.post('{}/programIndicators/filter/description'.format(api.api_url), data=filter)
    return r.json()['message']

def validate_nominator_denominator(api, expr):
    r = api.get('expressions/description', params={'expression': expr})
    return r.json()['message']

def format_indicator(api, typ, data, object_mapping):
    if typ == 'indicators':
        for ind in data[typ]:
            Indicator.type = typ
            Indicator.uid = u'{}'.format(ind['id'])
            Indicator.name = u'{}'.format(ind['name'])
            Indicator.short_name = u'{}'.format(ind['shortName'])
            Indicator.numerator = replace_definitions(ind['numerator'], object_mapping)
            Indicator.numerator_description = u'{}'.format(ind.get('numeratorDescription'))
            Indicator.denominator = replace_definitions(ind['denominator'], object_mapping)
            Indicator.denominator_description = u'{}'.format(ind.get('denominatorDescription'))
            Indicator.annualized = u'{}'.format(ind.get('annualized', False))
            Indicator.indicator_type = u'{}'.format(object_mapping[ind['indicatorType']['id']].get('desc'))
            Indicator.decimals = u'{}'.format(ind.get('decimals', 'default'))
            Indicator.last_updated = u'{}'.format(ind['lastUpdated'])
            Indicator.numerator_valid = validate_nominator_denominator(api, ind['numerator'])
            Indicator.denominator_valid = validate_nominator_denominator(api, ind['denominator'])
            yield Indicator

    elif typ == 'programIndicators':
        for ind in data[typ]:
            ProgramIndicator.type = typ
            ProgramIndicator.uid = u'{}'.format(ind['id'])
            ProgramIndicator.name = u'{}'.format(ind['name'])
            ProgramIndicator.short_name = u'{}'.format(ind['shortName'])
            ProgramIndicator.expression = replace_definitions(ind['expression'], object_mapping)
            ProgramIndicator.filter = replace_definitions(ind['filter'], object_mapping) if ind.get(
                'filter') else 'no-filter'
            ProgramIndicator.aggregation_type = u'{}'.format(ind['aggregationType'])
            ProgramIndicator.analytics_type = u'{}'.format(ind['analyticsType'])
            ProgramIndicator.program = u'{}'.format(ind['program']['id'])
            ProgramIndicator.program_name = u'{}'.format(ind['program']['name'])
            ProgramIndicator.last_updated = u'{}'.format(ind['lastUpdated'])
            ProgramIndicator.expression_valid = validate_expression(api, ind['expression'])
            if ind.get('filter'):
                ProgramIndicator.filter_valid = validate_filter(api, ind['filter'])
            else:
                ProgramIndicator.filter_valid = 'no-filter'
            yield ProgramIndicator


def write_to_csv(api, typ, indicators, object_mapping, file_name):
    data = []
    if typ == 'indicators':
        header_row = indicator_fields.keys()

        for indicator in format_indicator(api, typ, indicators, object_mapping):
            data.append([
                indicator.type,
                indicator.uid,
                indicator.name,
                indicator.short_name,
                indicator.numerator,
                indicator.numerator_description,
                indicator.denominator,
                indicator.denominator_description,
                indicator.annualized,
                indicator.indicator_type,
                indicator.decimals,
                indicator.last_updated,
                indicator.numerator_valid,
                indicator.denominator_valid
            ])

        write_csv(data, file_name, header_row)
        logger.info("Success! CSV file exported to {}".format(file_name))

    elif typ == 'programIndicators':
        header_row = program_indicator_fields.keys()

        for program_indicator in format_indicator(api, typ, indicators, object_mapping):
            data.append([
                program_indicator.type,
                program_indicator.uid,
                program_indicator.name,
                program_indicator.short_name,
                program_indicator.expression,
                program_indicator.filter,
                program_indicator.aggregation_type,
                program_indicator.analytics_type,
                program_indicator.program,
                program_indicator.program_name,
                program_indicator.last_updated,
                program_indicator.filter_valid,
                program_indicator.expression_valid
            ])

        write_csv(data, file_name, header_row)
        logger.info("Success! CSV file exported to {}".format(file_name))


def main():
    setup_logger(include_caller=False)
    args, password = parse_args()

    api = create_api(server=args.server, username=args.username, password=password, api_version=args.api_version)

    file_name = '{}-{}.csv'.format(args.indicator_type, file_timestamp(api.api_url))

    if args.indicator_type == 'indicators':
        fields = ','.join([x for x in indicator_fields.values() if x != 'type'])

    elif args.indicator_type == 'programIndicators':
        fields = ','.join([x for x in program_indicator_fields.values() if x not in ('type', 'program_name')])

    else:
        raise SystemExit('Cannot process argument -t {}'.format(args.indicator_type))

    indicators = api.get(endpoint=args.indicator_type, params=get_params(args.indicator_filter, fields)).json()
    message = analyze_result(args.indicator_type, indicators, args.indicator_filter)
    logger.info(message)

    logger.info("Analyzing metadata...")
    object_mapping = object_map(api)

    write_to_csv(api, args.indicator_type, indicators, object_mapping, file_name)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warn("Aborted.")
    except PKClientException as e:
        logger.error(e)
    except Exception as e:
        logger.exception(e)
