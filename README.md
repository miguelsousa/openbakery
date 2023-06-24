<p align="center">
  <img src="https://raw.githubusercontent.com/miguelsousa/openbakery/main/data/openbakery.jpg" alt="OpenBakery">
</p>
<p align="center">
    <b>OpenBakery, a font quality assurance tool for everyone</b>
</p>
<p align="center">
<a href="https://github.com/miguelsousa/openbakery/actions/workflows/lint_test.yml" target="_blank">
    <img src="https://github.com/miguelsousa/openbakery/actions/workflows/lint_test.yml/badge.svg" alt="Lint & Test workflow status">
</a>
<a href="https://codecov.io/gh/miguelsousa/openbakery" target="_blank">
  <img src="https://codecov.io/gh/miguelsousa/openbakery/branch/main/graph/badge.svg?token=2K1LW5OCW8"/ alt="Code coverage status"> 
</a>
<a href="https://pypi.org/project/openbakery" target="_blank">
    <img src="https://img.shields.io/pypi/v/openbakery.svg" alt="Package version">
</a>
<a href="https://pypi.org/project/openbakery" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/openbakery.svg" alt="Minimum Python version">
</a>
</p>

---

**Documentation**: https://miguelsousa.github.io/openbakery

**Source Code**: https://github.com/miguelsousa/openbakery

**Contributing Guide**: https://github.com/miguelsousa/openbakery/blob/main/CONTRIBUTING.md

---

**OpenBakery** is a command-line tool for validating font binaries and, optionally, their source files and metadata.


## Requirements

- **Python** version 3.8 (or greater)
<br>To determine if your system has Python installed and which version, run this command: `python --version`
<br>Please refer to the instructions provided at [python.org](https://www.python.org/) for downloading and installing Python on your platform.

- **`pip`** version 22.0 (or greater)
<br>To determine if your Python environment has `pip` installed and which version, run this command: `python -m pip --version`
<br>Please refer to the instructions provided at [pip.pypa.io](https://pip.pypa.io/en/stable/installation/) for downloading and installing `pip` on your Python environment.

⚠️ **IMPORTANT**: If you have Python 2.x installed in your system, you may have to use `python3` (instead of `python`) in the commands below.


## Installation

Command to install a **stable version** of OpenBakery:

    python -m pip install --upgrade openbakery

Command to install a **beta version** of OpenBakery:

    python -m pip install --upgrade --pre openbakery

OpenBakery's functionality is organized into profiles. Each profile invokes specific font checks. To get a list of all the profiles run this command:

    openbakery --list-subcommands

```
adobefonts
fontbureau
fontval
fontwerk
googlefonts
iso15008
notofonts
opentype
ufo-sources
universal
proposals
check-profile
```

The installation commands above enable you to run the `universal` or the `opentype` profiles on a font, like so:

    openbakery universal MyFont-Regular.ttf

To test your fonts with other profiles, you need to install `openbakery` with a corresponding extra. The command below installs `openbakery` with all the necessary dependencies for running the checks in the `googlefonts` profile:

    python -m pip install --upgrade 'openbakery[googlefonts]'


## Usage

If you made it this far, congratulation! You should now be ready to "bake" your fonts. 😀 🥯🍞🥖🥨🥐🫓🧁

The [documentation](https://miguelsousa.github.io/openbakery) contains many examples of how to run `openbakery` with its various options.


## License

This project is licensed under the terms of the Apache 2.0 license.

All comments on issues, pull requests, and discussions will be treated as also licensed under this license such that they can be incorporated into the project's codebase.


## Fork acknowledgment

This project is a fork of [Font Bakery](https://github.com/googlefonts/fontbakery).
