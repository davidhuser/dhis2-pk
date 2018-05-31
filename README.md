# ![icon](https://i.imgur.com/AWrQJ4N.png) dhis2-pocket-knife [![Version](https://img.shields.io/pypi/v/dhis2-pocket-knife.svg)](https://pypi.python.org/pypi/dhis2-pocket-knife) [![Build](https://travis-ci.org/davidhuser/dhis2-pk.svg?branch=master)](https://travis-ci.org/davidhuser/dhis2-pk) [![Licence](https://img.shields.io/pypi/l/dhis2-pocket-knife.svg)](https://pypi.python.org/pypi/dhis2-pocket-knife) 

Command-line tools to interact with the Web API of [DHIS2](https://dhis2.org). Features:

* [Mass sharing of objects via filtering](#mass-sharing-of-objects-via-filtering)
* [Readable indicator definition to CSV](#readable-indicator-definition-to-csv)
* [User info to CSV](#export-user-info-to-csv)
* [Post CSS file](#post-css-file)

## Installation / updating

* Installation with [pip](https://pip.pypa.io/en/stable/installing) (python package manager, see if it is installed: `pip -V`)
* `pip install dhis2-pocket-knife` or `pip install dhis2-pocket-knife --user`
* Upgrade with `pip install dhis2-pocket-knife -U`

## Usage

* Either pass arguments for a server / username / password or it make it read from a `dish.json` file as described in [baosystems/dish2](https://github.com/baosystems/dish2#configuration).
* Get help on using arguments, e.g.`dhis2-pk-share --help`

---

## Mass sharing of objects via filtering

Apply [sharing](https://docs.dhis2.org/master/en/user/html/sharing.html) for DHIS2 metadata and data objects (dataElements, indicators, programs, ...) 
through **[metadata object filtering](https://docs.dhis2.org/master/en/developer/html/dhis2_developer_manual_full.html#webapi_metadata_object_filter)** (for both shareable objects and userGroups).


> 2.29 support: It is now possible to set DATA access for object types *Data Set*, *Tracked Entity Type*, *Program* and *Program Stage*. 
Read more [here.](https://docs.dhis2.org/master/en/user/html/sharing.html)

**Script name:** `dhis2-pk-share`

```
usage: (example) dhis2-pk-share -s play.dhis2.org/dev -u admin -p district -f 'id:eq:P3jJH5Tu5VC' -t dataelement -a readonly -g 'name:like:Admin' readwrite -g 'name:like:Research' readwrite

Share DHIS2 objects with userGroups via filters.

required arguments:
  -s URL                DHIS2 server URL, e.g. 'play.dhis2.org/demo'
  -u USERNAME           DHIS2 username, e.g. -u admin
  -p PASSWORD           DHIS2 password, e.g. -p district
  -t OBJECT_TYPE        DHIS2 object type to apply sharing, e.g. -t sqlView
  
  -a PUBLICACCESS       Public Access for all objects
                        Valid choices are: readwrite, none, readonly
                        For setting DATA access, add second argument, e.g. -a readwrite readonly

optional arguments:
  -f FILTER             Filter on objects with DHIS2 field filter.
                        To add multiple filters:
                        - '&&' joins filters with AND
                        - '||' joins filters with OR
                        Example:  -f 'name:like:ABC||code:eq:X'
                        
  -g USERGROUP [...]    User Group to share objects with: FILTER METADATA [DATA]
                        - FILTER: Filter all User Groups. See -f for filtering mechanism
                        - METADATA: Metadata access for this User Group  {readwrite, none, readonly}
                        - DATA: Data access for this User Group  {readwrite, none, readonly}
                        Example:  -g 'id:eq:OeFJOqprom6' readwrite none
                        
  -o                    Overwrite sharing - updates 'lastUpdated' field of all shared objects
  -l FILEPATH           Path to Log file (default level: INFO, pass -d for DEBUG)
  -v API_VERSION        DHIS2 API version e.g. -v 28
  -d                    Debug flag

```

Example to share metadata only:

`
dhis2-pk-share -s play.dhis2.org/2.29 -u admin -p district -f 'id:eq:P3jJH5Tu5VC' -t dataelement -a readonly -g 'name:like:Admin' readwrite -g 'name:like:Research' readwrite
`

Example to share data sets (with data access):

`
dhis2-pk-share -s play.dhis2.org/2.29 -u admin -p district -f='name:eq:Population' -t=datasets -a readonly readwrite -g 'name:like:Admin' readwrite readonly -g 'name:like:Research' readwrite readonly
`

#### Migrating from `dhis2-pk-share-objects`

To set write access for the *Admins* User Group and read access for the *Users* User Group:

- Old way: `-w 'name:like:Admins' -r 'name:like:Users`
- New way: `-g 'name:like:Admins' readwrite    -g 'name:like:Users' readonly`

---
## Readable indicator definition to CSV

**Script name:** `dhis-pk-indicator-definitions`

Writes indicator expressions (numerators/denominators/expressions) of Indicators and Program Indicators in a **readable format to a csv file**. Includes _names and number of orgunits for orgunit groups_, _dataelements (dataelement.categoryoptioncombo)_, _program dataelements_, _program indicators_, _trackedEntityAttributes_ and _constants_. It's possible to filter indicators with an object filter (see [`dhis2-pk-share-objects`](https://github.com/davidhuser/dhis2-pocket-knife#mass-sharing-of-objects-with-usergroups-through-filtering) for details). Note that when e.g. a dataElement is not shared with the user running the script but the indicator is, dataElement may still show up only with the UID.

Example output:
![ind-definitions](https://i.imgur.com/LFAlFpY.png)

Example column for numerator `ReUHfIn0pTQ - ANC 1-3 Dropout Rate`:
```
#{ANC 1st visit.Fixed}+#{ANC 1st visit.Outreach}-#{ANC 3rd visit.Fixed}-#{ANC 3rd visit.Outreach}
```

```
dhis2-pk-indicator-definitions --help
usage: dhis2-pk-indicator-definitions [-h] [-s] [-f] [-u] [-p] [-v] [-d]

optional arguments:
  -h, --help           show this help message and exit
  -s SERVER            DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo
  -t INDICATOR_TYPE    Type of indicator: 'indicators' or 'programIndicators'
  -f INDICATOR_FILTER  Indicator filter, e.g. -f='name:$like:HIV'
  -u USERNAME          DHIS2 username
  -p PASSWORD          DHIS2 password
  -v API_VERSION       DHIS2 API version e.g. -v=28
  -d                   Debug flag - writes more info to log file
```
### Indicator variables
For interpreting indicator variables (like `OUG{someUID}`), refer to [DHIS2 docs](https://docs.dhis2.org/master/en/developer/html/dhis2_developer_manual_full.html#d9584e5669)

##### Example (try it out against DHIS2 demo instance):
```
dhis2-pk-indicator-definitions -s=play.dhis2.org/demo -u=admin -p=district
```
---

## Export user info to CSV

Write information about users (paths of organisationUnits, userGroup membership) to a CSV file.

Click image for example CSV output:
![issue](https://i.imgur.com/2zkIFVi.png)

```
dhis2-pk-userinfo -h
usage: dhis2-pk-userinfo [-h] [-s] [-u] [-p] [-v] [-d]

optional arguments:
  -h, --help      show this help message and exit
  -s SERVER       DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo
  -u USERNAME     DHIS2 username
  -p PASSWORD     DHIS2 password
  -v API_VERSION  DHIS2 API version e.g. -v=28
  -d              Writes more info in log file

```

Example (try it out against DHIS2 demo instance):
`dhis2-pk-userinfo -s=play.dhis2.org/demo -u=admin -p=district`

---
## Post CSS file

Simply post a CSS file to a server. 

```
dhis2-pk-post-css -h
usage: dhis2-pk-post-css [-h] [-s] -c [-u] [-p] [-d]

optional arguments:
  -h, --help      show this help message and exit
  -s SERVER       DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo
  -c CSS          CSS file to post
  -u USERNAME     DHIS2 username
  -p PASSWORD     DHIS2 password
  -d              Writes more info in log file

```

Example (with reading out a `dish.json` file):

`dhis2-pk-post-css -c=style.css`

---

### Install from source

```
wget https://github.com/davidhuser/dhis2-pk/archive/master.zip
unzip master.zip
cd dhis2-pocket-knife
python setup.py install
```

### Done

- [x] debug flag as optional argument
- [x] multiple filters for userGroups
- [x] API version as optional
- [x] added indicator expression script
- [x] multiple filter should be added with `&&` instead of `&`
- [x] read from dish.json file
- [x] new feature: POST CSS to server
- [x] sharing: honor existing sharing settings and only update when different to arguments
- [x] color output
- [x] file logging
- [x] 2.29 support (data and metadata sharing)

### Todos

- [ ] Script tests
- [ ] Interactive sharing
