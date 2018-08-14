Attribute setter
------------------

Set custom attributes for many objects sourced from a CSV.

Script name: *dhis2-pk-attribute-setter*

A CSV could look like this:

::

    key,value
    UID1, myNewValue
    UID2, anotherValue

Or, as viewed from Excel:

::

    key     | value
    --------|--------
    UID1    | myNewValue
    UID2    | anotherValue

With *one* call of the script, it's only possible to set an attribute (``-a`` sets the UID) for one object type (``-t``, sets the object type) - but for many objects.

*Note:* It **does** update the existing value if it already exists.

Usage
^^^^^^

::

    usage: dhis2-pk-attribute-setter [-s] [-u] [-p] -c -t -a

    Example:
    dhis2-pk-attribute-setter -s=play.dhis2.org -u=admin -p=district -c=file.csv -t=organisationUnits -a=pt5Ll9bb2oP

    CSV file structure:
    key     | value
    --------|--------
    UID     | myValue


    Post Attribute Values sourced from CSV file

    optional arguments:
      -h, --help            show this help message and exit
      -s SERVER             DHIS2 server URL without /api/ e.g.
                            -s=play.dhis2.org/demo
      -c SOURCE_CSV         CSV file with Attribute values
      -t {programIndicators,optionSets,options,sections,categoryOptionGroupSets,organisationUnitGroups,trackedEntityTypes,categories,organisationUnits,categoryOptions,trackedEntityAttributes,trackedEntities,programStages,dataElementGroupSets,userGroups,dataElementGroups,validationRuleGroups,organisationUnitGroupSets,documents,legendSets,constants,users,sqlViews,dataElements,dataSets,legends,indicators,validationRules,programs,indicatorGroups,categoryOptionGroups,categoryOptionCombos}
                            DHIS2 object type to set attribute values
      -a ATTRIBUTE_UID      Attribute UID
      -u USERNAME           DHIS2 username
      -p PASSWORD           DHIS2 password
      -d                    Writes more info in log file

