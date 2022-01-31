# Import Fake Data

**BETA:** Create *fake* data for event programs and data sets. 
Useful for building analytic objects such as dashboads and charts.

> Warning:
> Do not import fake data to your production environments. 


**Script name**: `fake-data`

## Usage

```
Example: dhis2-pk fake-data -s play.dhis2.org/demo -u admin -p district -i kla3mAPgvCH -n 100

Import fake data for Event programs or Data Sets

required arguments:
  -s SERVER    DHIS2 server URL
  -u USERNAME  DHIS2 username
  -i UID       UID for program or data set to import fake data for.
  -n AMOUNT    Amount of events or dataValueSet templates.  min: 1 - max: 100000

optional arguments:
  -p PASSWORD  DHIS2 password
```

## Considerations

* Amount: Good starting points for the parameter ``-n`` (amount):
  * Event programs: 1000
  * Data sets: 100 for big data sets, 1000 for small data sets
* Event coordinates: randomized somewhere near Nigeria.

## Limitations

* Category option start- and end dates cannot be accounted for
* Organisation unit open- and close dates cannot be accounted for  
* Tracker programs are not supported (only Programs without registration)
* Not all DE valueType are supported (i.e. not supported: FILE, TRACKER_ASSOCIATE, USERNAME, COORDINATE, 
  IMAGE, LETTER, PHONE_NUMBER, AGE)  
* Due to the nature of randomization there isn't a duplicate check for data value sets, so there is a 
possibility of ignored values.
