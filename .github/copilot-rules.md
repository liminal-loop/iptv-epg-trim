# Copilot Coding Rules

## Language

Python 3.12+
All code must use type hints.

## Distribution

- Runtime dependencies must be included in executable artifacts.
- Build separate artifacts per target OS/architecture.
- Windows and Linux/Raspberry Pi artifacts are built independently.
- Do not claim a single binary works across Windows and Linux.

## Code Style

- Prefer small functions
- Avoid deeply nested logic
- Use descriptive variable names

## Error Handling

Network errors must not crash the service.
If updates fail: previous valid EPG files must remain available.
Log all errors using Python logging module.

## Logging

Use Python logging module.

Log important events:

- playlist download
- epg download
- epg filtering start
- epg filtering finished
- number of channels processed
- number of programmes processed
- errors and warnings

## Performance Constraints

EPG files may exceed 500MB.

Requirements:

- streaming XML parsing (lxml.etree.iterparse)
- constant memory usage
- avoid building large lists in memory

## File Storage

Output files:

- data/epg.cleaned.xml  
- data/epg.cleaned.xml.gz

Ensure output directories exist before writing files.

## Matching Rules

Channel identifiers must be matched case-insensitively.
Use normalized playlist identifier → channel id mapping for programme filtering.

## Identifier Normalization

Playlist identifiers must be normalized before matching.

Normalization steps:

- trim whitespace
- convert to lowercase
- collapse multiple spaces

For each <channel>, normalize all <display-name> entries.
Keep the channel if any normalized display-name matches a normalized playlist identifier.

Example: " First Channel HD " becomes "first channel hd"