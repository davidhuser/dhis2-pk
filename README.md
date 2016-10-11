# dhis2-pocket-knife

Tools to interact with [DHIS2](https://dhis2.org) REST API in bulk.

## Installation

* *pip python package manager* must be installed (check [installation instructions](https://pip.pypa.io/en/stable/installing))
* `pip install dhis2-pocket-knife`

## Usage
* Change directories with `cd` command where root of the directory is located
* Run `screen -L python <file-name>.py` and the arguments as required
* Be sure the specified user has the authorities to run these tasks for the specified DHIS2 server
* Writes to a logfile called `screenlog.0`

## Bulk sharing settings of objects

Apply sharing settings for DHIS2 objects (dataElements, indicators, programs, ...) based on metadata object filtering. This assumes structured object properties (e.g. all object names / codes have the same prefix or suffix).

| argument  |description   |required?   |
|---|---|---|
|`--server`   |server base, e.g. play.dhis2.org/demo   | yes  |
|`--object_type`   |type of object, e.g. dataElements   |yes   |
|`--filter`   |metadata object filter(s) (case sensitive), e.g. name:like:vaccine - **[docs](https://dhis2.github.io/dhis2-docs/master/en/developer/html/dhis2_developer_manual_full.html#webapi_metadata_object_filter)**   |yes   |
|`--usergroup_readwrite`  |name of usergroup which should get Read-Write access   |no   |
|`--usergroup_readonly`   |name of usergroup which should get Read-Only access   |no   |
|`--publicaccess` | public access (with login), e.g. readwrite, readonly, none   |yes   |
|`--username`   |DHIS2 username   |yes   |
|`--password`   |DHIS2 password   |yes   |

Full example:
`share-objects.py --server=play.dhis2.org/demo --object-type=dataElements --filter="name:like:Vaccine&code:^!like:CORE_DE" --usergroup_readwrite="Bo District Management" --usergroup_readonly="Bo District hospitals" --publicaccess=none --username=admin --password=district`

## Find users with a misconfigured Organization Unit assignment

Returns all users of an Organisation Unit that are configured like below. Users who are assigned both an Orgunit **and** sub-Orgunit are a source of access errors.
![issue](https://i.imgur.com/MXiALrL.png)

|argument   |description   |
|---|---|
|`--server`   |server base, e.g. play.dhis2.org/demo   |
|`--orgunit`   |Orgunit UID to check its users     |
|`--username`   |DHIS2 username   |
|`--password`   |DHIS2 password   |
Full example:
`user-orgunits.py --server=play.dhis2.org/demo --orgunit=JdhagCUEMbj --username=admin --password=district`

## Bulk deletion of objects

Delete objects based on a list of UIDs in a text file. Note: [baosystems/dish2](https://github.com/baosystems/dish2) may be better capable of this.

|argument   |description   |
|---|---|
|`--server`   |server base, e.g. play.dhis2.org/demo   |
|`--uid_file`   |text file with UIDs split by newline/break     |
|`--username`   |DHIS2 username   |
|`--password`   |DHIS2 password   |

Full example:
`delete-objects.py --server=play.dhis2.org/demo --uid_file="UIDs.txt" --username=admin --password=district`
