import os
import re

from packaging.version import VERSION_PATTERN

from openbakery.callable import check
from openbakery.constants import PlatformID, WindowsEncodingID
from openbakery.fonts_profile import profile_factory
from openbakery.glyphdata import desired_glyph_data
from openbakery.message import Message
from openbakery.profiles.layout import feature_tags
from openbakery.profiles.opentype import OPENTYPE_PROFILE_CHECKS
from openbakery.section import Section
from openbakery.status import PASS, FAIL, WARN, INFO, SKIP
from openbakery.utils import (
    bullet_list,
    get_font_glyph_data,
    get_glyph_name,
    glyph_has_ink,
    iterate_lookup_list_with_extensions,
    pretty_print_list,
)

re_version = re.compile(r"^\s*" + VERSION_PATTERN + r"\s*$", re.VERBOSE | re.IGNORECASE)

profile_imports = ((".", ("shared_conditions", "opentype")),)
profile = profile_factory(default_section=Section("Universal"))


SUPERFAMILY_CHECKS = [
    "com.google.fonts/check/superfamily/list",
    "com.google.fonts/check/superfamily/vertical_metrics",
]

UNIVERSAL_PROFILE_CHECKS = (
    OPENTYPE_PROFILE_CHECKS
    + SUPERFAMILY_CHECKS
    + [
        "com.google.fonts/check/name/trailing_spaces",
        "com.google.fonts/check/family/win_ascent_and_descent",
        "com.google.fonts/check/os2_metrics_match_hhea",
        "com.google.fonts/check/openbakery_version",
        "com.google.fonts/check/ttx_roundtrip",
        "com.google.fonts/check/family/single_directory",
        "com.google.fonts/check/mandatory_glyphs",
        "com.google.fonts/check/whitespace_glyphs",
        "com.google.fonts/check/whitespace_glyphnames",
        "com.google.fonts/check/whitespace_ink",
        "com.google.fonts/check/required_tables",
        "com.google.fonts/check/unwanted_tables",
        "com.google.fonts/check/valid_glyphnames",
        "com.google.fonts/check/unique_glyphnames",
        "com.google.fonts/check/family/vertical_metrics",
        "com.google.fonts/check/STAT_strings",
        "com.google.fonts/check/rupee",
        "com.google.fonts/check/unreachable_glyphs",
        "com.google.fonts/check/contour_count",
        "com.google.fonts/check/soft_hyphen",
        "com.google.fonts/check/cjk_chws_feature",
        "com.google.fonts/check/transformed_components",
        "com.google.fonts/check/gpos7",
        "com.google.fonts/check/ots",
        "com.adobe.fonts/check/freetype_rasterizer",
        "com.adobe.fonts/check/sfnt_version",
        "com.google.fonts/check/whitespace_widths",
        "com.google.fonts/check/interpolation_issues",
        "com.google.fonts/check/math_signs_width",
        "com.google.fonts/check/linegaps",
        "com.google.fonts/check/STAT_in_statics",
    ]
)


@check(
    id="com.google.fonts/check/name/trailing_spaces",
    proposal="https://github.com/googlefonts/fontbakery/issues/2417",
)
def com_google_fonts_check_name_trailing_spaces(ttFont):
    """Name table records must not have trailing spaces."""
    failed = False
    for name_record in ttFont["name"].names:
        name_string = name_record.toUnicode()
        if name_string != name_string.strip():
            failed = True
            name_key = tuple(
                [
                    name_record.platformID,
                    name_record.platEncID,
                    name_record.langID,
                    name_record.nameID,
                ]
            )
            shortened_str = name_record.toUnicode()
            if len(shortened_str) > 20:
                shortened_str = shortened_str[:10] + "[...]" + shortened_str[-10:]
            yield FAIL, Message(
                "trailing-space",
                f"Name table record with key = {name_key} has trailing spaces"
                f" that must be removed: '{shortened_str}'",
            )
    if not failed:
        yield PASS, ("No trailing spaces on name table entries.")


@check(
    id="com.google.fonts/check/family/win_ascent_and_descent",
    conditions=["vmetrics", "not is_cjk_font"],
    rationale="""
        A font's winAscent and winDescent values should be greater than or equal to
        the head table's yMax, abs(yMin) values. If they are less than these values,
        clipping can occur on Windows platforms
        (https://github.com/RedHatBrand/Overpass/issues/33).

        If the font includes tall/deep writing systems such as Arabic or Devanagari,
        the winAscent and winDescent can be greater than the yMax and absolute yMin
        values to accommodate vowel marks.

        When the 'win' Metrics are significantly greater than the UPM, the linespacing
        can appear too loose. To counteract this, enabling the OS/2 fsSelection
        bit 7 (Use_Typo_Metrics), will force Windows to use the OS/2 'typo' values
        instead. This means the font developer can control the linespacing with
        the 'typo' values, whilst avoiding clipping by setting the 'win' values to
        values greater than the yMax and absolute yMin.
    """,
    proposal="legacy:check/040",
)
def com_google_fonts_check_family_win_ascent_and_descent(ttFont, vmetrics):
    """Checking OS/2 usWinAscent & usWinDescent."""

    # NOTE:
    # This check works on a single font file as well as on a group of font files.
    # Even though one of this check's inputs is 'ttFont' (whereas other family-wide
    # checks use 'ttFonts') the other input parameter, 'vmetrics', will collect vertical
    # metrics values for all the font files provided in the command line. This means
    # that running the check may yield more or less results depending on the set of font
    # files that is provided in the command line. This behaviour is NOT a bug.
    # For example, compare the results of these two commands:
    #   openbakery universal -c win_ascent_and_descent data/test/mada/Mada-Regular.ttf
    #   openbakery universal -c win_ascent_and_descent data/test/mada/*.ttf
    #
    # The second command will yield more FAIL results for each font. This happens
    # because the check does a family-wide validation of the vertical metrics, instead
    # of a single font validation.

    if "OS/2" not in ttFont:
        yield FAIL, Message("lacks-OS/2", "Font file lacks OS/2 table")
        return

    failed = False
    os2_table = ttFont["OS/2"]
    win_ascent = os2_table.usWinAscent
    win_descent = os2_table.usWinDescent
    y_max = vmetrics["ymax"]
    y_min = vmetrics["ymin"]

    # OS/2 usWinAscent:
    if win_ascent < y_max:
        failed = True
        yield FAIL, Message(
            "ascent",
            f"OS/2.usWinAscent value should be equal or greater than {y_max},"
            f" but got {win_ascent} instead",
        )
    if win_ascent > y_max * 2:
        failed = True
        yield FAIL, Message(
            "ascent",
            f"OS/2.usWinAscent value {win_ascent} is too large."
            f" It should be less than double the yMax. Current yMax value is {y_max}",
        )
    # OS/2 usWinDescent:
    if win_descent < abs(y_min):
        failed = True
        yield FAIL, Message(
            "descent",
            f"OS/2.usWinDescent value should be equal or greater than {abs(y_min)},"
            f" but got {win_descent} instead",
        )

    if win_descent > abs(y_min) * 2:
        failed = True
        yield FAIL, Message(
            "descent",
            f"OS/2.usWinDescent value {win_descent} is too large."
            " It should be less than double the yMin."
            f" Current absolute yMin value is {abs(y_min)}",
        )
    if not failed:
        yield PASS, "OS/2 usWinAscent & usWinDescent values look good!"


@check(
    id="com.google.fonts/check/os2_metrics_match_hhea",
    conditions=["not is_cjk_font"],
    rationale="""
        OS/2 and hhea vertical metric values should match. This will produce the
        same linespacing on Mac, GNU+Linux and Windows.

        - Mac OS X uses the hhea values.⏎
        - Windows uses OS/2 or Win, depending on the OS or fsSelection bit value.

        When OS/2 and hhea vertical metrics match, the same linespacing results on
        macOS, GNU+Linux and Windows. Unfortunately as of 2018, Google Fonts
        has released many fonts with vertical metrics that don't match in this way.
        When we fix this issue in these existing families, we will create a visible
        change in line/paragraph layout for either Windows or macOS users,
        which will upset some of them.

        But we have a duty to fix broken stuff, and inconsistent paragraph layout
        is unacceptably broken when it is possible to avoid it.

        If users complain and prefer the old broken version, they have the freedom
        to take care of their own situation.
    """,
    proposal="legacy:check/042",
)
def com_google_fonts_check_os2_metrics_match_hhea(ttFont):
    """Checking OS/2 Metrics match hhea Metrics."""

    filename = os.path.basename(ttFont.reader.file.name)

    # Check both OS/2 and hhea are present.
    missing_tables = False

    required = ["OS/2", "hhea"]
    for key in required:
        if key not in ttFont:
            missing_tables = True
            yield FAIL, Message(f"lacks-{key}", f"{filename} lacks a '{key}' table.")

    if missing_tables:
        return

    # OS/2 sTypoAscender and sTypoDescender match hhea ascent and descent
    if ttFont["OS/2"].sTypoAscender != ttFont["hhea"].ascent:
        yield FAIL, Message(
            "ascender",
            f"OS/2 sTypoAscender ({ttFont['OS/2'].sTypoAscender})"
            f" and hhea ascent ({ttFont['hhea'].ascent}) must be equal.",
        )
    elif ttFont["OS/2"].sTypoDescender != ttFont["hhea"].descent:
        yield FAIL, Message(
            "descender",
            f"OS/2 sTypoDescender ({ttFont['OS/2'].sTypoDescender})"
            f" and hhea descent ({ttFont['hhea'].descent}) must be equal.",
        )
    elif ttFont["OS/2"].sTypoLineGap != ttFont["hhea"].lineGap:
        yield FAIL, Message(
            "lineGap",
            f"OS/2 sTypoLineGap ({ttFont['OS/2'].sTypoLineGap})"
            f" and hhea lineGap ({ttFont['hhea'].lineGap}) must be equal.",
        )
    else:
        yield PASS, "OS/2.sTypoAscender/Descender values match hhea.ascent/descent."


