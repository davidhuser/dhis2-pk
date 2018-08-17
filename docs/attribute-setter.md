# Attribute setter

Set custom attributes for many objects sourced from a CSV.

**Script name:** `dhis2-pk-attribute-setter`

A CSV could look like this:

```
uid,attributeValue
UID1,myNewValue
UID2,anotherValue
```
Or, as viewed from Excel:

```
uid   | attributeValue
------|---------------
UID1  | myNewValue
UID2  | anotherValue
```

With *one* call of the script, it\'s only possible to set an attribute
(`-a` sets the UID) for one object type (`-t`, sets the object type) -
but for many objects.

*Note:* It **does** update the existing value if it already exists.

## Usage

```
Example: dhis2-pk-attribute-setter -s play.dhis2.org/dev -u admin -p district -c file.csv -t organisationUnits -a pt5Ll9bb2oP

CSV file structure:
uid   | attributeValue
------|---------------
UID   | myValue

Set Attribute Values sourced from CSV file.

required arguments:
  -t OBJECT_TYPE    Object type to set attributeValues to: {organisationUnits, dataElements, ...}
  -c SOURCE_CSV     Path to CSV file with Attribute Values
  -a ATTRIBUTE_UID  Attribute UID

optional arguments:
  -s SERVER         DHIS2 server URL
  -u USERNAME       DHIS2 username
  -p PASSWORD       DHIS2 password

```