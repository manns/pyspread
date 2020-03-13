pyspread
====================

**pyspread** is a non-traditional spreadsheet that is
based on and written in the programming language Python.

It is released under the [GPL v3. LICENSE](LICENSE)

- Homepage: https://pyspread.gitlab.io/
- Repository: https://gitlab.com/pyspread/pyspread
- API Docs: https://pyspread.gitlab.io/pyspread/


# Install

## On Debian testing

On Debian, pyspread is available as a package.
A Python3 version is only available in testing at the moment.

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

#### On Debian unstable:

```bash
su -
apt install python3-pyqt5 python3-pyqt5.qtsvg python3-numpy python3-pyqt5.qtwebengine
apt install python3-matplotlib python3-enchant python3-pip
```

#### With pip

The example installs the dependencies for the current user. Make sure that
you are using the Python3 version of pip.

```bash
pip3 install --user requirements.txt
```

## Pyspread

Get the latest tarball at `https://gitlab.com/pyspread/downloads` or
clone the git repo at `https://gitlab.com/pyspread/pyspread.git`

In order to start pyspread without installation run
```
$ ./pyspread.sh
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
