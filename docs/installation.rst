Installation and Usage
======================


Installation
-------------

Installation with `pip <https://pip.pypa.io/en/stable/installing>`__ (python package manager, see if it is installed: ``pip -V``)

Best way is to install it for your user only:

.. code:: bash

    pip install dhis2-pocket-knife --user

This way you don't clutter your system installation, but it might be that you see a message like *dhis2-pk-share could not be found*.
To fix this you need to modify your Python PATH.

**macOS**

Replace ``$USER`` with your macOS username:

.. code:: bash

    echo 'export PATH=$PATH:/Users/$USER/Library/Python/2.7/bin' >> ~/.bash_profile && source ~/.bash_profile


To install it system-wide **(not recommended)**:

.. code:: bash

    sudo -H pip install dhis2-pocket-knife


Updating
--------

.. code:: bash

    pip install dhis2-pocket-knife --upgrade


Usage
------

If you're using the same server over and over, place file called ``dish.json`` in your home folder and leave out ``server``, ``username``, ``password`` in all commands. Make sure that file is kept in a secure place!
So: either pass arguments for a server / username / password
or make it read from a ``dish.json`` file as described in `davidhuser/dhis2.py <https://github.com/davidhuser/dhis2.py>`__.


Get help on using arguments, e.g. ``dhis2-pk-share --help``