@check(
    id="com.google.fonts/check/family/single_directory",
    rationale="""
        If the set of font files passed in the command line is not all in the
        same directory, then we warn the user since the tool will interpret the
        set of files as belonging to a single family (and it is unlikely that
        the user would store the files from a single family spreaded
        in several separate directories).
    """,
    proposal="legacy:check/002",
)
def com_google_fonts_check_family_single_directory(fonts):
    """Checking all files are in the same directory."""

    directories = []
    for target_file in fonts:
        directory = os.path.dirname(target_file)
        if directory not in directories:
            directories.append(directory)

    if len(directories) == 1:
        yield PASS, "All files are in the same directory."
    else:
        yield FAIL, Message(
            "single-directory",
            "Not all fonts passed in the command line are in the"
            " same directory. This may lead to bad results as the tool"
            " will interpret all font files as belonging to a single"
            f" font family. The detected directories are: {directories}",
        )


@check(id="com.google.fonts/check/ots", proposal="legacy:check/036")
def com_google_fonts_check_ots(font):
    """Checking with ots-sanitize."""
    import ots

    try:
        process = ots.sanitize(font, check=True, capture_output=True)

    except ots.CalledProcessError as e:
        yield FAIL, Message(
            "ots-sanitize-error",
            f"ots-sanitize returned an error code ({e.returncode})."
            f" Output follows:\n\n{e.stderr.decode()}{e.stdout.decode()}",
        )
    else:
        if process.stderr:
            yield WARN, Message(
                "ots-sanitize-warn",
                "ots-sanitize passed this file, however warnings were printed:\n\n"
                f"{process.stderr.decode()}",
            )
        else:
            yield PASS, "ots-sanitize passed this file"


def _parse_package_version(version_string: str) -> dict:
    """
    Parses a Python package version string.
    """
    match = re_version.search(version_string)
    release = match.group("release")
    pre_rel = match.group("pre")
    post_rel = match.group("post")
    dev_rel = match.group("dev")

    # Split MAJOR.MINOR.PATCH numbers, and convert them to integers
    major, minor, patch = map(int, release.split("."))
    version_parts = {
        "major": major,
        "minor": minor,
        "patch": patch,
    }
    # Add the release-kind booleans
    version_parts["pre"] = pre_rel is not None
    version_parts["post"] = post_rel is not None
    version_parts["dev"] = dev_rel is not None

    return version_parts


def is_up_to_date(installed_str, latest_str):
    installed_dict = _parse_package_version(installed_str)
    latest_dict = _parse_package_version(latest_str)

    installed_rel = [*installed_dict.values()][:3]
    latest_rel = [*latest_dict.values()][:3]

    # Compare MAJOR.MINOR.PATCH parts
    for inst_version, last_version in zip(installed_rel, latest_rel):
        if inst_version > last_version:
            return True
        if inst_version < last_version:
            return False

    # All MAJOR.MINOR.PATCH integers are the same between 'installed' and 'latest';
    # therefore OpenBakery is up-to-date, unless
    # a) a pre-release is installed or FB is installed in development mode (in which
    #    case the version number installed must be higher), or
    # b) a post-release has been issued.

    installed_is_pre_or_dev_rel = installed_dict.get("pre") or installed_dict.get("dev")
    latest_is_post_rel = latest_dict.get("post")

    return not (installed_is_pre_or_dev_rel or latest_is_post_rel)


