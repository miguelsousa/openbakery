import shutil
import sys

import pytest

from conftest import ImportRaiser, remove_import_raiser, reload_module

from openbakery.codetesting import TEST_FILE, assert_results_contain, CheckTester
from openbakery.status import FAIL
from openbakery.profiles import fontval as fontval_profile


def test_extra_needed_exit(monkeypatch):
    module_name = "lxml.etree"
    sys.meta_path.insert(0, ImportRaiser(module_name))
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    with pytest.raises(SystemExit):
        reload_module("openbakery.profiles.fontval")

    remove_import_raiser(module_name)


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
