# dhis2-pocket-knife

Command-line tools to interact with [DHIS2](https://dhis2.org) REST API in bulk, e.g. mass sharing of objects with userGroups

## Installation

* [pip](https://pip.pypa.io/en/stable/installing) (python package manager) must be installed
* `pip install dhis2-pocket-knife`

## Usage
* Get help on using arguments: `dhis2-pk-<scriptname> --help`
* Be sure the specified user has the authorities to run these tasks for the specified DHIS2 server.
* Logs to a file: `dhis2-pk.log`

---

## Mass sharing of objects with userGroups through filtering

**Script name:** `dhis2-pk-share-objects`

Apply sharing settings for DHIS2 metadata objects (dataElements, indicators, programs, ...) based on metadata object filtering. This assumes structured object properties (e.g. all object names / codes have the same prefix or suffix).

| argument|description   |required   |
|---|---|---|
|`-s` |Server base URL, e.g. `play.dhis2.org/demo`   |**yes**  |
|`-t` |Type of object, e.g. `dataElements` - see [list](https://github.com/davidhuser/dhis2-pocket-knife/blob/master/README.md#shareable-objects)   |**yes**   |
|`-f` |Object filter(s) in single quotes (`'xx'`): `-f='name:like:vaccine'` **[Docs](https://dhis2.github.io/dhis2-docs/master/en/developer/html/dhis2_developer_manual_full.html#webapi_metadata_object_filter)**   |**yes**   |
|`-w` |Filter(s) of usergroup which should get *Read-Write* access to objects (multiple filters: concatenated with `&`), e.g. `-w='name:$ilike:UG1&id:!eq:aBc123XyZ0u'`  |no   |
|`-r` |Filter(s) of usergroup which should get *Read-Only* access to objects (multiple filters: concatenated with `&`), e.g. ` -r='id:eq:aBc123XyZ0u'`  |no   |
|`-a` |Public access (with login), one of: `readwrite`, `readonly`, `none`   |**yes**   |
|`-v` |DHIS2 API version, e.g. `-v=24`   |no   |
|`-u` |DHIS2 username e.g.`-u=admin`|**yes**   |
|`-p` |DHIS2 password e.g. `-p=district`|**yes**   |
|`-d` |Log more info to log file |no |


### Shareable objects:
- userAuthorityGroups
- userGroups
- sqlViews
- constants
- optionSets
- optionGroups
- optionGroupSets
- legendSets
- organisationUnitGroupSet
- organisationUnitGroupSets
- categoryOptions
- categoryOptionGroupSet
- categoryOptionGroupSets
- categories
- categoryCombos
- dataElements
- dataElementGroups
- dataElementGroupSets
- indicators
- indicatorGroups
- indicatorsGroupSets
- dataSets
- dataApprovalLevels
- dataApprovalLevelWorkflows
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

Example (try it out against DHIS2 demo instance):

```
dhis2-pk-share-objects -s=play.dhis2.org/demo -t=dataElements -f='name:^like:All&name:!like:cough' -w='name:like:Africare HQ' -r='Bo District M&E officers' -a=readwrite -u=admin -p=district -v=24 -d
```

## Find users with a misconfigured Organisation Unit assignment

**Script name:** `dhis2-pk-user-orgunits`

Writes all users of an Organisation Unit who are configured like below to a **csv file**. Users who are assigned both an Orgunit **and** sub-Orgunit can be a source of access errors.
![issue](https://i.imgur.com/MXiALrL.png)

|argument              |description   |required|
|---|---|---|
|`-s` / `--server`     |Server base, e.g. `play.dhis2.org/demo`   |**yes**|
|`-o` / `--orgunit`    |Orgunit UID to check its users     |**yes**|
|`-u` / `--username`   |DHIS2 username   |**yes**|
|`-p` / `--password`   |DHIS2 password   |**yes**|
|`-d` / `--debug`      |Log more info to log file   |no|

Example:
```
dhis2-pk-user-orgunits --server=play.dhis2.org/demo --orgunit=O6uvpzGd5pu --username=admin --password=district
```

## Bulk deletion of metadata objects

**Script name:** `dhis2-pk-delete-objects`

Delete metadata objects based on a list of UIDs in a text file. Note: [baosystems/dish2](https://github.com/baosystems/dish2#remove-metadata-objects) may be an alternative.

|argument   |description   |required |
|---|---|---|
|`-s` / `--server`        |Server base, e.g. `play.dhis2.org/demo`   |**yes** |
|`-t` / `--object_type`   |Type of metadata object, e.g. `dataElements`   |**yes** |
|`-i` / `--uid_file`      |Text file with UIDs split by newline/break     |**yes** |
|`-u` / `--username`      |DHIS2 username   |**yes** | 
|`-p` / `--password`      |DHIS2 password   |**yes** |
|`-d` / `--debug`         |Log more info to log file   |no |

Example:

```
dhis2-pk-delete-objects --server=play.dhis2.org/demo --uid_file='UIDs.txt' --object_type=dataElements --username=admin --password=district
```

(put the following in a file called UIDs.txt to test it):

```
FHD3wiSM7Sn
iKGjnOOaPlE
XTqOHygxDj5
```

---


### done

- ~~debug flag as optional argument (DONE)~~
- ~~arguments: userGroups: multiple filters for userGroups (DONE)~~
- ~~API version (optional argument) (DONE)~~
- ~~better help text for sharing `-h`~~


---
PyPI link: https://pypi.python.org/pypi/dhis2-pocket-knife
