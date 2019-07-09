# Installation

## Prerequisites

Have you already a running Python installation? If not check this guide: https://realpython.com/installing-python

## Installation with pip

Installation with [pip](https://pip.pypa.io/en/stable/installing)
(python package manager, see if it is installed: `pip -V` or `pip3 -V`)

Best way is to install it for your user only:

```bash
pip install dhis2-pocket-knife --user --upgrade
```

if it failed, it might be that you are running `pip3` - repeat the same with `pip3` instead of `pip`.

With providing the `--user` argument you don't clutter your system installation (which might be really bad), but it might be that you see a message like *dhis2-pk-share could not be found*. To fix
this you need to modify your Python PATH - see below. 

## Fixing Python PATH for macOS and Linux

### PYTHONVERSION

First, you need to find out what Python version you are running:

```bash
python3 -V || python -V || python2 -V
```
This is returning somethine like `Python 3.5.3`, meaning you have a `$PYTHONVERSION` with value `3.5`.

### USER
Then you should find out which user you are:
```bash
echo $USER
```
Meaning you have a `$USER` with value `david`.

### Export

Now we know what to replace: replace `$USER` with your macOS username from above (e.g. `david`) and `$PYTHONVERSION` from above (e.g. `3.5`) and paste it into your terminal and hit ENTER. If it shows the help page all is set.

```bash
echo 'export PATH=$PATH:/Users/$USER/Library/Python/$PYTHONVERSION/bin' >> ~/.bash_profile && source ~/.bash_profile && dhis2-pk-share --help
```

## Windows

This guide can help: https://realpython.com/installing-python/#windows - make sure you tick the box for "Add Python3.X to path".


## System-wide installation

To install it system-wide **(really not recommended)**:

```bash
sudo -H pip install dhis2-pocket-knife
```

# Updating dhis2-pocket-knife

## Current version

```bash
pip show dhis2-pocket-knife
```

and compare it with the most recent release (the orange PyPI label here: https://github.com/davidhuser/dhis2-pk)

## Update it
```bash
pip install dhis2-pocket-knife --user --upgrade
```

# Usage

## Help text
Besides the documentation, you can also issue any command with the `--help` flage, e.g. `dhis2-pk-share --help`.

## dish.json
If you're using the same server over and over, place file called
`dish.json` in your home folder and leave out `server`, `username`,
`password` in all commands. 
Make sure that file is kept in a secure place. (`chmod 0600 dish.json`)

So: either pass arguments for a server / username / password or
make it read from a `dish.json` file as described in
[davidhuser/dhis2.py](https://github.com/davidhuser/dhis2.py#load-authentication-from-file).

## Windows

Windows is supported, however _do not use single apostrophes_ `'`

 * use PowerShell OR 
 * use double apostrophes `"` OR 
 * use no apostrophes at all (no problem when not having whitespaces in filters)
