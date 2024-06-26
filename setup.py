# Copyright 2017 The Font Bakery Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# See AUTHORS.txt for the list of Authors and LICENSE.txt for the License.

from setuptools import setup

try:
    readme = open("README.md", encoding="utf8").read()
except IOError:
    readme = ""


FONTTOOLS_VERSION = ">=4.39.0"  # Python 3.8+ required
UFO2FT_VERSION = ">=2.25.2"  # 2.25.2 updated the script lists for Unicode 14.0
VHARFBUZZ_VERSION = ">=0.2.0"  # 0.2.0 had an API update

# Profile-specific dependencies:
shaping_extras = [
    "collidoscope>=0.5.2",  # 0.5.2 added Python 3.11 wheels
    # (see https://github.com/googlefonts/fontbakery/issues/3970)
    "stringbrewer",
    f"ufo2ft{UFO2FT_VERSION}",
    f"vharfbuzz{VHARFBUZZ_VERSION}",
]

ufo_sources_extras = [
    "defcon",
    f"fontTools[ufo]{FONTTOOLS_VERSION}",
    f"ufo2ft{UFO2FT_VERSION}",
    "ufolint",
]

googlefonts_extras = (
    [
        "axisregistry>=0.4.8",
        "beautifulsoup4",  # For parsing registered vendor IDs from Microsoft's webpage
        "dehinter>=3.1.0",  # 3.1.0 added dehinter.font.hint function
        "font-v",
        f"fontTools[lxml,unicode]{FONTTOOLS_VERSION}",
        "gflanguages>=0.3.0",  # 0.3.0 had an api simplification/update
        # (see https://github.com/googlefonts/gflanguages/pull/7)
        "glyphsets>=0.5.0, <=0.6.6",  # newer versions contain breaking changes
        "protobuf>=3.7.0, <4",  # 3.7.0 fixed a bug on parsing some METADATA.pb files.
        # We cannot use v4 because our protobuf files have been compiled with v3.
        # (see https://github.com/googlefonts/fontbakery/issues/2200)
        f"vharfbuzz{VHARFBUZZ_VERSION}",
    ]
    + shaping_extras
    + ufo_sources_extras
)

iso15008_extras = [
    "uharfbuzz",
]

all_extras = set(
    googlefonts_extras + iso15008_extras + shaping_extras + ufo_sources_extras
)

setup(
    name="openbakery",
    use_scm_version={"write_to": "Lib/openbakery/_version.py"},
    url="https://github.com/miguelsousa/openbakery/",
    description="A font quality assurance tool for everyone",
    long_description=readme,
    long_description_content_type="text/markdown",
    author=(
        "OpenBakery authors and contributors:"
        " Dave Crossland,"
        " Felipe Sanches,"
        " Lasse Fister,"
        " Marc Foley,"
        " Nikolaus Waxweiler,"
        " Chris Simpkins,"
        " Jens Kutilek,"
        " Vitaly Volkov,"
        " Simon Cozens,"
        " Miguel Sousa"
    ),
    author_email="miguel.sousa@adobe.com",
    package_dir={"": "Lib"},
    packages=[
        "openbakery",
        "openbakery.reporters",
        "openbakery.profiles",
        "openbakery.commands",
    ],
    package_data={"openbakery": ["data/*.cache", "data/googlefonts/*_exceptions.txt"]},
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    setup_requires=[
        "setuptools>=61.2",
        "setuptools_scm[toml]>=6.2",
    ],
    install_requires=[
        # ---
        # core dependencies
        f"fontTools{FONTTOOLS_VERSION}",
        "freetype-py!=2.4.0",  # Avoiding 2.4.0 due to seg-fault described at
        # https://github.com/googlefonts/fontbakery/issues/4143
        "opentypespec",
        "opentype-sanitizer>=7.1.9",  # 7.1.9 fixes caret value format = 3 bug
        # (see https://github.com/khaledhosny/ots/pull/182)
        # ---
        # fontTools extra that is needed by 'interpolation_issues' check in
        # Universal profile
        "munkres",
        # ---
        # for parsing Configuration files (Lib/openbakery/configuration.py)
        "PyYAML",
        "toml",
        # ---
        # used by Reporters (Lib/openbakery/reporters)
        "cmarkgfm",  # (html.py)
        "rich",  # (terminal.py)
        # ---
        # used by 'openbakery_version' check in Universal profile
        "packaging",
        "pip-api",
        "requests",  # also used by Google Fonts profile
        # ---
        # used by 'italic_angle' check in OpenType profile ('post' table);
        # also used by ISO 15008 profile
        "beziers>=0.5.0",  # 0.5.0 uses new fontTools glyph outline access
        # ---
    ],
    extras_require={
        "all": all_extras,
        "fontwerk": googlefonts_extras,
        "googlefonts": googlefonts_extras,
        "notofonts": googlefonts_extras,
        "iso15008": iso15008_extras,
        "shaping": shaping_extras,
        "ufo-sources": ufo_sources_extras,
    },
    entry_points={
        "console_scripts": ["openbakery=openbakery.cli:main"],
    },
)