@check(
    id="com.google.fonts/check/openbakery_version",
    rationale="""
        Running old versions of OpenBakery can lead to a poor report which may
        include false WARNs and FAILs due do bugs, as well as outdated
        quality assurance criteria.

        Older versions will also not report problems that are detected by new checks
        added to the tool in more recent updates.
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/2093",
)
def com_google_fonts_check_openbakery_version(font, config):
    """Do we have the latest version of OpenBakery installed?"""
    import requests
    import pip_api

    try:
        response = requests.get(
            "https://pypi.org/pypi/openbakery/json", timeout=config.get("timeout")
        )

    except requests.exceptions.ConnectionError as err:
        return FAIL, Message(
            "connection-error",
            f"Request to PyPI.org failed with this message:\n{err}",
        )

    status_code = response.status_code
    if status_code != 200:
        return FAIL, Message(
            f"unsuccessful-request-{status_code}",
            f"Request to PyPI.org was not successful:\n{response.content}",
        )

    latest = response.json()["info"]["version"]
    installed = str(pip_api.installed_distributions()["openbakery"].version)

    if not is_up_to_date(installed, latest):
        return FAIL, Message(
            "outdated-openbakery",
            f"Current OpenBakery version is {installed},"
            f" while a newer {latest} is already available."
            f" Please upgrade it with 'pip install -U openbakery'",
        )
    else:
        return PASS, "OpenBakery is up-to-date."


@check(
    id="com.google.fonts/check/mandatory_glyphs",
    rationale="""
        The OpenType specification v1.8.2 recommends that the first glyph is the
        '.notdef' glyph without a codepoint assigned and with a drawing.

        https://docs.microsoft.com/en-us/typography/opentype/spec/recom#glyph-0-the-notdef-glyph

        Pre-v1.8, it was recommended that fonts should also contain 'space', 'CR'
        and '.null' glyphs. This might have been relevant for MacOS 9 applications.
    """,
    proposal="legacy:check/046",
)
def com_google_fonts_check_mandatory_glyphs(ttFont):
    """Font contains '.notdef' as its first glyph?"""
    passed = True
    NOTDEF = ".notdef"
    glyph_order = ttFont.getGlyphOrder()

    if NOTDEF not in glyph_order or len(glyph_order) == 0:
        yield WARN, Message(
            "notdef-not-found", f"Font should contain the {NOTDEF!r} glyph."
        )
        # The font doesn't even have the notdef. There's no point in testing further.
        return

    if glyph_order[0] != NOTDEF:
        passed = False
        yield WARN, Message(
            "notdef-not-first", f"The {NOTDEF!r} should be the font's first glyph."
        )

    cmap = ttFont.getBestCmap()  # e.g. {65: 'A', 66: 'B', 67: 'C'} or None
    if cmap and NOTDEF in cmap.values():
        passed = False
        rev_cmap = {name: val for val, name in reversed(sorted(cmap.items()))}
        yield WARN, Message(
            "notdef-has-codepoint",
            f"The {NOTDEF!r} glyph should not have a Unicode codepoint value assigned,"
            f" but has 0x{rev_cmap[NOTDEF]:04X}.",
        )

    if not glyph_has_ink(ttFont, NOTDEF):
        passed = False
        yield WARN, Message(
            "notdef-is-blank",
            f"The {NOTDEF!r} glyph should contain a drawing, but it is blank.",
        )

    if passed:
        yield PASS, "OK"


@check(id="com.google.fonts/check/whitespace_glyphs", proposal="legacy:check/047")
def com_google_fonts_check_whitespace_glyphs(ttFont, missing_whitespace_chars):
    """Font contains glyphs for whitespace characters?"""
    failed = False
    for wsc in missing_whitespace_chars:
        failed = True
        yield FAIL, Message(
            f"missing-whitespace-glyph-{wsc}",
            f"Whitespace glyph missing for codepoint {wsc}.",
        )

    if not failed:
        yield PASS, "Font contains glyphs for whitespace characters."


@check(
    id="com.google.fonts/check/whitespace_glyphnames",
    conditions=["not missing_whitespace_chars"],
    rationale="""
        This check enforces adherence to recommended whitespace
        (codepoints 0020 and 00A0) glyph names according to the Adobe Glyph List.
    """,
    proposal="legacy:check/048",
)
def com_google_fonts_check_whitespace_glyphnames(ttFont):
    """Font has **proper** whitespace glyph names?"""
    # AGL recommended names, according to Adobe Glyph List for new fonts:
    AGL_RECOMMENDED_0020 = {"space"}
    AGL_RECOMMENDED_00A0 = {"uni00A0", "space"}
    # "space" is in this set because some fonts use the same glyph for
    # U+0020 and U+00A0. Including it here also removes a warning
    # when U+0020 is wrong, but U+00A0 is okay.

    # AGL compliant names, but not recommended for new fonts:
    AGL_COMPLIANT_BUT_NOT_RECOMMENDED_0020 = {"uni0020", "u0020", "u00020", "u000020"}
    AGL_COMPLIANT_BUT_NOT_RECOMMENDED_00A0 = {
        "nonbreakingspace",
        "nbspace",
        "u00A0",
        "u000A0",
        "u0000A0",
    }

    if ttFont["post"].formatType == 3.0:
        yield SKIP, "Font has version 3 post table."
    else:
        passed = True

        space = get_glyph_name(ttFont, 0x0020)
        if space in AGL_RECOMMENDED_0020:
            pass

        elif space in AGL_COMPLIANT_BUT_NOT_RECOMMENDED_0020:
            passed = False
            yield WARN, Message(
                "not-recommended-0020",
                f'Glyph 0x0020 is called "{space}": Change to "space"',
            )
        else:
            passed = False
            yield FAIL, Message(
                "non-compliant-0020",
                f'Glyph 0x0020 is called "{space}": Change to "space"',
            )

        nbsp = get_glyph_name(ttFont, 0x00A0)
        if nbsp == space:
            # This is OK.
            # Some fonts use the same glyph for both space and nbsp.
            pass

        elif nbsp in AGL_RECOMMENDED_00A0:
            pass

        elif nbsp in AGL_COMPLIANT_BUT_NOT_RECOMMENDED_00A0:
            passed = False
            yield WARN, Message(
                "not-recommended-00a0",
                f'Glyph 0x00A0 is called "{nbsp}": Change to "uni00A0"',
            )
        else:
            passed = False
            yield FAIL, Message(
                "non-compliant-00a0",
                f'Glyph 0x00A0 is called "{nbsp}": Change to "uni00A0"',
            )

        if passed:
            yield PASS, "Font has **AGL recommended** names for whitespace glyphs."


@check(id="com.google.fonts/check/whitespace_ink", proposal="legacy:check/049")
def com_google_fonts_check_whitespace_ink(ttFont):
    """Whitespace glyphs have ink?"""
    # This checks that certain glyphs are empty.
    # Some, but not all, are Unicode whitespace.

    # code-points for all Unicode whitespace chars
    # (according to Unicode 11.0 property list):
    WHITESPACE_CHARACTERS = {
        0x0009,
        0x000A,
        0x000B,
        0x000C,
        0x000D,
        0x0020,
        0x0085,
        0x00A0,
        0x1680,
        0x2000,
        0x2001,
        0x2002,
        0x2003,
        0x2004,
        0x2005,
        0x2006,
        0x2007,
        0x2008,
        0x2009,
        0x200A,
        0x2028,
        0x2029,
        0x202F,
        0x205F,
        0x3000,
    }

    # Code-points that do not have whitespace property, but
    # should not have a drawing.
    EXTRA_NON_DRAWING = {0x180E, 0x200B, 0x2060, 0xFEFF}

    # Make the set of non drawing characters.
    # OGHAM SPACE MARK U+1680 is removed as it is
    # a whitespace that should have a drawing.
    NON_DRAWING = (WHITESPACE_CHARACTERS | EXTRA_NON_DRAWING) - {0x1680}

    passed = True
    for codepoint in sorted(NON_DRAWING):
        g = get_glyph_name(ttFont, codepoint)
        if g is not None and glyph_has_ink(ttFont, g):
            passed = False
            yield FAIL, Message(
                "has-ink",
                f"Glyph '{g}' has ink. It needs to be replaced by an empty glyph.",
            )
    if passed:
        yield PASS, "There is no whitespace glyph with ink."


@check(
    id="com.google.fonts/check/required_tables",
    conditions=["ttFont"],
    rationale="""
        According to the OpenType spec
        https://docs.microsoft.com/en-us/typography/opentype/spec/otff#required-tables

        Whether TrueType or CFF outlines are used in an OpenType font, the following
        tables are required for the font to function correctly:

        - cmap (Character to glyph mapping)⏎
        - head (Font header)⏎
        - hhea (Horizontal header)⏎
        - hmtx (Horizontal metrics)⏎
        - maxp (Maximum profile)⏎
        - name (Naming table)⏎
        - OS/2 (OS/2 and Windows specific metrics)⏎
        - post (PostScript information)

        The spec also documents that variable fonts require the following table:

        - STAT (Style attributes)

        Depending on the typeface and coverage of a font, certain tables are
        recommended for optimum quality.

        For example:⏎
        - the performance of a non-linear font is improved if the VDMX, LTSH,
          and hdmx tables are present.⏎
        - Non-monospaced Latin fonts should have a kern table.⏎
        - A gasp table is necessary if a designer wants to influence the sizes
          at which grayscaling is used under Windows. Etc.
    """,
    proposal="legacy:check/052",
)
def com_google_fonts_check_required_tables(ttFont, config, is_variable_font):
    """Font contains all required tables?"""
    REQUIRED_TABLES = ["cmap", "head", "hhea", "hmtx", "maxp", "name", "OS/2", "post"]

    OPTIONAL_TABLES = [
        "cvt ",
        "fpgm",
        "loca",
        "prep",
        "VORG",
        "EBDT",
        "EBLC",
        "EBSC",
        "BASE",
        "GPOS",
        "GSUB",
        "JSTF",
        "gasp",
        "hdmx",
        "LTSH",
        "PCLT",
        "VDMX",
        "vhea",
        "vmtx",
        "kern",
    ]

    # See https://github.com/googlefonts/fontbakery/issues/617
    #
    # We should collect the rationale behind the need for each of the
    # required tables above. Perhaps split it into individual checks
    # with the correspondent rationales for each subset of required tables.
    #
    # com.google.fonts/check/kern_table is a good example of a separate
    # check for a specific table providing a detailed description of
    # the rationale behind it.

    font_tables = ttFont.keys()

    optional_tables = [opt for opt in OPTIONAL_TABLES if opt in font_tables]
    if optional_tables:
        yield INFO, Message(
            "optional-tables",
            "This font contains the following optional tables:\n\n"
            f"{bullet_list(config, optional_tables)}",
        )

    if is_variable_font:
        # According to https://github.com/googlefonts/fontbakery/issues/1671
        # STAT table is required on WebKit on MacOS 10.12 for variable fonts.
        REQUIRED_TABLES.append("STAT")

    missing_tables = [req for req in REQUIRED_TABLES if req not in font_tables]

    if ttFont.sfntVersion == "OTTO" and (
        "CFF " not in font_tables and "CFF2" not in font_tables
    ):
        if "fvar" in font_tables:
            missing_tables.append("CFF2")
        else:
            missing_tables.append("CFF ")

    elif ttFont.sfntVersion == "\x00\x01\x00\x00" and "glyf" not in font_tables:
        missing_tables.append("glyf")

    if missing_tables:
        yield FAIL, Message(
            "required-tables",
            "This font is missing the following required tables:\n\n"
            f"{bullet_list(config, missing_tables)}",
        )
    else:
        yield PASS, "Font contains all required tables."


@check(
    id="com.google.fonts/check/unwanted_tables",
    rationale="""
        Some font editors store source data in their own SFNT tables, and these
        can sometimes sneak into final release files, which should only have
        OpenType spec tables.
    """,
    proposal="legacy:check/053",
)
def com_google_fonts_check_unwanted_tables(ttFont):
    """Are there unwanted tables?"""
    UNWANTED_TABLES = {
        "FFTM": "Table contains redundant FontForge timestamp info",
        "TTFA": "Redundant TTFAutohint table",
        "TSI0": "Table contains data only used in VTT",
        "TSI1": "Table contains data only used in VTT",
        "TSI2": "Table contains data only used in VTT",
        "TSI3": "Table contains data only used in VTT",
        "TSI5": "Table contains data only used in VTT",
        "prop": (
            "Table used on AAT, Apple's OS X specific technology."
            " Although Harfbuzz now has optional AAT support,"
            " new fonts should not be using that."
        ),
    }
    unwanted_tables_found = []
    unwanted_tables_tags = set(UNWANTED_TABLES)
    for table in ttFont.keys():
        if table in unwanted_tables_tags:
            info = UNWANTED_TABLES[table]
            unwanted_tables_found.append(f"* {table} - {info}\n")

    if unwanted_tables_found:
        yield FAIL, Message(
            "unwanted-tables",
            "The following unwanted font tables were found:\n\n"
            f"{''.join(unwanted_tables_found)}\nThey can be removed with"
            " the 'fix-unwanted-tables' script provided by gftools.",
        )
    else:
        yield PASS, "There are no unwanted tables."


@check(
    id="com.google.fonts/check/STAT_strings",
    conditions=["has_STAT_table"],
    rationale="""
        On the STAT table, the "Italic" keyword must not be used on AxisValues
        for variation axes other than 'ital'.
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/2863",
)
def com_google_fonts_check_STAT_strings(ttFont):
    """Check correctness of STAT table strings"""
    passed = True
    ital_axis_index = None
    for index, axis in enumerate(ttFont["STAT"].table.DesignAxisRecord.Axis):
        if axis.AxisTag == "ital":
            ital_axis_index = index
            break

    nameIDs = set()
    if ttFont["STAT"].table.AxisValueArray:
        for value in ttFont["STAT"].table.AxisValueArray.AxisValue:
            if hasattr(value, "AxisIndex"):
                if value.AxisIndex != ital_axis_index:
                    nameIDs.add(value.ValueNameID)

            if hasattr(value, "AxisValueRecord"):
                for record in value.AxisValueRecord:
                    if record.AxisIndex != ital_axis_index:
                        nameIDs.add(value.ValueNameID)

    bad_values = set()
    for name in ttFont["name"].names:
        if name.nameID in nameIDs and "italic" in name.toUnicode().lower():
            passed = False
            bad_values.add(f"nameID {name.nameID}: {name.toUnicode()}")

    if bad_values:
        yield FAIL, Message(
            "bad-italic",
            "The following AxisValue entries on the STAT table"
            f' should not contain "Italic":\n{sorted(bad_values)}',
        )

    if passed:
        yield PASS, "Looks good!"


