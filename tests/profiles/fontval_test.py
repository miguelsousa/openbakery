import shutil

import pytest

from openbakery.codetesting import TEST_FILE, assert_results_contain, CheckTester
from openbakery.status import FAIL
from openbakery.profiles import fontval as fontval_profile


def test_check_fontvalidator_not_installed():
    check = CheckTester(fontval_profile, "com.google.fonts/check/fontvalidator")
    font = TEST_FILE("mada/Mada-Regular.ttf")
    assert_results_contain(check(font), FAIL, "fontval-not-available")


@pytest.mark.skipif(
    not shutil.which("FontValidator"),
    reason="FontValidator is not installed on your system",
)
def test_check_fontvalidator():
    """MS Font Validator checks"""
    raise NotImplementedError
