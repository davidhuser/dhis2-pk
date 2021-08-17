=========
CHANGELOG
=========

0.36.0 (Aug 2021)
-----------------
- Feat: ``data-integrity`` script: check for invalid keywords in Program Rules and Program Rule Variables


0.35.5 (Mar 2021)
------------------
- Feat: ``userinfo`` script: export UIDs when supplying `-i`` flag.
- Feat: ``userinfo`` script: export email and Tracker Search Org units too
- Fix: user-agent fixed

0.35.4 (Feb 2021)
------------------
- Fix: print message for duplicate option codes fixed

0.35.3 (Feb 2021)
------------------
- Feat: check optionSet.options for duplicate codes and invalid sortOrder

0.35.2 (Nov 2020)
------------------
- Fix: inline help text

0.35.1 (Nov 2020)
------------------
- Fix: script entry-points

0.35.0 (Nov 2020)
-----------------
- Rewrote the entry points for scripts ( ``dhis2-pk share ...`` instead of ``dhis2-pk-share ...`` to allow to build executables)
- Added a ``dhis2-pk.exe`` download for Windows (under "Releases")
- Drop support for ``dish.json`` file as it allows clearer help on required arguments, and ``-p`` is optional already to securely set the password
- Drop support for Python 2.7 and Python 3.5
- This changelog

0.32.3 (July 2019)
------------------
- Still supporting Python 2.7

