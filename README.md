# dhis2-pocket-knife

Command-line tools to interact with [DHIS2](https://dhis2.org) REST API in bulk.

![screenshot](https://i.imgur.com/Hi5lSpM.png)

## Installation

* *pip* (python package manager) must be installed (check [installation instructions](https://pip.pypa.io/en/stable/installing))
* `pip install dhis2-pocket-knife`

## Usage
* In a terminal: `dhis2-pk-<scriptname> --argument=<something>` and the arguments as required.
* Get help on using arguments: `dhis2-pk-<scriptname> --help`
* Be sure the specified user has the authorities to run these tasks for the specified DHIS2 server.
* Logs to a log file called `dhis2-pk.log`

---

## Bulk sharing settings of objects

**Script name:** `dhis2-pk-share-objects`

Apply sharing settings for DHIS2 metadata objects (dataElements, indicators, programs, ...) based on metadata object filtering. This assumes structured object properties (e.g. all object names / codes have the same prefix or suffix).

| argument                       |description   |required   |
|---|---|---|
|`-s` / `--server`               |Server base, e.g. `play.dhis2.org/demo`   |**yes**  |
|`-t` / `--object_type`          |Type of object, e.g. `dataElements`   |**yes**   |
|`-f` / `--filter`               |Object filter(s) in single quotes (`'xx'`): `-f='name:like:vaccine'` **[Docs](https://dhis2.github.io/dhis2-docs/master/en/developer/html/dhis2_developer_manual_full.html#webapi_metadata_object_filter)**   |**yes**   |
|`-w` / `--usergroup_readwrite`  |Exact name of usergroup which should get *Read-Write* access to objects   |no   |
|`-r` / `--usergroup_readonly`   |Exact name of usergroup which should get *Read-Only* access to objects   |no   |
|`-a` / `--publicaccess`         |Public access (with login), one of: `readwrite`, `readonly`, `none`   |**yes**   |
|`-u` / `--username`             |DHIS2 username   |**yes**   |
|`-p` / `--password`             |DHIS2 password   |**yes**   |
|`-d` / `--debug`                |Log more info to log file   |no |


Example (try it out against DHIS2 demo instance):

```
dhis2-pk-share-objects --server=play.dhis2.org/demo --object_type=dataElements --filter='name:^like:All&name:!like:cough' --usergroup_readwrite='Africare HQ' --usergroup_readonly='Bo District M&E officers' --publicaccess=readwrite --username=admin --password=district
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


### TODO

~~- debug flag as optional argument~~

share-objects.py:

- arguments: userGroups: multiple names as arguments
- arguments: userGroups: UID as argument
- arguments: support for omitting field filters (= apply for all objects)

user-orgunits.py:

- validating "data analysis" org unit tree as well (=dataViewOrganisationUnits)

---
PyPI link: https://pypi.python.org/pypi/dhis2-pocket-knife
