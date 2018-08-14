Mass sharing of objects via filtering
-------------------------------------

Apply `sharing <https://docs.dhis2.org/master/en/user/html/sharing.html>`__
for DHIS2 metadata and data objects (dataElements, indicators, programs,
…) through `metadata object filtering <https://docs.dhis2.org/master/en/developer/html/dhis2_developer_manual_full.html#webapi_metadata_object_filter>`__ (for both shareable objects and userGroups).

It is now possible to share DATA access for object types data set, tracked entity type, program and program stage. Read
more `here. <https://docs.dhis2.org/master/en/user/html/ch23s04.html>`__

**Script name:** ``dhis2-pk-share``

::

   usage: dhis2-pk-share [-h] [-s] -t -f [-g] -a [-o] [-l] [-v] [-u] [-p] [-d]

   Share DHIS2 objects with userGroups FOR 2.29 SERVERS or newer

   required arguments:
     -s URL                DHIS2 server URL, e.g. 'play.dhis2.org/demo'
     -t OBJECT_TYPE        DHIS2 object type to apply sharing, e.g. sqlView
     -f FILTER             Filter on objects with DHIS2 field filter.
                           Add multiple filters with '&&' or '||'.
                           Example: -f 'name:like:ABC||code:eq:X'
     -a PUBLIC [PUBLIC ...]
                           publicAccess (with login).
                           Valid choices are: readwrite, none, readonly

   optional arguments:
     -g USERGROUP [USERGROUP ...]
                           Usergroup setting: FILTER METADATA [DATA] - can be repeated any number of times."
                           FILTER: Filter all User Groups. See -f for filtering mechanism
                           METADATA: Metadata access for this User Group. See -a for allowed choices
                           DATA: Data access for this User Group. optional (only for objects that support data sharing). see -a for allowed choices.
                           Example: -g 'id:eq:OeFJOqprom6' readwrite none
     -o                    Overwrite sharing - updates 'lastUpdated' field of all shared objects
     -l LOGGING_TO_FILE    Path to Log file (default level: INFO, pass -d for DEBUG), e.g. l='/var/log/pk.log'
     -v API_VERSION        DHIS2 API version e.g. -v=28
     -u USERNAME           DHIS2 username, e.g. -u=admin
     -p PASSWORD           DHIS2 password, e.g. -p=district
     -d                    Debug flag

Example to share metadata only:

``dhis2-pk-share -s play.dhis2.org/2.29 -u admin -p district -f='id:eq:P3jJH5Tu5VC' -t=dataelement -a readonly -g 'id:eq:wl5cDMuUhmF' readwrite -g 'id:eq:OeFJOqprom6' readwrite``

Example to share data sets (with data access):

``dhis2-pk-share -s play.dhis2.org/2.29 -u admin -p district -f='id:eq:P3jJH5Tu5VC' -t=dataelement -a readonly -g 'id:eq:wl5cDMuUhmF' readwrite -g 'id:eq:OeFJOqprom6' readwrite``