@check(
    id="com.google.fonts/check/valid_glyphnames",
    rationale="""
        Microsoft's recommendations for OpenType Fonts states the following:

        'NOTE: The PostScript glyph name must be no longer than 31 characters,
        include only uppercase or lowercase English letters, European digits,
        the period or the underscore, i.e. from the set [A-Za-z0-9_.] and
        should start with a letter, except the special glyph name ".notdef"
        which starts with a period.'

        https://docs.microsoft.com/en-us/typography/opentype/spec/recom#post-table


        In practice, though, particularly in modern environments, glyph names
        can be as long as 63 characters.

        According to the "Adobe Glyph List Specification" available at:

        https://github.com/adobe-type-tools/agl-specification
    """,
    proposal=[
        "legacy:check/058",
        # issue #2832 increased the limit to 63 chars
        "https://github.com/googlefonts/fontbakery/issues/2832",
    ],
)
def com_google_fonts_check_valid_glyphnames(ttFont, config):
    """Glyph names are all valid?"""
    if (
        ttFont.sfntVersion == "\x00\x01\x00\x00"
        and ttFont.get("post")
        and ttFont["post"].formatType == 3
    ):
        yield SKIP, (
            "TrueType fonts with a format 3 post table contain no glyph names."
        )
    elif (
        ttFont.sfntVersion == "OTTO"
        and ttFont.get("CFF2")
        and ttFont.get("post")
        and ttFont["post"].formatType == 3
    ):
        yield SKIP, (
            "OpenType-CFF2 fonts with a format 3 post table contain no glyph names."
        )
    else:
        bad_names = set()
        warn_names = set()
        for glyphName in ttFont.getGlyphOrder():
            # The first two names are explicit exceptions in the glyph naming rules.
            # The third was added in https://github.com/googlefonts/fontbakery/pull/2003
            if glyphName.startswith((".null", ".notdef", ".ttfautohint")):
                continue
            if not re.match(r"^(?![.0-9])[a-zA-Z._0-9]{1,63}$", glyphName):
                bad_names.add(glyphName)
            if len(glyphName) > 31 and len(glyphName) <= 63:
                warn_names.add(glyphName)

        if not bad_names:
            if not warn_names:
                yield PASS, "Glyph names are all valid."
            else:
                yield WARN, Message(
                    "legacy-long-names",
                    "The following glyph names may be too long for some legacy systems"
                    " which may expect a maximum 31-characters length limit:\n"
                    f"{pretty_print_list(config, sorted(warn_names))}",
                )
        else:
            bad_names_list = pretty_print_list(config, sorted(bad_names))
            yield FAIL, Message(
                "found-invalid-names",
                "The following glyph names do not comply"
                f" with naming conventions: {bad_names_list}\n\n"
                " A glyph name must be entirely comprised of characters"
                " from the following set: A-Z a-z 0-9 .(period) _(underscore)."
                " A glyph name must not start with a digit or period."
                ' There are a few exceptions such as the special glyph ".notdef".'
                ' The glyph names "twocents", "a1", and "_" are all valid,'
                ' while "2cents" and ".twocents" are not.',
            )


@check(
    id="com.google.fonts/check/unique_glyphnames",
    rationale="""
        Duplicate glyph names prevent font installation on Mac OS X.
    """,
    proposal="legacy:check/059",
    misc_metadata={"affects": [("Mac", "unspecified")]},
)
def com_google_fonts_check_unique_glyphnames(ttFont):
    """Font contains unique glyph names?"""
    if (
        ttFont.sfntVersion == "\x00\x01\x00\x00"
        and ttFont.get("post")
        and ttFont["post"].formatType == 3
    ):
        yield SKIP, (
            "TrueType fonts with a format 3 post table contain no glyph names."
        )
    elif (
        ttFont.sfntVersion == "OTTO"
        and ttFont.get("CFF2")
        and ttFont.get("post")
        and ttFont["post"].formatType == 3
    ):
        yield SKIP, (
            "OpenType-CFF2 fonts with a format 3 post table contain no glyph names."
        )
    else:
        glyph_names = set()
        dup_glyph_names = set()
        for gname in ttFont.getGlyphOrder():
            # On font load, Fonttools adds #1, #2, ... suffixes to duplicate glyph names
            glyph_name = re.sub(r"#\w+", "", gname)
            if glyph_name in glyph_names:
                dup_glyph_names.add(glyph_name)
            else:
                glyph_names.add(glyph_name)

        if not dup_glyph_names:
            yield PASS, "Glyph names are all unique."
        else:
            yield FAIL, Message(
                "duplicated-glyph-names",
                f"These glyph names occur more than once: {sorted(dup_glyph_names)}",
            )


@check(
    id="com.google.fonts/check/ttx_roundtrip",
    conditions=["not vtt_talk_sources"],
    proposal="https://github.com/googlefonts/fontbakery/issues/1763",
)
def com_google_fonts_check_ttx_roundtrip(font):
    """Checking with fontTools.ttx"""
    from fontTools import ttx
    import sys
    import tempfile

    ttFont = ttx.TTFont(font)
    failed = False
    fd, xml_file = tempfile.mkstemp()
    os.close(fd)

    class TTXLogger:
        msgs = []

        def __init__(self):
            self.original_stderr = sys.stderr
            self.original_stdout = sys.stdout
            sys.stderr = self
            sys.stdout = self

        def write(self, data):
            if data not in self.msgs:
                self.msgs.append(data)

        def restore(self):
            sys.stderr = self.original_stderr
            sys.stdout = self.original_stdout

    from xml.parsers.expat import ExpatError

    try:
        logger = TTXLogger()
        ttFont.saveXML(xml_file)
        export_error_msgs = logger.msgs

        if export_error_msgs:
            failed = True
            yield INFO, (
                "While converting TTF into an XML file,"
                " ttx emited the messages listed below."
            )
            for msg in export_error_msgs:
                yield FAIL, msg.strip()

        f = ttx.TTFont()
        f.importXML(xml_file)
        import_error_msgs = [msg for msg in logger.msgs if msg not in export_error_msgs]

        if len(import_error_msgs):
            failed = True
            yield INFO, (
                "While importing an XML file and converting it back to TTF,"
                " ttx emited the messages listed below."
            )
            for msg in import_error_msgs:
                yield FAIL, msg.strip()
        logger.restore()
    except ExpatError as e:
        failed = True
        yield FAIL, (
            "TTX had some problem parsing the generated XML file."
            " This most likely mean there's some problem in the font."
            " Please inspect the output of ttx in order to find more"
            " on what went wrong. A common problem is the presence of"
            " control characteres outside the accepted character range"
            " as defined in the XML spec. FontTools has got a bug which"
            " causes TTX to generate corrupt XML files in those cases."
            " So, check the entries of the name table and remove any control"
            " chars that you find there. The full ttx error message was:\n"
            f"======\n{e}\n======"
        )

    if not failed:
        yield PASS, "Hey! It all looks good!"

    # and then we need to cleanup our mess...
    if os.path.exists(xml_file):
        os.remove(xml_file)


@check(
    id="com.google.fonts/check/family/vertical_metrics",
    rationale="""
        We want all fonts within a family to have the same vertical metrics so
        their line spacing is consistent across the family.
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/1487",
)
def com_google_fonts_check_family_vertical_metrics(ttFonts):
    """Each font in a family must have the same set of vertical metrics values."""
    failed = []
    vmetrics = {
        "sTypoAscender": {},
        "sTypoDescender": {},
        "sTypoLineGap": {},
        "usWinAscent": {},
        "usWinDescent": {},
        "ascent": {},
        "descent": {},
        "lineGap": {},
    }

    missing_tables = False
    for ttFont in ttFonts:
        filename = os.path.basename(ttFont.reader.file.name)
        if "OS/2" not in ttFont:
            missing_tables = True
            yield FAIL, Message("lacks-OS/2", f"{filename} lacks an 'OS/2' table.")
            continue

        if "hhea" not in ttFont:
            missing_tables = True
            yield FAIL, Message("lacks-hhea", f"{filename} lacks a 'hhea' table.")
            continue

        full_font_name = ttFont["name"].getBestFullName()
        vmetrics["sTypoAscender"][full_font_name] = ttFont["OS/2"].sTypoAscender
        vmetrics["sTypoDescender"][full_font_name] = ttFont["OS/2"].sTypoDescender
        vmetrics["sTypoLineGap"][full_font_name] = ttFont["OS/2"].sTypoLineGap
        vmetrics["usWinAscent"][full_font_name] = ttFont["OS/2"].usWinAscent
        vmetrics["usWinDescent"][full_font_name] = ttFont["OS/2"].usWinDescent
        vmetrics["ascent"][full_font_name] = ttFont["hhea"].ascent
        vmetrics["descent"][full_font_name] = ttFont["hhea"].descent
        vmetrics["lineGap"][full_font_name] = ttFont["hhea"].lineGap

    if not missing_tables:
        # It is important to first ensure all font files have OS/2 and hhea tables
        # before performing the rest of the check routine.

        for k, v in vmetrics.items():
            metric_vals = set(vmetrics[k].values())
            if len(metric_vals) != 1:
                failed.append(k)

        if failed:
            for k in failed:
                s = ["{}: {}".format(k, v) for k, v in vmetrics[k].items()]
                s = "\n".join(s)
                yield FAIL, Message(
                    f"{k}-mismatch", f"{k} is not the same across the family:\n{s}"
                )
        else:
            yield PASS, "Vertical metrics are the same across the family."


@check(
    id="com.google.fonts/check/superfamily/list",
    rationale="""
        This is a merely informative check that lists all sibling families
        detected by openbakery.

        Only the fontfiles in these directories will be considered in
        superfamily-level checks.
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/1487",
)
def com_google_fonts_check_superfamily_list(superfamily):
    """List all superfamily filepaths"""
    for family in superfamily:
        yield INFO, Message("family-path", os.path.split(family[0])[0])


