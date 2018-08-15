Export user info to CSV
=======================

Write information about users (paths of organisationUnits, userGroup
membership, username, phone number, ...) to a CSV file.

Example CSV output: ![issue](https://i.imgur.com/2zkIFVi.png)

**Script name:** dhis2-pk-userinfo

```
Example: dhis2-pk-userinfo -s play.dhis2.org/demo -u admin -p district

Create CSV of user information.

optional arguments:
  -s SERVER       DHIS2 server URL
  -u USERNAME     DHIS2 username
  -p PASSWORD     DHIS2 password
  -v API_VERSION  DHIS2 API version e.g. -v=28
```
