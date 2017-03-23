# dhis2-pocket-knife

Command-line tools to interact with [DHIS2](https://dhis2.org) REST API in bulk, e.g. mass sharing of objects with userGroups

## Installation

* [pip](https://pip.pypa.io/en/stable/installing) (python package manager) must be installed
* `pip install dhis2-pocket-knife`

## Usage
* Get help on using arguments, e.g.`dhis2-pk-share-objects --help`
* Be sure the specified user has the authorities to run these tasks for the specified DHIS2 server.
* Logs to a file: `dhis2-pk.log`

---

## Mass sharing of objects with userGroups through filtering

**Script name:** `dhis2-pk-share-objects`

Apply [sharing](https://docs.dhis2.org/master/en/user/html/dhis2_user_manual_en_full.html#sharing) for DHIS2 metadata objects (dataElements, indicators, programs, ...) based on **[metadata object filtering](https://dhis2.github.io/dhis2-docs/master/en/developer/html/dhis2_developer_manual_full.html#webapi_metadata_object_filter)** (for both shareable objects and userGroups).

```
dhis2-pk-share-objects --help
usage: dhis2-pk-share-objects [-h] -s -t -f [-w] [-r] -a [-v] -u -p [-d]

PURPOSE: Share DHIS2 objects (dataElements, programs, ...) with userGroups

arguments:
  -h, --help            show this help message and exit
  
  -s SERVER             DHIS2 server URL, e.g. -s='play.dhis2.org/demo'
  
  -t {see shareable types below in this README}
                        DHIS2 object type to apply sharing, e.g. -t=sqlViews
                        
  -f FILTER             Filter on objects with DHIS2 field filter, e.g.
                        -f='name:like:ABC'
                        
  -w USERGROUP_READWRITE
                        UserGroup filter for Read-Write access, concat. with
                        '&', e.g. -w='name:$ilike:UG1&id:!eq:aBc123XyZ0u'
                        
  -r USERGROUP_READONLY
                        UserGroup filter for Read-Only access, concat. with
                        '&', e.g. -r='id:eq:aBc123XyZ0u'
                        
  -a {readwrite,none,readonly}
                        publicAccess (with login), e.g. -a=readwrite
                        
  -v API_VERSION        DHIS2 API version e.g. -v=24
                        (if omitted, <URL>/api/endpoint will be used)
  -u USERNAME           DHIS2 username, e.g. -u=admin
  -p PASSWORD           DHIS2 password, e.g. -p=district
  -d                    Debug flag - writes more info to log file

```

### Shareable objects:
- userGroups
- sqlViews
- constants
- optionSets
- optionGroups
- optionGroupSets
- legendSets
- organisationUnitGroups
- organisationUnitGroupSets
- categoryOptions
- categoryOptionGroups
- categoryOptionGroupSets
- categories
- categoryCombos
- dataElements
- dataElementGroups
- dataElementGroupSets
- indicators
- indicatorGroups
- indicatorGroupSets
- dataSets
- dataApprovalLevels
- validationRuleGroups
- interpretations
- trackedEntityAttributes
- programs
- eventCharts
- eventReports
- programIndicators
- maps
- documents
- reports
- charts
- reportTables
- dashboards

### Example (try it out against DHIS2 demo instance):

```
dhis2-pk-share-objects -s=play.dhis2.org/demo -t=dataElements -f='name:^like:All&name:!like:cough' -w='name:like:Africare HQ' -r='name:like:Bo District' -a=readwrite -u=admin -p=district -v=24 -d
```

## Export indicator definition (numerators/denominators) to a CSV file

**Script name:** `dhis-pk-indicator-definition`

Writes indicator definition in a readable format to a **csv file**. Includes names and number of orgunits for orgunit groups, dataelements (dataelement.categoryoptioncombo) or (program.dataelement) and constants. Possible to filter indiators with an object filter (see `dhis2-pk-share-objects` for details)

Example column for numerator `ReUHfIn0pTQ - ANC 1-3 Dropout Rate`:
```
#{ANC 1st visit.Fixed}+#{ANC 1st visit.Outreach}-#{ANC 3rd visit.Fixed}-#{ANC 3rd visit.Outreach}
```

```
dhis2-pk-indicator-definitions --help
usage: dhis2-pk-indicator-definitions [-h] -s [-f] -u -p [-v] [-d]

Create CSV with indicator definitions

optional arguments:
  -h, --help           show this help message and exit
  -s SERVER            Server, e.g. play.dhis2.org/demo
  -f INDICATOR_FILTER  Indicator filter
  -u USERNAME          DHIS2 username
  -p PASSWORD          DHIS2 password
  -v API_VERSION       DHIS2 API version e.g. -v=24
  -d                   Debug flag - writes more info to log file, e.g. -d
```

### Example (try it out against DHIS2 demo instance):
```
dhis2-pk-indicator-definitions -s=play.dhis2.org/demo -u=admin -p=district
```

## Find users with a misconfigured Organisation Unit assignment

**Script name:** `dhis2-pk-user-orgunits`

Writes all users of an Organisation Unit who are configured like below to a **csv file**. Users who are assigned both an Orgunit **and** sub-Orgunit can be a source of access errors.
![issue](https://i.imgur.com/MXiALrL.png)

```
dhis2-pk-user-orgunits --help
usage: dhis2-pk-user-orgunits [-h] -s -o -u -p [-v] [-d]

Create CSV all users of an orgunit who also have sub-orgunits assigned

optional arguments:
  -h, --help      show this help message and exit
  -s SERVER       Server, e.g. play.dhis2.org/demo
  -o ORGUNIT      Top-level orgunit UID to check its users
  -u USERNAME     DHIS2 username
  -p PASSWORD     DHIS2 password
  -v API_VERSION  DHIS2 API version e.g. -v=24
  -d              Writes more info in log file
```

### Example (try it out against DHIS2 demo instance):
```
dhis2-pk-user-orgunits --server=play.dhis2.org/demo --orgunit=O6uvpzGd5pu --username=admin --password=district
```



### done

- ~~debug flag as optional argument~~
- ~~arguments: userGroups: multiple filters for userGroups~~
- ~~API version (optional argument)~~
- ~~better help text for sharing `-h`~~

### todo
- better handling of `&` in filters

---
PyPI link: https://pypi.python.org/pypi/dhis2-pocket-knife
