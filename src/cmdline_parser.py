#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import textwrap
import getpass
import sys


from dhis2 import is_valid_uid

try:
    from src.common.exceptions import PKClientException
    from .__version__ import __version__ as version
except ModuleNotFoundError:  # for pytest
    from common.exceptions import PKClientException
    from __version__ import __version__ as version


def pk_general_help():
    s = '----------------------------\n' \
        'dhis2-pocket-knife v{}\n' \
        '----------------------------\n' \
        'It is required to select one of these scripts:\n\n' \
        'dhis2-pk attribute-setter --help\n' \
        'dhis2-pk data-integrity --help\n' \
        'dhis2-pk indicator-definitions --help\n' \
        'dhis2-pk post-css --help\n' \
        'dhis2-pk share --help\n' \
        'dhis2-pk userinfo --help\n\n' \
        'More info and docs on the website:\n' \
        'https://github.com/davidhuser/dhis2-pk'.format(version)
    sys.exit(s)


def get_password(args):
    """Set the password or getpass it in a secure way"""
    if not args.password:
        password = getpass.getpass(prompt="Password for {} @ {}: ".format(args.username, args.server))
    else:
        password = args.password
    return args, password


def standard_arguments(parser):
    """Add required and optional arguments common to all scripts"""
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    required.add_argument('-s', dest='server', action='store', required=True, help="DHIS2 server URL")
    required.add_argument('-u', dest='username', action='store', required=True, help='DHIS2 username')
    optional.add_argument('-p', dest='password', action='store', required=False, help='DHIS2 password')
    return required, optional


def parse_args_attributes(argv):
    description = "Set Attribute Values sourced from CSV file."

    usage = """
Example: dhis2-pk attribute-setter -s play.dhis2.org/dev -u admin -p district -c file.csv -t organisationUnits -a pt5Ll9bb2oP

CSV file structure:
uid   | attributeValue
------|---------------
UID   | myValue
"""

    parser = argparse.ArgumentParser(usage=usage, description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)
    required, optional = standard_arguments(parser)

    required.add_argument('-t', dest='object_type', action='store', required=True,
                          help="Object type to set attributeValues to: {organisationUnits, dataElements, ...}")
    required.add_argument('-c', dest='source_csv', action='store', required=True,
                          help="Path to CSV file with Attribute Values")
    required.add_argument('-a', dest='attribute_uid', action='store', help='Attribute UID', required=True)

    args = parser.parse_args(argv)

    obj_types = {
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

    if args.object_type not in obj_types:
        raise PKClientException("argument -t must be a valid object_type - one of:\n{}".format(', '.join(sorted(obj_types))))
    if not is_valid_uid(args.attribute_uid):
        raise PKClientException("Attribute {} is not a valid UID".format(args.attribute_uid))

    return get_password(args)


def parse_args_css(argv):
    description = "Post CSS stylesheet to a server."
    usage = "\nExample: dhis2-pk post-css -s=play.dhis2.org/dev -u=admin -p=district -c=file.css"
    parser = argparse.ArgumentParser(usage=usage, description=description)
    required, optional = standard_arguments(parser)
    required.add_argument('-c', dest='css', action='store', required=True, help="Path to CSS file")
    args = parser.parse_args(argv)
    return get_password(args)


def parse_args_indicators(argv):
    description = "Readable indicator definition to CSV."
    usage = "\nExample: dhis2-pk indicator-definitions -s play.dhis2.org/demo -u admin -p district -t indicators"

    types = {'programIndicators', 'indicators'}
    parser = argparse.ArgumentParser(usage=usage, description=description)
    required, optional = standard_arguments(parser)

    required.add_argument('-t', dest='indicator_type', action='store', metavar='INDICATOR_TYPE',
                        help="{}".format(" or ".join(types)), choices=types, required=True)

    required.add_argument('-f', dest='indicator_filter', action='store',
                        help="Indicator filter, e.g. -f 'name:like:HIV' - see dhis2-pk-share --help", required=False)
    args = parser.parse_args(argv)
    return get_password(args)


def parse_args_integrity(argv):
    description = "Run additional data integrity checks."
    usage = "\nExample: dhis2-pk data-integrity -s play.dhis2.org/demo -u admin -p district"
    parser = argparse.ArgumentParser(usage=usage, description=description)
    standard_arguments(parser)
    args = parser.parse_args(argv)
    return get_password(args)


def parse_args_share(argv):
    """Argument parsing"""
    try:
        from share import access  # imported in function to avoid circular imports
    except ModuleNotFoundError:
        from src.share import access

    description = "Share DHIS2 objects with userGroups via filters."
    usage = """
Example: dhis2-pk share -s play.dhis2.org/dev -u admin -p district -f 'id:eq:P3jJH5Tu5VC' -t dataelement -a readonly -g 'name:like:Admin' readwrite -g 'name:like:Research' readwrite
"""

    parser = argparse.ArgumentParser(usage=usage,
                                     description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)

    required, optional = standard_arguments(parser)

    required.add_argument('-t', dest='object_type', action='store', required=True,
                          help="DHIS2 object type to apply sharing, e.g. -t sqlView")

    optional.add_argument('-a',
                          dest='public_access',
                          action='append',
                          required=False,
                          nargs='+',
                          metavar='PUBLICACCESS',
                          choices=access.keys(),
                          help=textwrap.dedent('''\
                            Public Access for all objects. 
                            Valid choices are: {{{}}}
                            For setting DATA access, add second argument, e.g. -a readwrite readonly
                          '''.format(', '.join(access.keys()))))
    optional.add_argument('-f',
                          dest='filter',
                          action='store',
                          required=False,
                          help=textwrap.dedent('''\
                                Filter on objects with DHIS2 field filter.
                                To add multiple filters:
                                - '&&' joins filters with AND
                                - '||' joins filters with OR
                                Example:  -f 'name:like:ABC||code:eq:X'
                                   '''))
    optional.add_argument('-g',
                          dest='groups',
                          action='append',
                          required=False,
                          metavar='USERGROUP',
                          nargs='+',
                          help=textwrap.dedent('''\
                            User Group to share objects with: FILTER METADATA [DATA]
                            - FILTER: Filter all User Groups. See -f for filtering mechanism
                            - METADATA: Metadata access for this User Group. {readwrite, none, readonly}
                            - DATA: Data access for this User Group. {readwrite, none, readonly}
                            Example:  -g 'id:eq:OeFJOqprom6' readwrite none
                            '''))
    optional.add_argument('-o',
                          dest='overwrite',
                          action='store_true',
                          required=False,
                          default=False,
                          help="Overwrite sharing - updates 'lastUpdated' field of all shared objects")
    optional.add_argument('-e',
                          dest='extend',
                          action='store_true',
                          required=False,
                          default=False,
                          help="Extend existing sharing settings")
    optional.add_argument('-l',
                          dest='logging_to_file',
                          action='store',
                          required=False,
                          metavar='FILEPATH',
                          help="Path to Log file (default level: INFO, pass -d for DEBUG)")
    optional.add_argument('-d',
                          dest='debug',
                          action='store_true',
                          default=False,
                          required=False,
                          help="Debug flag")
    args = parser.parse_args(argv)
    return get_password(args)


def parse_args_userinfo(argv):
    description = "Create CSV of user information."
    usage = "\nExample: dhis2-pk userinfo -s play.dhis2.org/demo -u admin -p district"

    parser = argparse.ArgumentParser(usage=usage, description=description)
    standard_arguments(parser)
    args = parser.parse_args(argv)
    return get_password(args)

