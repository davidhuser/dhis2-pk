# dhis2-pocket-knife [![Version](https://img.shields.io/pypi/v/dhis2-pocket-knife.svg)](https://pypi.python.org/pypi/dhis2-pocket-knife) [![Build Status](https://travis-ci.org/davidhuser/dhis2-pocket-knife.svg?branch=master)](https://travis-ci.org/davidhuser/dhis2-pocket-knife) [![Licence](https://img.shields.io/pypi/l/dhis2-pocket-knife.svg)](https://pypi.python.org/pypi/dhis2-pocket-knife) 


Command-line tools to interact with the RESTful Web API of [DHIS2](https://dhis2.org)

_An example:_
> Share all dataElements starting with `ABC-` with a userGroup called `UG Admin` for read-write access and with a userGroup called `UG Users` for read-only access while public Access is set to `None`:
  
 ```
 dhis2-pk-share-objects -s=play.dhis2.org/demo -t=dataElements -f='name:^like:ABC-' -w='name:like:UG Admin' -r='name:like:UG Users' -a=none -u=admin -p=district
 ```

All tools:

* [Mass sharing of objects with user groups through filtering](#mass-sharing-of-objects-with-usergroups-through-filtering)
* [Export readable indicator definition to CSV](#export-readable-indicator-definition-to-csv)
* [Download metadata to JSON, XML or CSV](#download-metadata-to-json-or-xml-or-csv)
* [Export user info to CSV](#export-user-info-to-csv)
* [Export user-orgunit double assignment](#export-users-with-a-misconfigured-organisation-unit-assignment-to-csv)

## Installation / updating

* Easy installation with [pip](https://pip.pypa.io/en/stable/installing) (python package manager, see if it is installed: `pip -V`)
* `pip install dhis2-pocket-knife` or `sudo -H pip install dhis2-pocket-knife`
* Upgrade with `pip install dhis2-pocket-knife --upgrade`

## Usage

* Get help on using arguments, e.g.`dhis2-pk-share-objects --help`
* In the help text, `[-v]` means an optional argument
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
  
  -s SERVER             DHIS2 server URL without /api/, e.g. -s='play.dhis2.org/demo'
  
  -t {see shareable types below in this README}
                        DHIS2 object type to apply sharing, e.g. -t=sqlViews or -t=DE
                        
  -f FILTER             Filter on objects with DHIS2 field filter (add multiple 
                        filters with '&&') e.g. -f='name:like:ABC'
                        
  -w USERGROUP_READWRITE
                        UserGroup filter for Read-Write access (add multiple 
                        filters with '&&') e.g. -w='name:$ilike:aUserGroup7&&id:!eq:aBc123XyZ0u'
                        
  -r USERGROUP_READONLY
                        UserGroup filter for Read-Only access, (add multiple 
                        filters with '&&') e.g. -r='id:eq:aBc123XyZ0u'
                        
  -a {readwrite,none,readonly}
                        Public Access (with login), e.g. -a=readwrite
                        
  -v API_VERSION        DHIS2 API version e.g. -v=24
                        (if omitted, <URL>/api/endpoint will be used)
  -u USERNAME           DHIS2 username, e.g. -u=admin
  -p PASSWORD           DHIS2 password, e.g. -p=district
  -d                    Debug flag - writes more info to log file

```

### Shareable objects:

It's also possible to use acronyms/abbreviations like `de` or `catcombo`, `-t=ds` for dataSets

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
dhis2-pk-share-objects -s=play.dhis2.org/demo -t=dataElements -f='name:^like:All&&name:!like:cough' -w='name:like:Africare HQ' -r='name:like:Bo District' -a=readwrite -u=admin -p=district -v=24 -d
```
---
## Export readable indicator definition to CSV

**Script name:** `dhis-pk-indicator-definitions`

Writes indicator expressions (numerators/denominators) in a **readable format to a csv file**. Includes _names and number of orgunits for orgunit groups_, _dataelements (dataelement.categoryoptioncombo)_, _program dataelements_, _program indicators_, _trackedEntityAttributes_ and _constants_. It's possible to filter indicators with an object filter (see [`dhis2-pk-share-objects`](https://github.com/davidhuser/dhis2-pocket-knife#mass-sharing-of-objects-with-usergroups-through-filtering) for details). Note that when e.g. a dataElement is not shared with the user running the script but the indicator is, dataElement may still show up only with the UID.

Example output:
![ind-definitions](https://i.imgur.com/LFAlFpY.png)

Example column for numerator `ReUHfIn0pTQ - ANC 1-3 Dropout Rate`:
```
#{ANC 1st visit.Fixed}+#{ANC 1st visit.Outreach}-#{ANC 3rd visit.Fixed}-#{ANC 3rd visit.Outreach}
```

```
dhis2-pk-indicator-definitions --help
usage: dhis2-pk-indicator-definitions [-h] -s [-f] -u -p [-v] [-d]

PURPOSE: Create CSV with indicator definitions

arguments:
  -h, --help           show this help message and exit
  -s SERVER            DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo
  -f INDICATOR_FILTER  Indicator filter, e.g. -f='name:^like:HIV'
  -u USERNAME          DHIS2 username
  -p PASSWORD          DHIS2 password
  -v API_VERSION       DHIS2 API version e.g. -v=24
  -d                   Debug flag - writes more info to log file
```
### Indicator variables
For interpreting indicator variables (like `OUG{someUID}`), refer to [DHIS2 docs](https://docs.dhis2.org/master/en/developer/html/dhis2_developer_manual_full.html#d9584e5669)

### Example (try it out against DHIS2 demo instance):
```
dhis2-pk-indicator-definitions -s=play.dhis2.org/demo -u=admin -p=district
```
---

## Download metadata to JSON or XML or CSV

**Script name:** `dhis-pk-metadata-dl`

* It uses the metadata export feature (for 2.23+ versions) described in the [docs](https://docs.dhis2.org/master/en/developer/html/dhis2_developer_manual_full.html#webapi_metadata_export)
* It defaults to use JSON, but can be overriden by using `-y=xml` or `-y=csv`
* Note that CSV should not be used for direct import to DHIS2 as it may break things.
* You can use any common term for a type, e.g. `-t=ou` of `-t=CatCombos`

```
dhis2-pk-metadata-dl -h
usage: dhis2-pk-metadata-dl [-h] -s -t [-f] [-e] [-y] [-z]-u -p [-d]
                                                         
Download metadata

optional arguments:
  -h, --help         show this help message and exit
  -s SERVER          Server, e.g. play.dhis2.org/demo
  -t OBJECT_TYPE     DHIS2 object type to get, e.g. -t=dataElements
  -f OBJECT_FILTER   Object filter, e.g. -f='name:like:Acute'
  -e FIELDS          Fields to include, e.g. -f='id,name'
  -y {json,xml,csv}  File format, defaults to JSON
  -z COMPRESS        Compress/zip download (for XML and JSON only)
  -u USERNAME        DHIS2 username
  -p PASSWORD        DHIS2 password
  -d                 Debug flag - writes more info to log file
```

Example (try it out against DHIS2 demo instance):
```
dhis2-pk-metadata-dl -s=play.dhis2.org/demo -u=admin -p=district -t=dataElements -f='name:like:Acute'
```

---
## Export user info to CSV

Write information about users (paths of organisationUnits, userGroups membership) to a CSV file.

Click image for example CSV output:
![issue](https://i.imgur.com/2zkIFVi.png)

```
dhis2-pk-userinfo -h
usage: dhis2-pk-userinfo [-h] -s SERVER -u USERNAME -p PASSWORD [-v API_VERSION]
                   [-d]

Create CSV of orgunits / usergroups of users

optional arguments:
  -h, --help      show this help message and exit
  -s SERVER       DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo
  -u USERNAME     DHIS2 username
  -p PASSWORD     DHIS2 password
  -v API_VERSION  DHIS2 API version e.g. -v=24
  -d              Writes more info in log file

```

Example (try it out against DHIS2 demo instance):
`dhis2-pk-userinfo -s=play.dhis2.org/demo -u=admin -p=district`

---
## Export users with a misconfigured Organisation Unit assignment to CSV

**Script name:** `dhis2-pk-user-orgunits`

Writes all users of an Organisation Unit who are configured like below to a **csv file**. Users who are assigned both an Orgunit **and** sub-Orgunit can be a source of access errors.
![issue](https://i.imgur.com/MXiALrL.png)

```
dhis2-pk-user-orgunits --help
usage: dhis2-pk-user-orgunits [-h] -s -o -u -p [-v] [-d]

PURPOSE: Create CSV all users of an orgunit who also have sub-orgunits assigned

arguments:
  -h, --help      show this help message and exit
  -s SERVER       DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo
  -o ORGUNIT      Top-level orgunit UID to check its users
  -u USERNAME     DHIS2 username
  -p PASSWORD     DHIS2 password
  -v API_VERSION  DHIS2 API version e.g. -v=24
  -d              Writes more info in log file
```

### Example (try it out against DHIS2 demo instance):
```
dhis2-pk-user-orgunits -s=play.dhis2.org/demo -o=O6uvpzGd5pu -u=admin -p=district
```

---

### done

- [x] debug flag as optional argument
- [x] multiple filters for userGroups
- [x] API version as optional
- [x] added indicator expression script
- [x] acronym support for object types (`-t=de`)
- [x] multiple filter should be added with `&&` instead of `&`
- [x] new feature: download of metadata

### todo

- [ ] Script tests
- [ ] User-orgunits: Tree traversal of all OUs where Root=args.ou


