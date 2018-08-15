Mass sharing of objects via filtering
=====================================

Apply [sharing](https://docs.dhis2.org/master/en/user/html/sharing.html)
for DHIS2 metadata and data objects (dataElements, indicators, programs, ...) through 
[metadata object filtering](https://docs.dhis2.org/master/en/developer/html/dhis2_developer_manual_full.html#webapi_metadata_object_filter)
(for both shareable objects and userGroups).

It is now possible to share DATA access for object types data set,
tracked entity type, program and program stage. Read more
[here.](https://docs.dhis2.org/master/en/user/html/ch23s04.html)

**Script name:** `dhis2-pk-share`

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

Example to share metadata only:

```
dhis2-pk-share -s play.dhis2.org/2.29 -u admin -p district -f='id:eq:P3jJH5Tu5VC' -t=dataelement -a readonly -g 'id:eq:wl5cDMuUhmF' readwrite -g 'id:eq:OeFJOqprom6' readwrite
```

Example to share data sets (with data access):

```
dhis2-pk-share -s play.dhis2.org/2.29 -u admin -p district -f='id:eq:P3jJH5Tu5VC' -t=dataelement -a readonly -g 'id:eq:wl5cDMuUhmF' readwrite -g 'id:eq:OeFJOqprom6' readwrite
```