@check(
    id="com.google.fonts/check/superfamily/vertical_metrics",
    rationale="""
        We may want all fonts within a super-family (all sibling families) to have
        the same vertical metrics so their line spacing is consistent
        across the super-family.

        This is an experimental extended version of
        com.google.fonts/check/family/vertical_metrics and for now it will only
        result in WARNs.
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/1487",
)
def com_google_fonts_check_superfamily_vertical_metrics(superfamily_ttFonts):
    """
    Each font in set of sibling families must have the same set of vertical metrics
    values.
    """
    if len(superfamily_ttFonts) < 2:
        yield SKIP, "Sibling families were not detected."
        return

    warn = []
    vmetrics = {
        "sTypoAscender": {},
        "sTypoDescender": {},
        "sTypoLineGap": {},
        "usWinAscent": {},
        "usWinDescent": {},
        "ascent": {},
        "descent": {},
        "lineGap": {},
    }

    for family_ttFonts in superfamily_ttFonts:
        for ttFont in family_ttFonts:
            full_font_name = ttFont["name"].getBestFullName()
            vmetrics["sTypoAscender"][full_font_name] = ttFont["OS/2"].sTypoAscender
            vmetrics["sTypoDescender"][full_font_name] = ttFont["OS/2"].sTypoDescender
            vmetrics["sTypoLineGap"][full_font_name] = ttFont["OS/2"].sTypoLineGap
            vmetrics["usWinAscent"][full_font_name] = ttFont["OS/2"].usWinAscent
            vmetrics["usWinDescent"][full_font_name] = ttFont["OS/2"].usWinDescent
            vmetrics["ascent"][full_font_name] = ttFont["hhea"].ascent
            vmetrics["descent"][full_font_name] = ttFont["hhea"].descent
            vmetrics["lineGap"][full_font_name] = ttFont["hhea"].lineGap

    for k, v in vmetrics.items():
        metric_vals = set(vmetrics[k].values())
        if len(metric_vals) != 1:
            warn.append(k)

    if warn:
        for k in warn:
            s = ["{}: {}".format(k, v) for k, v in vmetrics[k].items()]
            s = "\n".join(s)
            yield WARN, Message(
                "superfamily-vertical-metrics",
                f"{k} is not the same across the super-family:\n{s}",
            )
    else:
        yield PASS, "Vertical metrics are the same across the super-family."


@check(
    id="com.google.fonts/check/rupee",
    rationale="""
        Per Bureau of Indian Standards every font supporting one of the
        official Indian languages needs to include Unicode Character
        “₹” (U+20B9) Indian Rupee Sign.
    """,
    conditions=["is_indic_font"],
    proposal="https://github.com/googlefonts/fontbakery/issues/2967",
)
def com_google_fonts_check_rupee(ttFont):
    """Ensure indic fonts have the Indian Rupee Sign glyph."""
    if 0x20B9 not in ttFont["cmap"].getBestCmap().keys():
        yield FAIL, Message(
            "missing-rupee",
            "Please add a glyph for Indian Rupee Sign (₹) at codepoint U+20B9.",
        )
    else:
        yield PASS, "Looks good!"


@check(
    id="com.google.fonts/check/unreachable_glyphs",
    rationale="""
        Glyphs are either accessible directly through Unicode codepoints or through
        substitution rules.

        In Color Fonts, glyphs are also referenced by the COLR table.

        Any glyphs not accessible by either of these means
        are redundant and serve only to increase the font's file size.
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/3160",
)
def com_google_fonts_check_unreachable_glyphs(ttFont, config):
    """Check font contains no unreachable glyphs"""

    def remove_lookup_outputs(all_glyphs, lookup):
        if lookup.LookupType == 1:  # Single:
            # Replace one glyph with one glyph
            for sub in lookup.SubTable:
                all_glyphs -= set(sub.mapping.values())

        if lookup.LookupType == 2:  # Multiple:
            # Replace one glyph with more than one glyph
            for sub in lookup.SubTable:
                for slot in sub.mapping.values():
                    all_glyphs -= set(slot)

        if lookup.LookupType == 3:  # Alternate:
            # Replace one glyph with one of many glyphs
            for sub in lookup.SubTable:
                for slot in sub.alternates.values():
                    all_glyphs -= set(slot)

        if lookup.LookupType == 4:  # Ligature:
            # Replace multiple glyphs with one glyph
            for sub in lookup.SubTable:
                for ligatures in sub.ligatures.values():
                    all_glyphs -= set(lig.LigGlyph for lig in ligatures)

        if lookup.LookupType in [5, 6]:
            # We do nothing here, because these contextual lookup types don't
            # generate glyphs directly; they only dispatch to other lookups
            # stored elsewhere in the lookup list. As we are examining all
            # lookups in the lookup list, other calls to this function will
            # deal with the lookups that a contextual lookup references.
            pass

        if lookup.LookupType == 7:  # Extension Substitution:
            # Extension mechanism for other substitutions
            for xt in lookup.SubTable:
                xt.SubTable = [xt.ExtSubTable]
                xt.LookupType = xt.ExtSubTable.LookupType
                remove_lookup_outputs(all_glyphs, xt)

        if lookup.LookupType == 8:  # Reverse chaining context single:
            # Applied in reverse order,
            # replace single glyph in chaining context
            for sub in lookup.SubTable:
                all_glyphs -= set(sub.Substitute)

    all_glyphs = set(ttFont.getGlyphOrder())

    # Exclude cmapped glyphs
    all_glyphs -= set(ttFont.getBestCmap().values())

    # Exclude glyphs referenced by cmap format 14 variation sequences
    # (as discussed at https://github.com/googlefonts/fontbakery/issues/3915):
    for table in ttFont["cmap"].tables:
        if table.format == 14:
            for values in table.uvsDict.values():
                for v in list(values):
                    if v[1] is not None:
                        all_glyphs.discard(v[1])

    # and ignore these:
    all_glyphs.discard(".null")
    all_glyphs.discard(".notdef")

    if "COLR" in ttFont:
        if ttFont["COLR"].version == 0:
            for glyphname, colorlayers in ttFont["COLR"].ColorLayers.items():
                for layer in colorlayers:
                    all_glyphs.discard(layer.name)

        elif ttFont["COLR"].version == 1:
            if (
                hasattr(ttFont["COLR"].table, "BaseGlyphRecordArray")
                and ttFont["COLR"].table.BaseGlyphRecordArray is not None
            ):
                for baseglyph_record in ttFont[
                    "COLR"
                ].table.BaseGlyphRecordArray.BaseGlyphRecord:
                    all_glyphs.discard(baseglyph_record.BaseGlyph)

            if (
                hasattr(ttFont["COLR"].table, "LayerRecordArray")
                and ttFont["COLR"].table.LayerRecordArray is not None
            ):
                for layer_record in ttFont["COLR"].table.LayerRecordArray.LayerRecord:
                    all_glyphs.discard(layer_record.LayerGlyph)

            for paint_record in ttFont["COLR"].table.BaseGlyphList.BaseGlyphPaintRecord:
                if hasattr(paint_record.Paint, "Glyph"):
                    all_glyphs.discard(paint_record.Paint.Glyph)

            for paint in ttFont["COLR"].table.LayerList.Paint:
                if hasattr(paint, "Glyph"):
                    all_glyphs.discard(paint.Glyph)

    if "GSUB" in ttFont and ttFont["GSUB"].table.LookupList:
        lookups = ttFont["GSUB"].table.LookupList.Lookup

        for lookup in lookups:
            remove_lookup_outputs(all_glyphs, lookup)

    # Remove components used in TrueType table
    if "glyf" in ttFont:
        for glyph_name in ttFont["glyf"].keys():
            base_glyph = ttFont["glyf"][glyph_name]
            if base_glyph.isComposite():
                all_glyphs -= set(base_glyph.getComponentNames(ttFont["glyf"]))

    if all_glyphs:
        yield WARN, Message(
            "unreachable-glyphs",
            "The following glyphs could not be reached"
            " by codepoint or substitution rules:\n\n"
            f"{bullet_list(config, sorted(all_glyphs))}\n",
        )
    else:
        yield PASS, "Font did not contain any unreachable glyphs"


