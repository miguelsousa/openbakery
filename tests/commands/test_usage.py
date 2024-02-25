import os
import re
import subprocess
import tempfile

import pytest

TOOL_NAME = "openbakery"


def test_list_subcommands_option(capfd):
    """Test if 'openbakery --list-subcommands' can run successfully and output
    the expected content."""
    from openbakery.cli import SUBCOMMANDS

    subprocess.run([TOOL_NAME, "--list-subcommands"], check=True)
    captured = capfd.readouterr()
    assert captured.out == f"{os.linesep.join(SUBCOMMANDS)}{os.linesep}"


def test_list_checks_option(capfd):
    """Test if 'openbakery <subcommand> --list-checks' can run successfully and output
    the expected content."""
    from openbakery.profiles.universal import UNIVERSAL_PROFILE_CHECKS

    subprocess.run([TOOL_NAME, "universal", "--list-checks"], check=True)
    output = capfd.readouterr().out
    assert set(output.split()) == set(UNIVERSAL_PROFILE_CHECKS)


def test_command_check_googlefonts():
    """Test if 'openbakery googlefonts' can run successfully."""
    subprocess.run([TOOL_NAME, "googlefonts", "-h"], check=True)
    subprocess.run(
        [
            TOOL_NAME,
            "googlefonts",
            "-c",
            "com.google.fonts/check/canonical_filename",
            "-c",
            "stat_axis_record_for_each_axis",
            "-c",
            "layout_valid_feature_tags",
            os.path.join("data", "test", "nunito", "Nunito-Regular.ttf"),
        ],
        check=True,
    )
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run([TOOL_NAME, "googlefonts"], check=True)


@pytest.mark.parametrize(
    "subcommand",
    [
        "check-profile",
        "opentype",
        "ufo-sources",
    ],
)
def test_command_check_profile(subcommand):
    """Test if 'openbakery <subcommand>' can run successfully."""
    subprocess.run([TOOL_NAME, subcommand, "-h"], check=True)

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run([TOOL_NAME, subcommand], check=True)


def test_tool_help():
    """Test if just 'openbakery' command can run successfully."""
    assert subprocess.run([TOOL_NAME, "-h"]).returncode == 0
    assert subprocess.run([TOOL_NAME]).returncode == 0


@pytest.mark.xfail(
    strict=True
)  # This test is too much prone to failing whenever we update
# the text-output formatting or the actual log messages in that openbakery check
# I would like to have this test refactored to be in a good state for much longer.
# Please, only remove the xfail mark once the test is more robust / future proof.
def test_status_log_is_indented():
    """Test if statuses are printed in a limited boundary."""
    result = subprocess.run(
        [
            TOOL_NAME,
            "googlefonts",
            "-c",
            "old_ttfautohint",
            "-c",
            "font_copyright",
            os.path.join("data", "test", "nunito", "Nunito-Regular.ttf"),
        ],
        capture_output=True,
    )

    p = re.compile("([^][a-zA-Z0-9@:,.()'\"\n ])", re.I | re.M)
    stdout = p.sub("#", result.stdout.decode()).split("\n")
    assert "\n".join(stdout[24:30]) == "\n".join(
        [
            "     #[0#31#40mFAIL#[0m Name Table entry: Copyright notices should match a      ",  # noqa:E501 pylint:disable=C0301
            '          pattern similar to: "Copyright 2019 The Familyname Project Authors    ',  # noqa:E501 pylint:disable=C0301
            '          (git url)"                                                            ',  # noqa:E501 pylint:disable=C0301
            "          But instead we have got:                                              ",  # noqa:E501 pylint:disable=C0301
            '          "Copyright 2014 The Nunito Project Authors (contact@sansoxygen.com)"  ',  # noqa:E501 pylint:disable=C0301
            "          [code: bad#notice#format]                                             ",  # noqa:E501 pylint:disable=C0301
        ]
    )
    assert "\n".join(stdout[10:15]) == "\n".join(
        [
            "     #[0#36#40mINFO#[0m Could not detect which version of ttfautohint was used  ",  # noqa:E501 pylint:disable=C0301
            "          in this font. It is typically specified as a comment in the font      ",  # noqa:E501 pylint:disable=C0301
            "          version entries of the 'name' table. Such font version strings are    ",  # noqa:E501 pylint:disable=C0301
            "          currently: ['Version 3.000', 'Version 3.000'] [code:                  ",  # noqa:E501 pylint:disable=C0301
            "          version#not#detected]                                                 ",  # noqa:E501 pylint:disable=C0301
        ]
    )


def test_command_config_file():
    """Test if we can set checks using a config file."""
    config = tempfile.NamedTemporaryFile(delete=False)
    config.write(b"explicit_checks = ['com.adobe.fonts/check/name/empty_records']")
    config.close()
    test_font = os.path.join("data", "test", "nunito", "Nunito-Regular.ttf")
    result = subprocess.run(
        [TOOL_NAME, "googlefonts", "--config", config.name, test_font],
        stdout=subprocess.PIPE,
    )
    stdout = result.stdout.decode()
    assert "running 1 individual check" in stdout
    os.unlink(config.name)


def test_command_config_file_injection():
    """Test if we can inject a config variable into a check."""
    config = tempfile.NamedTemporaryFile(delete=False)
    config.write(
        b"""
[a_test_profile]
OK = 123
"""
    )
    config.close()
    test_font = os.path.join("data", "test", "nunito", "Nunito-Regular.ttf")
    test_profile = os.path.join("tests", "profiles", "a_test_profile.py")
    result = subprocess.run(
        [
            TOOL_NAME,
            "check-profile",
            "-C",
            "--config",
            config.name,
            test_profile,
            test_font,
        ],
        stdout=subprocess.PIPE,
    )
    stdout = result.stdout.decode()
    assert "FAIL: 0" in stdout
    os.unlink(config.name)


def test_config_override():
    """Test we can override check statuses in the configuration file"""
    config = tempfile.NamedTemporaryFile(delete=False)
    config.write(
        b"""
overrides:
  com.google.fonts/check/file_size:
    large-font: FAIL
explicit_checks:
  - com.google.fonts/check/file_size
"""
    )
    config.close()
    test_font = os.path.join("data", "test", "varfont", "inter", "Inter[slnt,wght].ttf")
    result = subprocess.run(
        [TOOL_NAME, "googlefonts", "-C", "--config", config.name, test_font],
        stdout=subprocess.PIPE,
    )
    stdout = result.stdout.decode()
    # This font has a WARN here, so should now FAIL
    assert "FAIL: 1" in stdout
    os.unlink(config.name)
