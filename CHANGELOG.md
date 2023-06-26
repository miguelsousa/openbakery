# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - YYYY-MM-DD

### Added

- `iso15008` extra (#21). To run the `iso15008` profile it's now necessary to install **openbakery** like so:

        python -m pip install -U 'openbakery[iso15008]'

- `shaping` subcommand and extra (#36).
- `fontwerk` extra (#37).
- `notofonts` extra (#37).

### Changed

- Removed the `check-` prefix from most subcommands (#35). As an example, now the command for running the Universal profile checks is,

        openbakery universal font.ttf

  instead of `openbakery check-universal font.ttf`.

- The shaping checks are no longer invoked by the Universal profile. To run them use the new `shaping` subcommand (#36).
- `com.google.fonts/check/fontvalidator`: The check emitted an ERROR if FontValidator isn't installed. It now emits a FAIL (#30).
- `com.google.fonts/check/valid_glyphnames`: The check now takes into account that OpenType-CFF2 fonts with `post` table format 3 contain no glyph names, and will yield SKIP (#38).
- `com.google.fonts/check/unique_glyphnames`: The check now takes into account that OpenType-CFF2 fonts with `post` table format 3 contain no glyph names, and will yield SKIP (#38).
- `com.google.fonts/check/STAT_in_statics`: The check now skips fonts that do not have a `STAT` table (#38).

### Fixed

- `com.google.fonts/check/interpolation_issues`: The check ERRORed when ran on CFF2 variable fonts. The check is now SKIPped for such fonts because it depends on the presence of the `gvar` table, which only apply to TrueType variable fonts (#28).
- `com.google.fonts/check/fontvalidator`: ERROR caused by attempting to run FontValidator before checking if it's installed (#30).
- `com.google.fonts/check/mandatory_glyphs`: Improved the check's resilience to edge cases that could result in ERRORs (#38).
- `-L`/`--list-checks` option that can be used with subcommands. Previously this option only worked if a path to an input file was also provided in the command line (#35).

## [0.1.0] - 2023-06-11

First release. This version is functionally equivalent to Font Bakery version 0.8.13, with two notable differences:

1. The `freetype-py` library is installed by default. Consequently, the `freetype` extra was removed since it's no longer necessary. A warning message will be displayed if the removed `freetype` extra is invoked during the installation of `openbakery`. This warning message can be safely disregarded.
2. To run `check-googlefonts` or `check-ufo-sources` checks it's necessary to install `openbakery` with the new extras named `googlefonts` or `ufo-sources`, respectively. Alternatively, you can use another new extra named `all`; this will install all the Python libraries required by all the checks.
