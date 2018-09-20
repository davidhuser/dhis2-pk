#!/bin/bash

# Run from Repo root

URL='play.dhis2.org/dev'
USERNAME='admin'
PW='district'

echo -e '\nuserinfo'
pipenv run python pk/userinfo.py -s ${URL} -u ${USERNAME} -p ${PW}

echo -e '\nshare'
pipenv run python pk/share.py -s ${URL} -u ${USERNAME} -p ${PW} -f 'id:eq:P3jJH5Tu5VC' -t dataelement -a readonly -g 'name:like:Admin' readwrite -g 'name:like:Research' readwrite

echo -e '\nindicator-definition'
pipenv run python pk/indicators.py -s ${URL} -u ${USERNAME} -p ${PW} -t indicators

echo -e '\nattribute-setter'
pipenv run python pk/attributes.py -s ${URL} -u ${USERNAME} -p ${PW} -c tests/testdata/attribute-manual.csv -t organisationUnits -a n2xYlNbsfko

echo -e '\npost-css'
pipenv run python pk/css.py -s ${URL} -u ${USERNAME} -p ${PW} -c tests/testdata/style.css

echo -e '\ndata-integrity'
pipenv run python pk/integrity.py -s ${URL} -u ${USERNAME} -p ${PW}

echo -e '\nclean-up...'
rm -f indicators-201*.csv
rm -f userinfo-201*.csv