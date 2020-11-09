# Installation

## Prerequisites

Have you already a running Python installation? If not check this guide: https://realpython.com/installing-python

Note: due to End-of-life for Python 2, **Python 3.6+ is required.**

## Installation with pip

Installation with [pip](https://pip.pypa.io/en/stable/installing)
(python package manager, see if it is installed: `pip3 -V` or `pip -V`)

Best way is to install it for your user only:

```bash
pip3 install dhis2-pocket-knife --user --upgrade
```

if it failed, it might be that you are running `pip` - repeat the same with `pip` instead of `pip3`.

With providing the `--user` argument you don't clutter your system installation (which might be really bad), but it 
might be that you see a message like `dhis2-pk could not be found. To fix
this you need to modify your Python PATH - see below. 

## Fixing Python PATH for macOS and Linux

### PYTHONVERSION

First, you need to find out what Python version you are running:

```bash
python3 -V || python -V
```
This is returning something like `Python 3.7.9`, meaning you have a `$PYTHONVERSION` with value `3.7`.

### USER

Then you should find out which user you are:

```bash
echo $USER
```
Meaning you have a `$USER` with value `david`.

### Export

Now we know what to replace: replace `$USER` with your macOS username from above (e.g. `david`) and `$PYTHONVERSION` from above (e.g. `3.7`) and paste it into your terminal and hit ENTER. If it shows the help page all is set.

```bash
echo 'export PATH=$PATH:/Users/$USER/Library/Python/$PYTHONVERSION/bin' >> ~/.bash_profile && source ~/.bash_profile && dhis2-pk share --help
```

## Windows

This guide can help: https://realpython.com/installing-python/#windows - make sure you tick the box for "Add Python3.X to path". 
Another hint regarding the usage on Windows is below.


## System-wide installation

To install it system-wide **(really not recommended)**:

```bash
sudo -H pip3 install dhis2-pocket-knife
```

# Updating dhis2-pocket-knife

## Current version

```bash
pip3 show dhis2-pocket-knife
```

and compare it with the most recent release (the orange PyPI label here: https://github.com/davidhuser/dhis2-pk)

## Update it
```bash
pip3 install dhis2-pocket-knife --user --upgrade
```

# Usage

## Help text
Besides the documentation, you can also issue any command with the `--help` flag, e.g. `dhis2-pk share --help`.

## Windows

![package-exe-for-windows](https://github.com/davidhuser/dhis2-pk/workflows/package-exe-for-windows/badge.svg)

On Windows there are two options:

* Either install it with `pip` as well
* Or download a `.exe` with dhis2-pocket-knife from the [releases page.](https://github.com/davidhuser/dhis2-pk/releases), download the ZIP file, extract it, and open a Powershell or CMD.exe and change (`cd`) to the directory. Instead of typing `dhis2-pk share ...`, all commands have an .exe, e.g. `dhis2-pk.exe share ...`. 

In the command-line, _do not use single apostrophes_ `'`

 * use the PowerShell app OR 
 * use double apostrophes `"` OR 
 * use no apostrophes at all (no problem when not having whitespaces in filters)
