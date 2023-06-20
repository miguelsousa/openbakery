# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - YYYY-MM-DD

### Added

- `iso15008` extra. To run the `check-iso15008` profile it's now necessary to install **openbakery** like so:

        python -m pip install -U 'openbakery[iso15008]'

### Fixed

- `com.google.fonts/check/interpolation_issues`: The check ERRORed when ran on CFF2 variable fonts. The check is now SKIPped for such fonts because it depends on the presence of the `gvar` table, which only apply to TrueType variable fonts (#28).

## [0.1.0] - 2023-06-11

First release. This version is functionally equivalent to Font Bakery version 0.8.13, with two notable differences:

1. The `freetype-py` library is installed by default. Consequently, the `freetype` extra was removed since it's no longer necessary. A warning message will be displayed if the removed `freetype` extra is invoked during the installation of `openbakery`. This warning message can be safely disregarded.
2. To run `check-googlefonts` or `check-ufo-sources` checks it's necessary to install `openbakery` with the new extras named `googlefonts` or `ufo-sources`, respectively. Alternatively, you can use another new extra named `all`; this will install all the Python libraries required by all the checks.
