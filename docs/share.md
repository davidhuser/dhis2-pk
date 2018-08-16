# Mass sharing of objects via filtering

Apply [sharing](https://docs.dhis2.org/master/en/user/html/sharing.html)
for DHIS2 metadata and data objects (dataElements, indicators, programs, ...) through 
[metadata object filtering](https://docs.dhis2.org/master/en/developer/html/dhis2_developer_manual_full.html#webapi_metadata_object_filter)
(for both shareable objects and userGroups).

It is now possible to share DATA access for object types data set,
tracked entity type, program and program stage on DHIS2 instances 2.29+. Read more
[here.](https://docs.dhis2.org/master/en/user/html/ch23s04.html)

**Script name:** `dhis2-pk-share`

## Usage

```
Example: dhis2-pk-share -s play.dhis2.org/dev -u admin -p district -f 'id:eq:P3jJH5Tu5VC' -t dataelement -a readonly -g 'name:like:Admin' readwrite -g 'name:like:Research' readwrite

Share DHIS2 objects with userGroups via filters.

required arguments:
  -t OBJECT_TYPE        DHIS2 object type to apply sharing, e.g. -t sqlView
  -a PUBLICACCESS [PUBLICACCESS ...]
                        Public Access for all objects. 
                        Valid choices are: {readonly, none, readwrite}
                        For setting DATA access, add second argument, e.g. -a readwrite readonly

optional arguments:
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
  -l FILEPATH           Path to Log file (default level: INFO, pass -d for DEBUG)
  -v API_VERSION        DHIS2 API version e.g. -v 28
  -s URL                DHIS2 server URL
  -u USERNAME           DHIS2 username, e.g. -u admin
  -p PASSWORD           DHIS2 password, e.g. -p district
  -d                    Debug flag

```

## Examples

A few examples for a 2.29+ DHIS2 instance are below.

### Example 1: Data Elements

Example to share dataElements that start with `ANC`:

* Public Access: `readonly`
* User Group with `Admin` in its names to have `readwrite` access (for metadata)

`
dhis2-pk-share -s play.dhis2.org/2.29 -u admin -p district -t dataelement -f 'name:$like:ANC' -a readonly -g 'name:like:Admin' readwrite 
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

* Public Access: Metadata access -> `none`, Data access -> `readwrite`
* User Groups with `Research` in its name: Metadata access -> `none`, Data access -> `readonly`
* User Group named `Kenya staff`: Metadata access -> `readonly`, Data access -> `none`


`
dhis2-pk-share -s play.dhis2.org/2.29 -u admin -p district -t dataSets -f 'id:eq:aLpVgfXiz0f' -a readonly readwrite -g 'name:like:Research' none readonly -g 'name:eq:Kenya staff' readonly none
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

## Filtering

You can really use [any filter DHIS2 would allow]((https://docs.dhis2.org/master/en/developer/html/dhis2_developer_manual_full.html#webapi_metadata_object_filter)) in the Browser as well.

Additionally, you can join filters with *AND* or *OR*:
* `&&` joins filters with *AND* - e.g. name must be `XY` *AND* have valueType `INTEGER`: `-f 'name:eq:XY&&valueType:eq:INTEGER'`
* `||` joins filters with *OR* - e.g. name must contain `ABC` *OR* have a code equal to `XYZ`: `-f 'name:like:ABC||code:eq:XYZ'`

### Filter examples

* Share all data elements within a data element group: `-t dataElements -f 'dataElementGroups.id:eq:oDkJh5Ddh7d'`
* Share all programStages within a program: `-t programStages -f 'program.id:eq:uy2gU8kT1jF'`
* Share something with all UserGroups starting with `HQ-` in its name: `-g 'name:$like:HQ-' readwrite readonly`
