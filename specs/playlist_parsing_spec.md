# Playlist Parsing Specification

## Supported Formats

- M3U
- M3U8

Both formats follow the same structure.

Example playlist entry:

```m3u
#EXTINF:0 tvg-rec="0",First Channel HD
http://example.com/channel/stream.m3u8
```

## Extracted Channel Identifier

The parser must extract a channel identifier from EXTINF entries.

Priority order:

1. tvg-id attribute
2. tvg-name attribute
3. display name after the comma

Example with tvg-id: `#EXTINF:-1 tvg-id="ard.de",Das Erste`

identifier = `ard.de`

Example without tvg-id: `#EXTINF:0 tvg-rec="0",First Channel HD`

identifier = `First Channel HD`

## Data Structure

All extracted identifiers must be stored in a set.

Example:

```json
{
 "ard.de",
 "zdf.de",
 "First Channel HD"
}
```

## Matching Rules

Identifiers must be normalized:

- trim whitespace
- convert to lowercase

Matching must be case-insensitive.