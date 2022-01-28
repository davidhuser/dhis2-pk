#!/bin/bash

# Run from Repo root:
# bash tests/manual.sh

URL='play.dhis2.org/demo'
USERNAME='admin'
PW='district'

echo '------'
echo $URL
echo '------'

echo -e '\nuserinfo'
pipenv run python src/main.py userinfo -s ${URL} -u ${USERNAME} -p ${PW}

echo -e '\nshare'
pipenv run python src/main.py share -s ${URL} -u ${USERNAME} -p ${PW} -f 'id:eq:P3jJH5Tu5VC' -t dataelement -a readonly -g 'name:like:Admin' readwrite -g 'name:like:Research' readwrite

echo -e '\nshare and extend'
pipenv run python src/main.py share -s ${URL} -u ${USERNAME} -p ${PW} -f 'id:eq:P3jJH5Tu5VC' -t dataelement -g 'name:like:Bo District M&E officers' readonly -e

echo -e '\nindicator-definition'
pipenv run python src/main.py indicator-definitions -s ${URL} -u ${USERNAME} -p ${PW} -t indicators

echo -e '\nattribute-setter'
pipenv run python src/main.py attribute-setter -s ${URL} -u ${USERNAME} -p ${PW} -c tests/testdata/attribute-manual.csv -t organisationUnits -a n2xYlNbsfko

echo -e '\npost-css'
pipenv run python src/main.py post-css -s ${URL} -u ${USERNAME} -p ${PW} -c tests/testdata/style.css

echo -e '\ndata-integrity'
pipenv run python src/main.py data-integrity -s ${URL} -u ${USERNAME} -p ${PW}

echo -e '\nfake-data'
pipenv run python src/main.py fake-data -s ${URL} -u ${USERNAME} -p ${PW} -i q04UBOqq3rp -n 10
pipenv run python src/main.py fake-data -s ${URL} -u ${USERNAME} -p ${PW} -i eZDhcZi6FLP -n 50


echo -e '\nclean-up...'
rm -f indicators-202*.csv
rm -f userinfo-202*.csv
rm -f fake_data_*.csv