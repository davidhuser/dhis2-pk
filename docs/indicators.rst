Readable indicator definition to CSV
------------------------------------

**Script name:** ``dhis-pk-indicator-definitions``

Writes indicator expressions (numerators/denominators) in a **readable
format to a csv file**. Includes *names and number of orgunits for
orgunit groups*, *dataelements (dataelement.categoryoptioncombo)*,
*program dataelements*, *program indicators*, *trackedEntityAttributes*
and *constants*. It’s possible to filter indicators with an object
filter (see
```dhis2-pk-share-objects`` <https://github.com/davidhuser/dhis2-pocket-knife#mass-sharing-of-objects-with-usergroups-through-filtering>`__
for details). Note that when e.g. a dataElement is not shared with the
user running the script but the indicator is, dataElement may still show
up only with the UID.

Example output: |ind-definitions|

Example column for numerator ``ReUHfIn0pTQ - ANC 1-3 Dropout Rate``:

::

   #{ANC 1st visit.Fixed}+#{ANC 1st visit.Outreach}-#{ANC 3rd visit.Fixed}-#{ANC 3rd visit.Outreach}

.. _usage-2:

Usage
^^^^^

::

   dhis2-pk-indicator-definitions --help
   usage: dhis2-pk-indicator-definitions [-h] [-s] [-f] [-u] [-p] [-v] [-d]

   optional arguments:
     -h, --help           show this help message and exit
     -s SERVER            DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo
     -f INDICATOR_FILTER  Indicator filter, e.g. -f='name:$like:HIV'
     -u USERNAME          DHIS2 username
     -p PASSWORD          DHIS2 password
     -v API_VERSION       DHIS2 API version e.g. -v=28

Indicator variables
^^^^^^^^^^^^^^^^^^^^

For interpreting indicator variables (like ``OUG{someUID}``), refer to
`DHIS2
docs <https://docs.dhis2.org/master/en/developer/html/dhis2_developer_manual_full.html#d9584e5669>`__

Example
^^^^^^^^

 Try it out against DHIS2 demo instance:

::

   dhis2-pk-indicator-definitions -s=play.dhis2.org/demo -u=admin -p=district

.. |ind-definitions| image:: https://i.imgur.com/LFAlFpY.png
