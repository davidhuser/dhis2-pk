Post CSS file
-------------

Simply post a CSS file to a server (e.g. to style the login page).

::

   dhis2-pk-post-css -h
   usage: dhis2-pk-post-css [-h] [-s] -c [-u] [-p] [-d]

   optional arguments:
     -h, --help      show this help message and exit
     -s SERVER       DHIS2 server URL without /api/ e.g. -s=play.dhis2.org/demo
     -c CSS          CSS file to post
     -u USERNAME     DHIS2 username
     -p PASSWORD     DHIS2 password
     -d              Writes more info in log file

Example
^^^^^^^^

Put this into a ``style.css``:

::

    .loginPage {
      background-color: #354f6b;
      color: #28a745;
    }

    #flagArea {
      border: 1px solid #28a745;
    }

    #footerArea {
      background-color: #3a4c5f;
      border-top: 1px solid #28a745;
      color: #28a745;
    }


then:

``dhis2-pk-post-css -s=play.dhis2.org/dev -c=style.css -u=admin -p=district``