# Additional data integrity

**Script name:** `data-integrity`

To enhance the DHIS2 built-in data integrity, this script warns if the following configurations are detected:

* Validation Rules that have invalid expressions
* Option Sets that are not in any Data Element, Tracked Entity Attribute or Attribute
* Option Sets with Options that have an invalid sort order
* Option Sets with Options that have duplicate codes
* Category Options that are not in any Category
* Category not in any Category Combo
* Category Combo not in any Data Element, Data Set Element, Program or Data Set

## Usage

```
Example: dhis2-pk data-integrity -s play.dhis2.org/demo -u admin -p district

Run additional data integrity checks.

required arguments:
  -s SERVER    DHIS2 server URL
  -u USERNAME  DHIS2 username

optional arguments:
  -p PASSWORD  DHIS2 password
```