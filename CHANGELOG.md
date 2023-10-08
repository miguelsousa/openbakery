# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - YYYY-MM-DD

### Added

- `iso15008` extra (https://github.com/miguelsousa/openbakery/pull/21). To run the `iso15008` profile it's now necessary to install **openbakery** like so:

        python -m pip install -U 'openbakery[iso15008]'

- `shaping` subcommand and extra (https://github.com/miguelsousa/openbakery/pull/36).
- `fontwerk` extra (https://github.com/miguelsousa/openbakery/pull/37).
- `notofonts` extra (https://github.com/miguelsousa/openbakery/pull/37).
- `com.thetypefounders/check/features_default_languagesystem`: Checks if a default languagesystem statement is present in feature files and warns if the compiler will not insert one automatically (https://github.com/fonttools/fontbakery/issues/4011).

### Changed

- Removed the `check-` prefix from most subcommands (https://github.com/miguelsousa/openbakery/pull/35). As an example, now the command for running the Universal profile checks is,

        openbakery universal font.ttf

  instead of `openbakery check-universal font.ttf`.

- The shaping checks are no longer invoked by the Universal profile. To run them use the new `shaping` subcommand (https://github.com/miguelsousa/openbakery/pull/36).
- `com.google.fonts/check/fontvalidator`: The check emitted an ERROR if FontValidator isn't installed. It now emits a FAIL (https://github.com/miguelsousa/openbakery/pull/30).
- `com.google.fonts/check/valid_glyphnames`: The check now takes into account that OpenType-CFF2 fonts with `post` table format 3 contain no glyph names, and will yield SKIP (https://github.com/miguelsousa/openbakery/pull/38).
- `com.google.fonts/check/unique_glyphnames`: The check now takes into account that OpenType-CFF2 fonts with `post` table format 3 contain no glyph names, and will yield SKIP (https://github.com/miguelsousa/openbakery/pull/38).
- `com.google.fonts/check/STAT_in_statics`: The check now skips fonts that do not have a `STAT` table (https://github.com/miguelsousa/openbakery/pull/38).
- `com.google.fonts/check/family_naming_recommendations`: Two validations of PostScript name were moved out of this check and into separate new checks `com.adobe.fonts/check/postscript_name_characters` and `com.adobe.fonts/postscript_name_hyphens` which yield FAIL (https://github.com/miguelsousa/openbakery/pull/62).
- `com.google.fonts/check/cjk_not_enough_glyphs`: This check is now only run when a font has CJK codepages or ranges declared in the `OS/2` table. Other CJK-related checks are run on fonts with a minimum of 150 CJK glyphs (https://github.com/fonttools/fontbakery/issues/3846).
- `com.google.fonts/check/family/panose_familytype` and `com.google.fonts/check/family/panose_proportion`: Failures have been downgraded to warnings (https://github.com/fonttools/fontbakery/issues/4192).

### Fixed

- `com.google.fonts/check/interpolation_issues`: The check ERRORed when ran on CFF2 variable fonts. The check is now SKIPped for such fonts because it depends on the presence of the `gvar` table, which only apply to TrueType variable fonts (https://github.com/miguelsousa/openbakery/issues/28).
- `com.google.fonts/check/fontvalidator`: ERROR caused by attempting to run FontValidator before checking if it's installed (https://github.com/miguelsousa/openbakery/issues/30).
- `com.google.fonts/check/mandatory_glyphs`: Improved the check's resilience to edge cases that could result in ERRORs (https://github.com/miguelsousa/openbakery/pull/38).
- `-L`/`--list-checks` option that can be used with subcommands. Previously this option only worked if a path to an input file was also provided in the command line (https://github.com/miguelsousa/openbakery/pull/35).
- Summary statistics on HTML reporter (https://github.com/fonttools/fontbakery/issues/3997).

## [0.1.0] - 2023-06-11

First release. This version is functionally equivalent to Font Bakery version 0.8.13, with two notable differences:

1. The `freetype-py` library is installed by default. Consequently, the `freetype` extra was removed since it's no longer necessary. A warning message will be displayed if the removed `freetype` extra is invoked during the installation of `openbakery`. This warning message can be safely disregarded.
2. To run `check-googlefonts` or `check-ufo-sources` checks it's necessary to install `openbakery` with the new extras named `googlefonts` or `ufo-sources`, respectively. Alternatively, you can use another new extra named `all`; this will install all the Python libraries required by all the checks.
