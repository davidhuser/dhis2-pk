|pocket-knife| dhis2-pk
=======================

|PyPi| |Downloads| |Travis| |Exe| |PythonVersion|

Command-line tools for `DHIS2 <https://dhis2.org>`__.


-  Mass **sharing** via filtering `(docs) <https://github.com/davidhuser/dhis2-pk/blob/master/docs/share.md>`__
-  Download **indicator definitions** to CSV `(docs)  <https://github.com/davidhuser/dhis2-pk/blob/master/docs/indicator-definitions.md>`__
-  Download **user information** to CSV `(docs) <https://github.com/davidhuser/dhis2-pk/blob/master/docs/userinfo.md>`__
-  Set **attribute values** with a CSV `(docs) <https://github.com/davidhuser/dhis2-pk/blob/master/docs/attribute-setter.md>`__
-  Additional **data integrity** `(docs) <https://github.com/davidhuser/dhis2-pk/blob/master/docs/data-integrity.md>`__
-  Post a **CSS** style sheet for the login page `(docs) <https://github.com/davidhuser/dhis2-pk/blob/master/docs/post-css.md>`__

Installation
-------------

Note: **Python 3.6+** is required.

The straightforward way is usually:

.. code:: bash

   pip3 install dhis2-pocket-knife --user

If you are on Windows or run into issues,
check the `Installation instructions <https://github.com/davidhuser/dhis2-pk/blob/master/docs/installation.md>`__.

Usage
------

Scripts are invoked by running: ``dhis2-pk <script-name>``, for example:

.. code:: bash

   dhis2-pk share --help

Check out the docs for more details regarding each script.

Changelog
----------

see `Changelog.rst <https://github.com/davidhuser/dhis2-pk/blob/master/Changelog.rst>`__.

----

Under the hood it uses the DHIS2 API wrapper `dhis2.py <https://github.com/davidhuser/dhis2.py>`__.

.. |pocket-knife| image:: https://i.imgur.com/AWrQJ4N.png
    :alt: Pocket Knife

.. |PyPi| image:: https://img.shields.io/pypi/v/dhis2-pocket-knife.svg?label=PyPI
    :alt: pip version
    :target: https://pypi.python.org/pypi/dhis2-pocket-knife
    
.. |Downloads| image:: https://pepy.tech/badge/dhis2-pocket-knife/month
   :target: https://pepy.tech/project/dhis2-pocket-knife
   :alt: Downloads

.. |Travis| image:: https://img.shields.io/travis/davidhuser/dhis2-pk/master.svg
    :alt: Travis CI build status
    :target: https://travis-ci.org/davidhuser/dhis2-pk

.. |Exe| image:: https://github.com/davidhuser/dhis2-pk/workflows/package-exe-for-windows/badge.svg
    :alt: Windows EXE build status
    :target: https://github.com/davidhuser/dhis2-pk/actions?query=workflow%3Apackage-exe-for-windows

.. |PythonVersion| image:: https://img.shields.io/pypi/pyversions/dhis2-pocket-knife.svg
    :alt: PyPI - Python Version

