---
layout: default
title: Home
nav_order: 1
description: "OpenBakery is a command-line tool for validating font binaries, their source files, and metadata."
---

# Font quality assurance for everyone
{: .fs-9 }

OpenBakery is a command-line tool to help you validate font binaries, their source files, and metadata. [View it on GitHub][OpenBakery repo].
{: .fs-6 .fw-300 }

---

## Getting started

👋 Hi! Thank you for your interest in OpenBakery. Before we start, we need to ensure that your system has the necessary software installed.

OpenBakery requires **Python version 3.8** (or greater) and **`pip` version 22.0** (or greater).


### Checking Python version

To determine if your system has Python installed and which version, open **Terminal** —on macOS and Linux— or **PowerShell** and **Command Prompt** —on Windows— and run the following command:

    python --version

{: .note }
If the `python` command isn't found, try using `python3` instead.

If you need to install Python (or just a newer version of it) please refer to the instructions provided at [python.org] for your platform.


### Checking `pip` version

To determine if your Python environment has `pip` installed and which version, run this command:

    python -m pip --version

If you need to install `pip` (or just a newer version of it) please refer to the instructions provided at [pip.pypa.io].


## Ready to go

All set! Choose a ~~pill~~ button to get started 😎

[DEVELOPER]({% link developer-guide.md %}){: .label .label-blue .fs-4 }
[USER]({% link user-guide.md %}){: .label .fs-4 .label-red }


[OpenBakery repo]: https://github.com/miguelsousa/openbakery
[python.org]: https://www.python.org/
[pip.pypa.io]: https://pip.pypa.io/en/stable/installation/
