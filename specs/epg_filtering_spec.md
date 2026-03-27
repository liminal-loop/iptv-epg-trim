# EPG Filtering Specification

## XMLTV Structure

Relevant XML elements:

```xml
<channel id="...">
<display-name>...</display-name>

<programme channel="...">
```

## Channel Matching

For each <channel> element:

1. Extract all <display-name> values.
2. Normalize each display-name (trim whitespace, lowercase, collapse multiple spaces).
3. Keep the channel if **any** display-name matches a playlist identifier.
4. Build a mapping: playlist identifier → channel id.

Example:

```xml
<channel id="2379">
<display-name lang="de">First Channel HD</display-name>
```

If the playlist identifier is `First Channel HD` the channel must be kept.

## Programme Filtering

Filter `<programme>` elements:

- Keep if programme@channel exists in the kept channel IDs mapping

## Output Format

The output must remain a valid XMLTV document.

Root element: `<tv>`

## Performance Requirements

EPG files may be very large.

XML must be processed using streaming parsing to avoid loading the entire document into memory.
