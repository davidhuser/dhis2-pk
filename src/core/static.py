from copy import deepcopy
import re

shareable = {
    'userGroups': ['usergroups', 'ug', 'usergroup'],
    'userRoles': ['userroles', 'ur', 'userrole'],
    'sqlViews': ['sqlviews', 'sqlview'],
    'constants': ['constants', 'constant'],
    'optionSets': ['optionsets', 'optionset', 'os'],
    'optionGroups': ['optiongroups', 'optiongroup'],
    'optionGroupSets': ['optiongroupsets', 'optiongroupset'],
    'legendSets': ['legendsets', 'legendset'],
    'organisationUnitGroups': ['organisationunitgroups', 'oug', 'orgunitgroups', 'ougroups', 'orgunitgroup', 'ougroup'],
    'organisationUnitGroupSets': ['organisationunitgroupsets', 'ougs', 'orgunitgroupsets', 'ougroupsets',
                                  'orgunitgroupset', 'ougroupset'],
    'categoryOptions': ['categoryoptions', 'catoptions', 'catoption', 'categoryoption', 'dataelementcategoryoption'],
    'categoryOptionGroups': ['categoryoptiongroups', 'catoptiongroups', 'catoptiongroup', 'categoryoptiongroup'],
    'categoryOptionGroupSets': ['categoryoptiongroupsets', 'catoptiongroupsets', 'catoptiongroupset',
                                'categoryoptiongroupset'],
    'categories': ['categories', 'cat', 'cats' 'category', 'dataelementcategory', 'dataelementcategories'],
    'categoryCombos': ['categorycombos', 'catcombos', 'catcombo', 'categorycombo', 'categorycombination',
                       'categorycombinations'],
    'dataElements': ['dataelements', 'de', 'des', 'dataelement'],
    'dataElementGroups': ['dataelementgroups', 'deg', 'degroups', 'degroup', 'dataelementgroup'],
    'dataElementGroupSets': ['dataelementgroupsets', 'degs', 'degroupsets', 'degroupset', 'dataelementgroupset'],
    'indicators': ['indicators', 'i', 'ind', 'indicator'],
    'indicatorGroups': ['indicatorgroups', 'ig', 'indgroups', 'indicatorgroup'],
    'indicatorGroupSets': ['indicatorgroupsets', 'igs', 'indgroupsets', 'indicatorgroupset'],
    'dataSets': ['datasets', 'ds', 'dataset'],
    'dataApprovalLevels': ['dataapprovallevels', 'datasetapprovallevel'],
    'validationRuleGroups': ['validationrulegroups', 'validationrulegroup'],
    'interpretations': ['interpretations', 'interpretation'],
    'trackedEntityAttributes': ['trackedentityattributes', 'trackedentityattribute', 'tea', 'teas'],
    'programs': ['programs', 'program'],
    'eventCharts': ['eventcharts', 'eventchart'],
    'eventReports': ['eventreports', 'eventtables', 'eventreport'],
    'programIndicators': ['programindicators', 'pi', 'programindicator'],
    'maps': ['maps', 'map'],
    'documents': ['documents', 'document'],
    'reports': ['reports', 'report'],
    'charts': ['charts', 'chart', 'datavisualization', 'datavisualizations', 'datavizualisation', 'datavizualisations'],
    'reportTables': ['pivottable', 'pivottables', 'reporttables', 'reporttable'],
    'dashboards': ['dashboards', 'dashboard']
}


def shareable_object_types():
    """Reverse dictionary from  key:list  to  each_listitem: key and sort it"""
    return dict((v, k) for k in shareable for v in shareable[k])


def all_object_types():
    """Reverse dictionary from  key:list  to  each_listitem: key and sort it"""
    all_objects = deepcopy(shareable)
    all_objects['organisationUnits'] = ['ou', 'orgunit', 'orgunits']
    all_objects['validationRules'] = ['validationrules', 'validationrule']
    return dict((v, k) for k in all_objects for v in all_objects[k])


def valid_uid(uid):
    """Check if string matches DHIS2 UID pattern"""
    return re.compile("[A-Za-z][A-Za-z0-9]{10}").match(uid)

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
