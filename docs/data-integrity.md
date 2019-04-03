# Additional data integrity

To enhance the DHIS2 built-in data integrity, this script checks the following things:

* Validation Rules - invalid expressions
* Option Sets not in any Data Element, Tracked Entity Attribute or Attribute
* Category Option not in any Category
* Category not in any Category Combo
* Category Combo not in any Data Element, Data Set Element, Program or Data Set

## Usage

```
Example: dhis2-pk-data-integrity -s play.dhis2.org/demo -u admin -p district

Additional data integrity checks.

optional arguments:
  -h, --help      show this help message and exit
  -s SERVER       DHIS2 server URL
  -u USERNAME     DHIS2 username
  -p PASSWORD     DHIS2 password
  -v API_VERSION  DHIS2 API version e.g. -v=28
```