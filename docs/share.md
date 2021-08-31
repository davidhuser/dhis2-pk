# Mass sharing of objects via filtering

Apply [sharing](https://docs.dhis2.org/en/full/use/user-guides/dhis-core-version-master/dhis2-user-manual.html#sharing)
for DHIS2 metadata and data objects (dataElements, indicators, programs, ...) through 
[metadata object filtering](https://docs.dhis2.org/en/full/develop/dhis-core-version-master/developer-manual.html#webapi_metadata_object_filter)
(for both shareable objects and userGroups).

Depending on the object type it is required to set the DATA access to (who can enter data), particularly for the object types:

* tracked entity type 
* program
* program stage
* data set
* category option

More info in the [dhis2 docs on data sharing and access control](https://docs.dhis2.org/en/full/use/user-guides/dhis-core-version-master/dhis2-user-manual.html#data-sharing-and-access-control).

**Script name:** `share`

## Usage

```
Example: dhis2-pk share -s play.dhis2.org/dev -u admin -p district -f 'id:eq:P3jJH5Tu5VC' -t dataelement -a readonly -g 'name:like:Admin' readwrite -g 'name:like:Research' readwrite

Share DHIS2 objects with userGroups via filters.

required arguments:
  -s SERVER             DHIS2 server URL
  -u USERNAME           DHIS2 username
  -t OBJECT_TYPE        DHIS2 object type to apply sharing, e.g. -t sqlView

optional arguments:
  -p PASSWORD           DHIS2 password
  -a PUBLICACCESS [PUBLICACCESS ...]
                        Public Access for all objects. 
                        Valid choices are: {none, readonly, readwrite}
                        For setting DATA access, add second argument, e.g. -a readwrite readonly
  -f FILTER             Filter on objects with DHIS2 field filter.
                        To add multiple filters:
                        - '&&' joins filters with AND
                        - '||' joins filters with OR
                        Example:  -f 'name:like:ABC||code:eq:X'
  -g USERGROUP [USERGROUP ...]
                        User Group to share objects with: FILTER METADATA [DATA]
                        - FILTER: Filter all User Groups. See -f for filtering mechanism
                        - METADATA: Metadata access for this User Group. {readwrite, none, readonly}
                        - DATA: Data access for this User Group. {readwrite, none, readonly}
                        Example:  -g 'id:eq:OeFJOqprom6' readwrite none
  -o                    Overwrite sharing - updates 'lastUpdated' field of all shared objects
  -e                    Extend existing sharing settings
  -l FILEPATH           Path to Log file (default level: INFO, pass -d for DEBUG)
  -d                    Debug flag


```

## Examples

A few examples are below (assuming a 2.29+ instance):

### Example 1: Data Elements

Example to share dataElements that start with `ANC`:

* Public Access: `readonly`
* User Group with `Admin` in its names to have `readwrite` access (for metadata)

`
dhis2-pk share -s play.dhis2.org/demo -u admin -p district -t dataelement -f 'name:$like:ANC' -a readonly -g 'name:like:Admin' readwrite 
`

Console output:

```
* INFO  2018-08-16 15:02:54,983  Sharing 4 dataElements with filter [name:$like:ANC]
* INFO  2018-08-16 15:02:55,093  User Groups with filter [name:like:Admin]
* INFO  2018-08-16 15:02:55,093  - wl5cDMuUhmF 'Administrators' ➜ [metadata:readwrite]
* INFO  2018-08-16 15:02:55,094  Public access ➜ [metadata:readonly]
* INFO  2018-08-16 15:02:55,094  1/4 dataElement Jtf34kNZhzP 'ANC 3rd visit'
* INFO  2018-08-16 15:02:55,260  2/4 dataElement cYeuwXTCPkU 'ANC 2nd visit'
* INFO  2018-08-16 15:02:55,362  3/4 dataElement fbfJHSPpUQD 'ANC 1st visit'
* INFO  2018-08-16 15:02:55,556  4/4 dataElement hfdmMSPBgLG 'ANC 4th or more visits'
```

### Example 2: Data Sets

Example to share Data Set with UID `aLpVgfXiz0f` where we need to specify METADATA **and** DATA access 
by simply supplying a second `readwrite`/ `readonly` / `none` argument.

* Public Access: Metadata access -> `readonly`, Data access -> `readwrite`
* User Groups with `Research` in its name: Metadata access -> `none`, Data access -> `readonly`
* User Group named `Kenya staff`: Metadata access -> `readonly`, Data access -> `none`


`
dhis2-pk share -s play.dhis2.org/demo -u admin -p district -t dataSets -f 'id:eq:aLpVgfXiz0f' -a readonly readwrite -g 'name:like:Research' none readonly -g 'name:eq:Kenya staff' readonly none
`

Console output:

```
* INFO  2018-08-16 15:22:55,703  Sharing 1 dataSet with filter [id:eq:aLpVgfXiz0f]
* INFO  2018-08-16 15:22:55,845  User Groups with filter [name:like:Research]
* INFO  2018-08-16 15:22:55,845  - wAAA1agEHin 'Cape Town University Research Group' ➜ [metadata:none] [data:readonly]
* INFO  2018-08-16 15:22:55,845  - k3xzluFKVyw 'Nairobi University Research Group' ➜ [metadata:none] [data:readonly]
* INFO  2018-08-16 15:22:55,984  User Groups with filter [name:eq:Kenya staff]
* INFO  2018-08-16 15:22:55,984  - YCPJDwzbe8T 'Kenya staff' ➜ [metadata:readonly] [data:none]
* INFO  2018-08-16 15:22:55,984  Public access ➜ [metadata:readonly] [data:readwrite]
* INFO  2018-08-16 15:22:55,984  1/1 dataSet aLpVgfXiz0f 'Population'
```

### Example 3: Extending existing sharing settings

To add additional User Group(s) to a Data Element that is already shared, use the argument `-e`.

`
dhis2-pk share -s play.dhis2.org/demo -u admin -p district -t dataSets -f 'id:eq:aLpVgfXiz0f' -g 'name:like:Research' none readonly -a none readwrite -e
`

Console output:

```
* INFO  2019-07-03 15:30:54,941  Sharing 1 dataSet with filter [id:eq:aLpVgfXiz0f]
* INFO  2019-07-03 15:30:55,073  User Groups with filter [name:like:Research]
* INFO  2019-07-03 15:30:55,074  - k3xzluFKVyw 'Nairobi University Research Group' ➡️️ [metadata:none] [data:readonly]
* INFO  2019-07-03 15:30:55,074  - wAAA1agEHin 'Cape Town University Research Group' ➡️️ [metadata:none] [data:readonly]
* INFO  2019-07-03 15:30:55,074  Public access ➡️️ [metadata:none] [data:readwrite]
* WARNING  2019-07-03 15:30:55,075  Extending with additional User Groups...
* INFO  2019-07-03 15:30:57,077  1/1 dataSet aLpVgfXiz0f 'Population'
```

Note: 
* You can supply the Public Access argument `-a` - if omitted it will re-use the existing setting for Public Access.
* Sharing settings via arguments have higher priority than what is already set on the server (to prevent double specification), i.e. what you specify will overwrite what is on the server

## Filtering

You can really use [any filter DHIS2 would allow]((https://docs.dhis2.org/master/en/developer/html/dhis2_developer_manual_full.html#webapi_metadata_object_filter)) in the Browser as well.

Additionally, you can join filters with *AND* or *OR*:
* `&&` joins filters with *AND* - e.g. name must be `XY` *AND* have valueType `INTEGER`: `-f 'name:eq:XY&&valueType:eq:INTEGER'`
* `||` joins filters with *OR* - e.g. name must contain `ABC` *OR* have a code equal to `XYZ`: `-f 'name:like:ABC||code:eq:XYZ'`

### Filter examples

* Share all data elements within a data element group: `-t dataElements -f 'dataElementGroups.id:eq:oDkJh5Ddh7d'`
* Share all programStages within a program: `-t programStages -f 'program.id:eq:uy2gU8kT1jF'`
* Share something with all UserGroups starting with `HQ-` in its name: `-g 'name:$like:HQ-' readwrite readonly`

Note: if you're using Windows you might run into problems but [they can be solved.](https://github.com/davidhuser/dhis2-pk/blob/master/docs/installation.md#windows)
