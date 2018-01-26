import re

newest_dhis = 29


def valid_uid(uid):
    """Check if string matches DHIS2 UID pattern"""
    return re.compile("[A-Za-z][A-Za-z0-9]{10}").match(uid) is not None


properties_to_remove = {
    'created',
    'user',
    'lastUpdated',
    'publicAccess',
    'userGroupAccesses',
    'userAccesses',
    'href',
    'url',
    'uuid'
}

csv_import_objects = {
    'dataElements',
    'dataElementGroups',
    'categoryOptions',
    'categoryOptionGroups',
    'organisationUnits',
    'organisationUnitGroups',
    'validationRules',
    'translations',
    'optionSets'
}
