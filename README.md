pyspread
====================

**pyspread** is a non-traditional spreadsheet that is
based on and written in the programming language Python.

It is released under the [GPL v3. LICENSE](LICENSE)

- Homepage: https://pyspread.gitlab.io/
- Repository: https://gitlab.com/pyspread/pyspread
- API Docs: https://pyspread.gitlab.io/pyspread/


# Installation

## On Debian bullseye

On Debian bullseye, pyspread is available as a package.
Note that the version number for the Python3 beta release is >=1.99.1.

```bash
su -
apt install pyspread
```

## Other platforms

### Prerequisites

Get the prerequisites:
- Python (>=3.6)
- PyQt5 (>=5.10) (must include PyQtSvg)
- numpy (>=1.1)

and if needed the suggested modules:
- matplotlib (>=1.1.1)
- pyenchant (>=1.1)
- pip (>=18)

Should the package pkg_resources be missing in your setup (e.g. on Ubuntu),
then you may need to reinstall pip for Python3.

### With pip

The example installs the dependencies for the current user. Make sure that
you are using the Python3 version of pip.

```bash
pip3 install --user requirements.txt
```

## Getting the bleeding edge version from the code repository

Note that there may unfixed bugs if you use the latest repository version.
You may want to check the CI, which comprises unit tests at
`https://gitlab.com/pyspread/pyspread/pipelines`.

Get the latest tarball or zip at https://gitlab.com/pyspread/pyspread or
clone the git repo at `https://gitlab.com/pyspread/pyspread.git`

# Starting pyspread

With an installation via pip, distutils or your OS's installer, simply run
```
$ pyspread
```
from any directory.

In order to start pyspread without installation directly from the cloned
repository or the extracted tarball or zip, run
```
$ ./bin/pyspread
```
or
```
$ python -m pyspread
```
inside the top directory.

# Contribute

## Issues

Please submit issues in the gitlab issue tracker at
- https://gitlab.com/pyspread/pyspread/issues

## Code

Commit your changes, push them into your fork and send a pull request.

This page gives an overview how to do this:
- https://help.github.com/articles/fork-a-repo

You can find more more details about code organization at
- https://pyspread.gitlab.io/pyspread/
