## Readable indicator definition to CSV

**Script name:** `dhis-pk-indicator-definitions`

Writes indicator expressions (numerators/denominators/expressions) of Indicators and Program Indicators in a **readable format to a csv file**. Includes _names and number of orgunits for orgunit groups_, _dataelements (dataelement.categoryoptioncombo)_, _program dataelements_, _program indicators_, _trackedEntityAttributes_ and _constants_. 

It's possible to filter indicators with an object filter (see [`dhis2-pk-share`](../docs/share.md) for details). 

Note that when e.g. a dataElement is not shared with the user running the script but the indicator is, dataElement may still show up only with the UID.

Demo output:

![ind-definitions](https://i.imgur.com/LFAlFpY.png)

Example column for numerator `ANC 1-3 Dropout Rate` (`ReUHfIn0pTQ`):

```
#{ANC 1st visit.Fixed}+#{ANC 1st visit.Outreach}-#{ANC 3rd visit.Fixed}-#{ANC 3rd visit.Outreach}
```

### Usage
```
Example: dhis2-pk-indicator-definitions -s play.dhis2.org/demo -u admin -p district -t indicators

Readable indicator definition to CSV.

required arguments:
  -t INDICATOR_TYPE    indicators or programIndicators

optional arguments:
  -s SERVER            DHIS2 server URL
  -f INDICATOR_FILTER  Indicator filter, e.g. -f 'name:like:HIV' - see
                       dhis2-pk-share --help
  -u USERNAME          DHIS2 username
  -p PASSWORD          DHIS2 password
  -v API_VERSION       DHIS2 API version e.g. -v=28

```
### Indicator variables
For interpreting indicator variables (like `OUG{someUID}`), refer to [DHIS2 docs](https://docs.dhis2.org/master/en/developer/html/dhis2_developer_manual_full.html#d9584e5669).

### Example

(try it out!)

`dhis2-pk-indicator-definitions -s=play.dhis2.org/demo -u=admin -p=district`
