Examples for the shaping check
==============================

As well as finding structural issues with a font, openbakery contains a
check profile (`openbakery.profiles.shaping`) which ensures that the
font's OpenType layout rules behave as designed. To run this check, the
designer must supply one or more test suites, which are represented as
JSON files.

The `shaping/` directory contains a number of JSON files which
illustrate the expected format and syntax of these test suites. They are also documented with comments to explain the intent of tests and how they can be customised. Copying and modifying these files can form a basis for your own shaping test suite.

To run the shaping check, you need to tell openbakery where to find your test suite. This can be done by creating a openbakery configuration file in YAML format and specifying the directory where the JSON files can be found:

```
com.google.fonts/check/shaping:
    test_directory: examples/shaping
```

If this file is saved as (e.g.) `openbakery.yml`, then the shaping check can be run with the following command:

```
openbakery check-profile --config openbakery.yml openbakery.profiles.shaping Font.ttf
```

For best results, generate a HTML report using the `--html report.html` flag to openbakery, as this will contain SVG illustrations for failing tests.

For more information on the shaping check, see https://simoncozens.github.io/tdd-for-otl/
