# Python 3.11.0 Build Summary

This document summarizes the steps taken to build and install Python 3.11.0 from source.

## 1. Download the Source Code

**Command:**
```bash
curl -O https://www.python.org/ftp/python/3.11.0/Python-3.11.0.tgz
ls -lh Python-3.11.0.tgz
```

**Output:**
```
-rw-rw-r-- 1 jules jules 26M Jan 12 21:59 Python-3.11.0.tgz
```
**Verification:** Download OK.

## 2. Verify the Downloaded File

**Command:**
```bash
file ~/python-build/Python-3.11.0.tgz
```

**Output:**
```
/home/jules/python-build/Python-3.11.0.tgz: gzip compressed data, max compression, from Unix, original size modulo 2^32 98867200
```
**Verification:** Download OK.

## 3. Extract the Source Code

**Command:**
```bash
tar -xzf ~/python-build/Python-3.11.0.tgz -C ~/python-build && ls -l ~/python-build
```

**Output:**
```
total 25724
drwxr-xr-x 17 jules jules     4096 Oct 24  2022 Python-3.11.0
-rw-rw-r--  1 jules jules 26333656 Jan 12 21:59 Python-3.11.0.tgz
```
**Verification:** Extraction OK.

## 4. Verify the Extracted Source Code

**Command:**
```bash
cd ~/python-build/Python-3.11.0 && ls && head -n 5 README.rst
```

**Output:**
```
Doc
Grammar
Include
LICENSE
Lib
Mac
Makefile
Makefile.pre
Makefile.pre.in
Misc
Modules
Objects
PC
PCbuild
Parser
Programs
Python
README.rst
Tools
_bootstrap_python
aclocal.m4
build
config.guess
config.log
config.status
config.sub
configure
configure.ac
install-sh
libpython3.11.a
platform
profile-run-stamp
pybuilddir.txt
pyconfig.h
pyconfig.h.in
python
python-config
python-config.py
python-gdb.py
setup.py
This is Python version 3.11.0
=============================

.. image:: https://github.com/python/cpython/workflows/Tests/badge.svg
   :alt: CPython build status on GitHub Actions
```
**Verification:** Extraction OK.

## 5. Configure the Build Environment

**Command:**
```bash
cd ~/python-build/Python-3.11.0 && ./configure --enable-optimizations --with-ensurepip=install --prefix=/usr/local/python311
```

**Output:**
(Output truncated for brevity)
```
configure: creating ./config.status
config.status: creating Makefile.pre
config.status: creating Misc/python.pc
config.status: creating Misc/python-embed.pc
config.status: creating Misc/python-config.sh
config.status: creating Modules/Setup.bootstrap
config.status: creating Modules/Setup.stdlib
config.status: creating Modules/ld_so_aix
config.status: creating pyconfig.h
config.status: pyconfig.h is unchanged
configure: creating Modules/Setup.local
configure: creating Makefile
```
**Verification:** Configure OK.

## 6. Compile and Install Python

**Command:**
```bash
cd ~/python-build/Python-3.11.0 && make -j$(nproc) && sudo make altinstall
```

**Output:**
(Output truncated for brevity)
```
running install_lib
...
running install_scripts
...
Requirement already satisfied: setuptools in /usr/local/python311/lib/python3.11/site-packages (65.5.0)
Requirement already satisfied: pip in /usr/local/python311/lib/python3.11/site-packages (22.3)
```
**Verification:** Compile and install OK.

## 7. Verify the Final Python Installation

**Commands:**
```bash
/usr/local/python311/bin/python3.11 --version
/usr/local/python311/bin/pip3.11 --version
/usr/local/python311/bin/python3.11 -m ensurepip --upgrade
```

**Output:**
```
Python 3.11.0
pip 22.3 from /usr/local/python311/lib/python3.11/site-packages/pip (python 3.11)
Defaulting to user installation because normal site-packages is not writeable
Looking in links: /tmp/tmpjesuxl82
Requirement already satisfied: setuptools in /usr/local/python311/lib/python3.11/site-packages (65.5.0)
Requirement already satisfied: pip in /usr/local/python311/lib/python3.11/site-packages (22.3)
```
**Verification:** Installation OK.
