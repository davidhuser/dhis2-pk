# Import Fake Data

**BETA:** Create fake data for event programs and data sets

**Script name**: `fake-data`

## Usage

```
Example: dhis2-pk fake-data -s=play.dhis2.org/dev -u=admin -p=district -i q04UBOqq3rp -n 100

usage: 
Example: dhis2-pk fake-data -s play.dhis2.org/demo -u admin -p district

Import faked data for Event programs or Data Sets

required arguments:
  -s SERVER    DHIS2 server URL
  -u USERNAME  DHIS2 username
  -i UID       UID for program or data set to import fake data for
  -n AMOUNT    Amount of events or dataValueSet templates to import

optional arguments:
  -p PASSWORD  DHIS2 password
```

## Considerations

Good starting points for the parameter ``-n`` (amount):

* Event programs: 1000
* Data sets: 1000 for big data sets, 20000 for small data sets

If the file size is huge, the data will not be imported directly but rather stored as a JSON file on the computer.

## Limitations

* Category option start- and end dates cannot be accounted for
* Tracker programs are not supported (only Programs without registration)
* Not all DE valueType are supported  
* Due to the nature of randomization there isn't a duplicate check for data value sets