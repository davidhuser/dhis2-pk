# Post CSS file

Simply post a CSS file to a server (e.g. to style the login page).

**Script name**: `dhis2-pk-post-css`

## Usage

```
Example: dhis2-pk-post-css -s=play.dhis2.org/dev -u=admin -p=district -c=file.css

Post CSS stylesheet to a server.

required arguments:
  -c CSS       Path to CSS file

optional arguments:
  -s SERVER    DHIS2 server URL
  -u USERNAME  DHIS2 username
  -p PASSWORD  DHIS2 password
```

## Example

Put this into a `style.css`:

```css
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
```

then:

```bash
dhis2-pk-post-css -s=play.dhis2.org/dev -c=style.css -u=admin -p=district
```
