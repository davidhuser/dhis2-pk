Export user info to CSV
-----------------------

Write information about users (paths of organisationUnits, userGroup
membership) to a CSV file.

Example CSV output: |issue|

**Script name:** dhis2-pk-userinfo

::

   dhis2-pk-userinfo -h
   usage: dhis2-pk-userinfo [-h] [-s] [-u] [-p] [-v] [-d]

   optional arguments:
     -h, --help      show this help message and exit
     -s SERVER       DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo
     -u USERNAME     DHIS2 username
     -p PASSWORD     DHIS2 password
     -v API_VERSION  DHIS2 API version e.g. -v=28
     -d              Writes more info in log file

Example (try it out against DHIS2 demo instance):


.. code:: bash

    dhis2-pk-userinfo -s=play.dhis2.org/demo -u=admin -p=district


.. |issue| image:: https://i.imgur.com/2zkIFVi.png