@check(
    id="com.google.fonts/check/contour_count",
    conditions=["is_ttf", "not is_variable_font"],
    rationale="""
        Visually QAing thousands of glyphs by hand is tiring. Most glyphs can only
        be constructured in a handful of ways. This means a glyph's contour count
        will only differ slightly amongst different fonts, e.g a 'g' could either
        be 2 or 3 contours, depending on whether its double story or single story.

        However, a quotedbl should have 2 contours, unless the font belongs
        to a display family.

        This check currently does not cover variable fonts because there's plenty
        of alternative ways of constructing glyphs with multiple outlines for each
        feature in a VarFont. The expected contour count data for this check is
        currently optimized for the typical construction of glyphs in static fonts.
    """,
    proposal="legacy:check/153",
)
def com_google_fonts_check_contour_count(ttFont, config):
    """Check if each glyph has the recommended amount of contours.

    This check is useful to assure glyphs aren't incorrectly constructed.

    The desired_glyph_data module contains the 'recommended' countour count
    for encoded glyphs. The contour counts are derived from fonts which were
    chosen for their quality and unique design decisions for particular glyphs.

    In the future, additional glyph data can be included. A good addition would
    be the 'recommended' anchor counts for each glyph.
    """

    def in_PUA_range(codepoint):
        """
        In Unicode, a Private Use Area (PUA) is a range of code points that,
        by definition, will not be assigned characters by the Unicode Consortium.
        Three private use areas are defined:
          one in the Basic Multilingual Plane (U+E000–U+F8FF),
          and one each in, and nearly covering, planes 15 and 16
          (U+F0000–U+FFFFD, U+100000–U+10FFFD).
        """
        return (
            (codepoint >= 0xE000 and codepoint <= 0xF8FF)
            or (codepoint >= 0xF0000 and codepoint <= 0xFFFFD)
            or (codepoint >= 0x100000 and codepoint <= 0x10FFFD)
        )

    # rearrange data structure:
    desired_glyph_data_by_codepoint = {}
    desired_glyph_data_by_glyphname = {}
    for glyph in desired_glyph_data:
        desired_glyph_data_by_glyphname[glyph["name"]] = glyph
        # since the glyph in PUA ranges have unspecified meaning,
        # it doesnt make sense for us to have an expected contour cont for them
        if not in_PUA_range(glyph["unicode"]):
            desired_glyph_data_by_codepoint[glyph["unicode"]] = glyph

    bad_glyphs = []
    desired_glyph_contours_by_codepoint = {
        f: desired_glyph_data_by_codepoint[f]["contours"]
        for f in desired_glyph_data_by_codepoint
    }
    desired_glyph_contours_by_glyphname = {
        f: desired_glyph_data_by_glyphname[f]["contours"]
        for f in desired_glyph_data_by_glyphname
    }

    font_glyph_data = get_font_glyph_data(ttFont)

    if font_glyph_data is None:
        yield FAIL, Message("lacks-cmap", "This font lacks cmap data.")
    else:
        font_glyph_contours_by_codepoint = {
            f["unicode"]: list(f["contours"])[0] for f in font_glyph_data
        }
        font_glyph_contours_by_glyphname = {
            f["name"]: list(f["contours"])[0] for f in font_glyph_data
        }

        shared_glyphs_by_codepoint = set(desired_glyph_contours_by_codepoint) & set(
            font_glyph_contours_by_codepoint
        )
        for glyph in sorted(shared_glyphs_by_codepoint):
            if (
                font_glyph_contours_by_codepoint[glyph]
                not in desired_glyph_contours_by_codepoint[glyph]
            ):
                bad_glyphs.append(
                    [
                        glyph,
                        font_glyph_contours_by_codepoint[glyph],
                        desired_glyph_contours_by_codepoint[glyph],
                    ]
                )

        shared_glyphs_by_glyphname = set(desired_glyph_contours_by_glyphname) & set(
            font_glyph_contours_by_glyphname
        )
        for glyph in sorted(shared_glyphs_by_glyphname):
            if (
                font_glyph_contours_by_glyphname[glyph]
                not in desired_glyph_contours_by_glyphname[glyph]
            ):
                bad_glyphs.append(
                    [
                        glyph,
                        font_glyph_contours_by_glyphname[glyph],
                        desired_glyph_contours_by_glyphname[glyph],
                    ]
                )

        if len(bad_glyphs) > 0:
            cmap = (
                ttFont["cmap"]
                .getcmap(PlatformID.WINDOWS, WindowsEncodingID.UNICODE_BMP)
                .cmap
            )

            def _glyph_name(cmap, name):
                if name in cmap:
                    return cmap[name]
                else:
                    return name

            bad_glyphs_name = [
                f"Glyph name: {_glyph_name(cmap, name)}\t"
                f"Contours detected: {count}\t"
                f"Expected: {pretty_print_list(config, expected, glue='or')}"
                for name, count, expected in bad_glyphs
            ]
            bad_glyphs_name = bullet_list(config, bad_glyphs_name)
            yield WARN, Message(
                "contour-count",
                "This check inspects the glyph outlines and detects the total number"
                " of contours in each of them. The expected values are infered from"
                " the typical ammounts of contours observed in a large collection"
                " of reference font families. The divergences listed below may simply"
                " indicate a significantly different design on some of your glyphs."
                " On the other hand, some of these may flag actual bugs in the font"
                " such as glyphs mapped to an incorrect codepoint. Please consider"
                " reviewing the design and codepoint assignment of these to make"
                " sure they are correct.\n\n"
                "The following glyphs do not have the recommended"
                f" number of contours:\n\n{bad_glyphs_name}\n",
            )
        else:
            yield PASS, "All glyphs have the recommended amount of contours"


@check(
    id="com.google.fonts/check/soft_hyphen",
    rationale="""
        The 'Soft Hyphen' character (codepoint 0x00AD) is used to mark
        a hyphenation possibility within a word in the absence of or
        overriding dictionary hyphenation.

        It is sometimes designed empty with no width (such as a control character),
        sometimes the same as the traditional hyphen, sometimes double encoded with
        the hyphen.

        That being said, it is recommended to not include it in the font at all,
        because discretionary hyphenation should be handled at the level of the
        shaping engine, not the font. Also, even if present, the software would
        not display that character.

        More discussion at:
        https://typedrawers.com/discussion/2046/special-dash-things-softhyphen-horizontalbar
    """,
    proposal=[
        "https://github.com/googlefonts/fontbakery/issues/4046",
        "https://github.com/googlefonts/fontbakery/issues/3486",
    ],
)
def com_google_fonts_check_soft_hyphen(ttFont):
    """Does the font contain a soft hyphen?"""
    if 0x00AD in ttFont["cmap"].getBestCmap().keys():
        yield WARN, Message("softhyphen", "This font has a 'Soft Hyphen' character.")
    else:
        yield PASS, "Looks good!"


@check(
    id="com.google.fonts/check/cjk_chws_feature",
    conditions=["is_cjk_font"],
    rationale="""
        The W3C recommends the addition of chws and vchw features to CJK fonts
        to enhance the spacing of glyphs in environments which do not fully support
        JLREQ layout rules.

        The chws_tool utility (https://github.com/googlefonts/chws_tool) can be used
        to add these features automatically.
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/3363",
)
def com_google_fonts_check_cjk_chws_feature(ttFont):
    """Does the font contain chws and vchw features?"""
    passed = True
    tags = feature_tags(ttFont)
    FEATURE_NOT_FOUND = (
        "{} feature not found in font."
        " Use chws_tool (https://github.com/googlefonts/chws_tool)"
        " to add it."
    )
    if "chws" not in tags:
        passed = False
        yield WARN, Message("missing-chws-feature", FEATURE_NOT_FOUND.format("chws"))
    if "vchw" not in tags:
        passed = False
        yield WARN, Message("missing-vchw-feature", FEATURE_NOT_FOUND.format("vchw"))
    if passed:
        yield PASS, "Font contains chws and vchw features"


@check(
    id="com.google.fonts/check/transformed_components",
    conditions=["is_ttf"],
    rationale="""
        Some families have glyphs which have been constructed by using
        transformed components e.g the 'u' being constructed from a flipped 'n'.

        From a designers point of view, this sounds like a win (less work).
        However, such approaches can lead to rasterization issues, such as
        having the 'u' not sitting on the baseline at certain sizes after
        running the font through ttfautohint.

        Other issues are outlines that end up reversed when only one dimension
        is flipped while the other isn't.

        As of July 2019, Marc Foley observed that ttfautohint assigns cvt values
        to transformed glyphs as if they are not transformed and the result is
        they render very badly, and that vttLib does not support flipped components.

        When building the font with fontmake, the problem can be fixed by adding
        this to the command line:

        --filter DecomposeTransformedComponentsFilter
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/2011",
)
def com_google_fonts_check_transformed_components(ttFont, is_hinted):
    """Ensure component transforms do not perform scaling or rotation."""
    failures = ""
    for glyph_name in ttFont.getGlyphOrder():
        glyf = ttFont["glyf"][glyph_name]
        if not glyf.isComposite():
            continue
        for component in glyf.components:
            comp_name, transform = component.getComponentInfo()

            # Font is hinted, complain about *any* transformations
            if is_hinted:
                if transform[0:4] != (1, 0, 0, 1):
                    failures += f"* {glyph_name} (component {comp_name})\n"
            # Font is unhinted, complain only about transformations where
            # only one dimension is flipped while the other isn't.
            # Otherwise the outline direction is intact and since the font is unhinted,
            # no rendering problems are to be expected
            else:
                if transform[0] * transform[3] < 0:
                    failures += f"* {glyph_name} (component {comp_name})\n"

    if failures:
        yield FAIL, Message(
            "transformed-components",
            "The following glyphs had components with scaling or rotation\n"
            f"or inverted outline direction:\n\n{failures}",
        )
    else:
        yield PASS, "No glyphs had components with scaling or rotation"


@check(
    id="com.google.fonts/check/gpos7",
    conditions=["ttFont"],
    severity=9,
    rationale="""
        Versions of fonttools >=4.14.0 (19 August 2020) perform an optimisation on
        chained contextual lookups, expressing GSUB6 as GSUB5 and GPOS8 and GPOS7
        where possible (when there are no suffixes/prefixes for all rules in
        the lookup).

        However, makeotf has never generated these lookup types and they are rare
        in practice. Perhaps before of this, Mac's CoreText shaper does not correctly
        interpret GPOS7, meaning that these lookups will be ignored by the shaper,
        and fonts containing these lookups will have unintended positioning errors.

        To fix this warning, rebuild the font with a recent version of fonttools.
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/3643",
)
def com_google_fonts_check_gpos7(ttFont):
    """Ensure no GPOS7 lookups are present."""
    has_gpos7 = False

    def find_gpos7(lookup):
        nonlocal has_gpos7
        if lookup.LookupType == 7:
            has_gpos7 = True

    iterate_lookup_list_with_extensions(ttFont, "GPOS", find_gpos7)

    if not has_gpos7:
        yield PASS, "Font has no GPOS7 lookups"
        return

    yield WARN, Message(
        "has-gpos7", "Font contains a GPOS7 lookup which is not processed by macOS"
    )


@check(
    id="com.adobe.fonts/check/freetype_rasterizer",
    conditions=["ttFont"],
    severity=10,
    rationale="""
        Malformed fonts can cause FreeType to crash.
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/3642",
)
def com_adobe_fonts_check_freetype_rasterizer(font):
    """Ensure that the font can be rasterized by FreeType."""
    import freetype
    from freetype.ft_errors import FT_Exception
    from pathlib import Path

    if isinstance(font, Path):
        font = str(font)

    try:
        face = freetype.Face(font)
        face.set_char_size(48 * 64)
        # *Almost* any character can be used here, however symbol fonts make
        # this check fail with many characters.
        face.load_char("0")

    except FT_Exception as err:
        yield FAIL, Message(
            "freetype-crash", f"Font caused FreeType to crash with this error: {err}"
        )
    else:
        yield PASS, "Font can be rasterized by FreeType."


@check(
    id="com.adobe.fonts/check/sfnt_version",
    severity=10,
    rationale="""
        OpenType fonts that contain TrueType outlines should use the value of 0x00010000
        for the sfntVersion. OpenType fonts containing CFF data (version 1 or 2) should
        use 0x4F54544F ('OTTO', when re-interpreted as a Tag) for sfntVersion.

        Fonts with the wrong sfntVersion value are rejected by FreeType.

        https://docs.microsoft.com/en-us/typography/opentype/spec/otff#table-directory
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/3388",
)
def com_adobe_fonts_check_sfnt_version(ttFont, is_ttf, is_cff, is_cff2):
    """Font has the proper sfntVersion value?"""
    sfnt_version = ttFont.sfntVersion

    if is_ttf and sfnt_version != "\x00\x01\x00\x00":
        yield FAIL, Message(
            "wrong-sfnt-version-ttf",
            "Font with TrueType outlines has incorrect sfntVersion value:"
            f" '{sfnt_version}'",
        )

    elif (is_cff or is_cff2) and sfnt_version != "OTTO":
        yield FAIL, Message(
            "wrong-sfnt-version-cff",
            f"Font with CFF data has incorrect sfntVersion value: '{sfnt_version}'",
        )

    else:
        yield PASS, "Font has the correct sfntVersion value."


@check(
    id="com.google.fonts/check/whitespace_widths",
    conditions=["not missing_whitespace_chars"],
    rationale="""
        If the space and nbspace glyphs have different widths, then Google Workspace
        has problems with the font.

        The nbspace is used to replace the space character in multiple situations in
        documents; such as the space before punctuation in languages that do that. It
        avoids the punctuation to be separated from the last word and go to next line.

        This is automatic substitution by the text editors, not by fonts. It's also used
        by designers in text composition practice to create nicely shaped paragraphs.
        If the space and the nbspace are not the same width, it breaks the text
        composition of documents.
    """,
    proposal=[
        "https://github.com/googlefonts/fontbakery/issues/3843",
        "legacy:check/050",
    ],
)
def com_google_fonts_check_whitespace_widths(ttFont):
    """Space and non-breaking space have the same width?"""
    space_name = get_glyph_name(ttFont, 0x0020)
    nbsp_name = get_glyph_name(ttFont, 0x00A0)

    space_width = ttFont["hmtx"][space_name][0]
    nbsp_width = ttFont["hmtx"][nbsp_name][0]

    if space_width > 0 and space_width == nbsp_width:
        yield PASS, "Space and non-breaking space have the same width."
    else:
        yield FAIL, Message(
            "different-widths",
            "Space and non-breaking space have differing width:"
            f" The space glyph named {space_name} is {space_width} font units wide,"
            f" non-breaking space named ({nbsp_name}) is {nbsp_width} font units wide,"
            ' and both should be positive and the same. GlyphsApp has "Sidebearing'
            ' arithmetic" (https://glyphsapp.com/tutorials/spacing) which allows you to'
            " set the non-breaking space width to always equal the space width.",
        )


@check(
    id="com.google.fonts/check/interpolation_issues",
    conditions=["is_variable_font", "is_ttf"],
    severity=4,
    rationale="""
        When creating a variable font, the designer must make sure that corresponding
        paths have the same start points across masters, as well as that corresponding
        component shapes are placed in the same order within a glyph across masters.
        If this is not done, the glyph will not interpolate correctly.

        Here we check for the presence of potential interpolation errors using the
        fontTools.varLib.interpolatable module.
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/3930",
)
def com_google_fonts_check_iterpolation_issues(ttFont, config):
    """Detect any interpolation issues in the font."""
    from fontTools.varLib.interpolatable import test as interpolation_test

    gvar = ttFont["gvar"]
    # This code copied from fontTools.varLib.interpolatable
    locs = set()
    names = []
    for variations in gvar.variations.values():
        for var in variations:
            loc = []
            for tag, val in sorted(var.axes.items()):
                loc.append((tag, val[1]))
            locs.add(tuple(loc))

    # Rebuild locs as dictionaries
    new_locs = [{}]
    names.append("()")
    for loc in sorted(locs, key=lambda v: (len(v), v)):
        names.append(str(loc))
        location = {}
        for tag, val in loc:
            location[tag] = val
        new_locs.append(location)

    locs = new_locs
    glyphsets = [ttFont.getGlyphSet(location=loc, normalized=True) for loc in locs]
    results = interpolation_test(glyphsets)

    if not results:
        yield PASS, "No interpolation issues found"
    else:
        # Most of the potential problems varLib.interpolatable finds can't
        # exist in a built binary variable font. We focus on those which can.
        report = []
        for glyph, glyph_problems in results.items():
            for p in glyph_problems:
                if p["type"] == "contour_order":
                    report.append(
                        f"Contour order differs in glyph '{glyph}':"
                        f" {p['value_1']} in {p['master_1'] or 'default'},"
                        f" {p['value_2']} in {p['master_2'] or 'default'}."
                    )
                elif p["type"] == "wrong_start_point":
                    report.append(
                        f"Contour {p['contour']} start point"
                        f" differs in glyph '{glyph}' between"
                        f" location {p['master_1'] or 'default'} and"
                        f" location {p['master_2'] or 'default'}"
                    )
        yield WARN, Message(
            "interpolation-issues",
            f"Interpolation issues were found in the font:"
            f" {bullet_list(config, report)}",
        )


@check(
    id="com.google.fonts/check/math_signs_width",
    rationale="""
        It is a common practice to have math signs sharing the same width
        (preferably the same width as tabular figures accross the entire font family).

        This probably comes from the will to avoid additional tabular math signs
        knowing that their design can easily share the same width.
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/3832",
)
def com_google_fonts_check_math_signs_width(ttFont):
    """Check math signs have the same width."""
    # Ironically, the block of text below may not have
    # uniform widths for these glyphs depending on
    # which font your text editor is using while you
    # read the source code of this check:
    COMMON_WIDTH_MATH_GLYPHS = (
        "+ < = > ¬ ± × ÷ ∈ ∉ ∋ ∌ − ∓ ∔ ∝ ∟ ∠ ∡ ∢ ∷ ∸ ∹ ∺ ∻ "
        "∼ ∽ ∾ ∿ ≁ ≂ ≃ ≄ ≅ ≆ ≇ ≈ ≉ ≊ ≋ ≌ ≍ ≎ ≏ ≐ ≑ ≒ ≓ ≖ ≗ "
        "≘ ≙ ≚ ≛ ≜ ≝ ≞ ≟ ≠ ≡ ≢ ≣ ≤ ≥ ≦ ≧ ≨ ≩ ≭ ≮ ≯ ≰ ≱ ≲ ≳ "
        "≴ ≵ ≶ ≷ ≸ ≹ ≺ ≻ ≼ ≽ ≾ ≿ ⊀ ⊁ ⊂ ⊃ ⊄ ⊅ ⊆ ⊇ ⊈ ⊉ ⊊ ⊋ ⊏ "
        "⊐ ⊑ ⊒ ⊢ ⊣ ⊤ ⊥ ⊨ ⊰ ⊱ ⊲ ⊳ ⊴ ⊵ ⊹ ⊾ ⋇ ⋍ ⋐ ⋑ ⋕ ⋖ ⋗ ⋚ ⋛ "
        "⋜ ⋝ ⋞ ⋟ ⋠ ⋡ ⋢ ⋣ ⋤ ⋥ ⋦ ⋧ ⋨ ⋩ ⋳ ⋵ ⋶ ⋸ ⋹ ⋻ ⋽ ⟀ ⟃ ⟄ ⟓ "
        "⟔ ⥶ ⥸ ⥹ ⥻ ⥾ ⥿ ⦓ ⦔ ⦕ ⦖ ⦛ ⦜ ⦝ ⦞ ⦟ ⦠ ⦡ ⦢ ⦣ ⦤ ⦥ ⦨ ⦩ ⦪ "
        "⦫ ⧣ ⧤ ⧥ ⧺ ⧻ ⨢ ⨣ ⨤ ⨥ ⨦ ⨧ ⨨ ⨩ ⨪ ⨫ ⨬ ⨳ ⩦ ⩧ ⩨ ⩩ ⩪ ⩫ ⩬ "
        "⩭ ⩮ ⩯ ⩰ ⩱ ⩲ ⩳ ⩷ ⩸ ⩹ ⩺ ⩻ ⩼ ⩽ ⩾ ⩿ ⪀ ⪁ ⪂ ⪃ ⪄ ⪅ ⪆ ⪇ ⪈ "
        "⪉ ⪊ ⪋ ⪌ ⪍ ⪎ ⪏ ⪐ ⪑ ⪒ ⪓ ⪔ ⪕ ⪖ ⪗ ⪘ ⪙ ⪚ ⪛ ⪜ ⪝ ⪞ ⪟ ⪠ ⪡ "
        "⪢ ⪦ ⪧ ⪨ ⪩ ⪪ ⪫ ⪬ ⪭ ⪮ ⪯ ⪰ ⪱ ⪲ ⪳ ⪴ ⪵ ⪶ ⪷ ⪸ ⪹ ⪺ ⪽ ⪾ ⪿ "
        "⫀ ⫁ ⫂ ⫃ ⫄ ⫅ ⫆ ⫇ ⫈ ⫉ ⫊ ⫋ ⫌ ⫏ ⫐ ⫑ ⫒ ⫓ ⫔ ⫕ ⫖ ⫟ ⫠ ⫡ ⫢ "
        "⫤ ⫦ ⫧ ⫨ ⫩ ⫪ ⫫ ⫳ ⫴ ⫵ ⫶ ⫹ ⫺ 〒"
    )

    glyphs_by_width = {}
    for glyph in COMMON_WIDTH_MATH_GLYPHS.split(" "):
        codepoint = ord(glyph)
        glyph_name = get_glyph_name(ttFont, codepoint)
        if glyph_name is None:
            # The font does not have this glyph, so move on...
            continue
        glyph_width = ttFont["hmtx"][glyph_name][0]
        if glyph_width not in glyphs_by_width:
            glyphs_by_width[glyph_width] = set([glyph_name])
        else:
            glyphs_by_width[glyph_width].add(glyph_name)

    most_common_width = None
    num_glyphs = 0
    for glyph_width, glyph_names in glyphs_by_width.items():
        if most_common_width is None:
            num_glyphs = len(glyph_names)
            most_common_width = glyph_width
        else:
            if len(glyph_names) > num_glyphs:
                most_common_width = glyph_width
                num_glyphs = len(glyph_names)

    if most_common_width and len(glyphs_by_width.keys()) > 1:
        outliers_summary = []
        for w, names in glyphs_by_width.items():
            if not w == most_common_width:
                outliers_summary.append(f"Width = {w}:\n{', '.join(names)}\n")
        outliers_summary = "\n".join(outliers_summary)
        yield WARN, Message(
            "width-outliers",
            f"The most common width is {most_common_width} among a set of {num_glyphs}"
            " math glyphs.\nThe following math glyphs have a different width, though:"
            f"\n\n{outliers_summary}",
        )
    else:
        yield PASS, "Looks good."


@check(
    id="com.google.fonts/check/linegaps",
    rationale="""
        The LineGap value is a space added to the line height created by the union
        of the (typo/hhea)Ascender and (typo/hhea)Descender. It is handled differently
        according to the environment.

        This leading value will be added above the text line in most desktop apps.
        It will be shared above and under in web browsers, and ignored in Windows
        if Use_Typo_Metrics is disabled.

        For better linespacing consistency across platforms,
        (typo/hhea)LineGap values must be 0.
    """,
    proposal=[
        "https://github.com/googlefonts/fontbakery/issues/4133",
        "https://googlefonts.github.io/gf-guide/metrics.html",
    ],
)
def com_google_fonts_check_linegaps(ttFont):
    """Checking Vertical Metric Linegaps."""

    required_tables = {"hhea", "OS/2"}
    missing_tables = sorted(required_tables - set(ttFont.keys()))
    if missing_tables:
        for table_tag in missing_tables:
            yield FAIL, Message("lacks-table", f"Font lacks '{table_tag}' table.")
        return

    if ttFont["hhea"].lineGap != 0:
        yield WARN, Message("hhea", "hhea lineGap is not equal to 0.")
    elif ttFont["OS/2"].sTypoLineGap != 0:
        yield WARN, Message("OS/2", "OS/2 sTypoLineGap is not equal to 0.")
    else:
        yield PASS, "OS/2 sTypoLineGap and hhea lineGap are both 0."


@check(
    id="com.google.fonts/check/STAT_in_statics",
    conditions=["not is_variable_font", "has_STAT_table"],
    rationale="""
        Adobe feature syntax allows for the definition of a STAT table. Fonts built
        with a hand-coded STAT table in feature syntax may be built either as static
        or variable, but will end up with the same STAT table.

        This is a problem, because a STAT table which works on variable fonts
        will not be appropriate for static instances. The examples in the OpenType spec
        of non-variable fonts with a STAT table show that the table entries must be
        restricted to those entries which refer to the static font's position in
        the designspace. i.e. a Regular weight static should only have the following
        entry for the weight axis:

        <AxisIndex value="0"/>
        <Flags value="2"/>  <!-- ElidableAxisValueName -->
        <ValueNameID value="265"/>  <!-- Regular -->
        <Value value="400.0"/>

        However, if the STAT table intended for a variable font is compiled into a
        static, it will have many entries for this axis. In this case, Windows will
        read the first entry only, causing all instances to report themselves
        as "Thin Condensed".
    """,
    proposal="https://github.com/googlefonts/fontbakery/issues/4149",
)
def com_google_fonts_check_STAT_in_statics(ttFont):
    """Checking STAT table entries in static fonts."""

    entries = {}

    def count_entries(tag_name):
        if tag_name in entries:
            entries[tag_name] += 1
        else:
            entries[tag_name] = 1

    passed = True
    stat = ttFont["STAT"].table
    designAxes = stat.DesignAxisRecord.Axis
    for axisValueTable in stat.AxisValueArray.AxisValue:
        axisValueFormat = axisValueTable.Format
        if axisValueFormat in (1, 2, 3):
            axisTag = designAxes[axisValueTable.AxisIndex].AxisTag
            count_entries(axisTag)
        elif axisValueFormat == 4:
            for rec in axisValueTable.AxisValueRecord:
                axisTag = designAxes[rec.AxisIndex].AxisTag
                count_entries(axisTag)

    for tag_name in entries:
        if entries[tag_name] > 1:
            passed = False
            yield FAIL, Message(
                "multiple-STAT-entries",
                "The STAT table has more than a single entry for the"
                f" '{tag_name}' axis ({entries[tag_name]}) on this"
                " static font which will causes problems on Windows.",
            )

    if passed:
        yield PASS, "Looks good!"


profile.auto_register(globals())
profile.test_expected_checks(UNIVERSAL_PROFILE_CHECKS, exclusive=True)
