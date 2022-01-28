#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
import os
import random
import sys
import time
import uuid

from dhis2 import Api, setup_logger, logger, is_valid_uid, RequestException, generate_uid

try:
    from common.utils import create_api, file_timestamp, write_csv
    from common.exceptions import PKClientException
except (SystemError, ImportError):
    from src.common.utils import create_api, file_timestamp, write_csv
    from src.common.exceptions import PKClientException


def random_year() -> list:
    """Return a list of years ending with this year"""
    today = datetime.date.today()
    start_year = int(today.strftime("%Y"))
    return [start_year - 2, start_year - 1, start_year]


def random_date():
    """Get a random date between January 1 of this year and today"""
    today = datetime.date.today()
    start_year = int(today.strftime("%Y"))
    start_date = datetime.date(start_year, 1, 1)
    end_date = today
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + datetime.timedelta(days=random_number_of_days)


def human_size(bytes_num: int, units=None):
    """ Returns a human readable string representation of bytes """
    units = [' bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'] if units is None else units
    return str(bytes_num) + units[0] if bytes_num < 1024 else human_size(bytes_num >> 10, units[1:])


def get_today():
    """Return today in YYYY-MM-DD format"""
    return datetime.datetime.today().strftime('%Y-%m-%d')


def fake_data_program(uid: str, amount: int, api: Api):
    """Import fake events"""
    metadata = api.get(f'programs/{uid}', params={
        'fields': 'id,name,organisationUnits,'
                  'programStages[programStageDataElements[dataElement[id,valueType,optionSet[options[code]]]]]'}).json()

    logger.info(f"Program: {metadata['name']}")
    time.sleep(4)

    data_elements = {
        de['dataElement']['id']: de['dataElement']['valueType']
        for de in metadata['programStages'][0]['programStageDataElements']
    }

    data_elements_options = {}
    for de in metadata['programStages'][0]['programStageDataElements']:
        if 'optionSet' in de['dataElement']:
            data_element_uid = de['dataElement']['id']
            data_elements_options[data_element_uid] = [o['code'] for o in de['dataElement']['optionSet']['options']]

    org_units = {ou['id'] for ou in metadata['organisationUnits']}

    aocs = {
        coc['categoryOptions'][0]['id'] for coc
        in api.get(
            f'programs/{uid}',
            params={'fields': 'id,name,categoryCombo[categoryOptionCombos[categoryOptions]]'}
        ).json()['categoryCombo']['categoryOptionCombos']
    }

    payload = {"events": []}
    for i in range(amount):
        event = {
            "event": generate_uid(),
            "program": uid,
            "orgUnit": random.choice(list(org_units)),
            "eventDate": random_date().strftime('%Y-%m-%d'),
            "status": "COMPLETED",
            "completedDate": get_today(),
            "dataValues": [],
            "attributeCategoryOptions": random.choice(list(aocs))
            # "coordinate": {
            #     "latitude": round(random.uniform(4, 13), 3),
            #     "longitude": round(random.uniform(2.7, 14.5), 3), # Nigeria
            # }
        }

        for de_uid, de_value_type in data_elements.items():
            dv_value = None

            if de_uid in data_elements_options:
                dv_value = random.choice(data_elements_options[de_uid])
            else:
                if de_value_type in ('INTEGER_POSITIVE', 'INTEGER'):
                    dv_value = random.randint(1, 300)
                elif de_value_type == 'INTEGER_ZERO_OR_POSITIVE':
                    dv_value = random.randint(0, 300)
                elif de_value_type == 'NUMBER':
                    dv_value = round(random.uniform(0, 100), 3)
                elif de_value_type == 'BOOLEAN':
                    dv_value = random.choice([True, False])
                elif de_value_type in ('LONG_TEXT', 'TEXT'):
                    dv_value = str(uuid.uuid4())
                elif de_value_type == 'TRUE_ONLY':
                    if random.choice([True, False]):
                        dv_value = 'true'
                elif de_value_type == 'PERCENTAGE':
                    dv_value = random.randint(0, 100)
                elif de_value_type == 'ORGANISATION_UNIT':
                    dv_value = random.choice(list(org_units))
                elif de_value_type == 'URL':
                    dv_value = "https://{}.com".format(uuid.uuid4())
                else:
                    logger.warning(f"Not supported valueType: {de_value_type}")
                    continue
            if dv_value:
                event['dataValues'].append({
                    "dataElement": de_uid,
                    "value": dv_value
                })

        payload["events"].append(event)

    amount = len(payload['events'])

    filename = f'fake_data_events_{uid}_{get_today()}.json'
    with open(filename, 'w') as f:
        json.dump(payload, f)

    logger.info("Fake data file stored: {}".format(filename))
    logger.info("File has around {} events and a file size of ca. {}".format(amount, human_size(
        os.path.getsize(filename))))

    if amount < 5000:
        logger.info("Importing data...")
        try:
            r = api.post('events', data=payload)
        except RequestException as e:
            logger.error(e)
        else:
            logger.info(f"Imported {len(payload['events'])} FAKE events.")
            logger.info(r.json().get('message'))
            resp = r.json().get('response')
            resp.pop('importOptions', None)
            resp.pop('importSummaries', None)
            logger.info(resp)
    else:
        logger.warning("Did not attempt to import due to large file size. "
                       "Import via Import/Export app in DHIS2 or decrease the amount of events.")


def fake_data_dataset(uid: str, amount: int, api: Api):
    """Import fake data value sets"""
    data_elements = {
        de['id']: de['valueType']
        for de in api.get_paged(
            'dataElements',
            params={'fields': 'id,name,valueType'},
            merge=True,
            page_size=300
        ).get('dataElements')
    }

    dvs_template = api.get(f'dataSets/{uid}/dataValueSet').json()

    assigned_org_units = {
        ou['id'] for ou in
        api.get(
            f'dataSets/{uid}',
            params={'fields': 'id,name,organisationUnits[id]'}
        ).json().get('organisationUnits', [])
    }

    payload = {"dataValues": []}

    metadata = api.get(f'dataSets/{uid}', params={'fields': 'id,name,periodType'}).json()
    dataset_name = metadata['name']
    period_type = metadata['periodType']

    logger.info(f"Dataset: {dataset_name}")

    aocs = {
        coc['id'] for coc in api.get(
            f'dataSets/{uid}',
            params={'fields': 'id,name,categoryCombo[categoryOptionCombos]'}
        ).json()['categoryCombo']['categoryOptionCombos']
    }

    for i in range(amount):
        for dv in dvs_template['dataValues']:
            dv_de = dv['dataElement']
            dv_coc = dv['categoryOptionCombo']

            de_value_type = data_elements[dv_de]
            if de_value_type in ('INTEGER_POSITIVE', 'INTEGER'):
                dv_value = random.randint(1, 30000)
            elif de_value_type == 'INTEGER_ZERO_OR_POSITIVE':
                dv_value = random.randint(0, 30000)
            elif de_value_type == 'NUMBER':
                dv_value = round(random.uniform(0, 100), 3)
            elif de_value_type == 'BOOLEAN':
                dv_value = random.choice([True, False])
            elif de_value_type in ('LONG_TEXT', 'TEXT'):
                dv_value = str(uuid.uuid4())
            elif de_value_type == 'TRUE_ONLY':
                if random.choice([True, False]):
                    dv_value = True
                else:
                    continue
            elif de_value_type == 'PERCENTAGE':
                dv_value = random.randint(0, 100)
            elif de_value_type == 'URL':
                dv_value = "https://{}.com".format(uuid.uuid4())
            else:
                logger.warning(f"Not supported valueType: {de_value_type}")
                continue

            if period_type == 'Yearly':
                dv_period = random.choice(random_year())
            elif period_type == 'Monthly':
                random_month = random_date().strftime('%Y%m')
                dv_period = f"{random_month}"
            elif period_type == 'Quarterly':
                quarter = random.choice([1, 2, 3, 4])
                year = random.choice(random_year())
                dv_period = f"{year}Q{quarter}"
            else:
                raise ValueError(f"Not supported period: {period_type}")

            payload['dataValues'].append(
                {
                    "dataElement": dv_de,
                    "categoryOptionCombo": dv_coc,
                    "period": dv_period,
                    "value": dv_value,
                    "orgUnit": random.choice(list(assigned_org_units)),
                    "attributeOptionCombo": random.choice(list(aocs))
                }
            )

    amount = len(payload['dataValues'])

    filename = f'fake_data_dataset_{uid}_{get_today()}.json'
    with open(filename, 'w') as f:
        json.dump(payload, f)

    logger.info("Fake data file stored: {}".format(filename))
    logger.info("File has around {} data values and a file size of ca. {}".format(amount, human_size(
        os.path.getsize(filename))))

    if amount < 100000:
        logger.info("Importing data...")
        try:
            r = api.post('dataValueSets', data=payload)
        except RequestException as e:
            logger.error(e)
        else:
            logger.info(r.json().get('description'))
            logger.info(r.json().get('importCount'))
    else:
        logger.warning("Did not attempt to import due to large file size. "
                       "Import via Import/Export app in DHIS2 or decrease the amount of data values.")


def main(args, password):
    setup_logger(include_caller=False)

    api = create_api(server=args.server, username=args.username, password=password)

    if not is_valid_uid(args.uid):
        logger.error(f"Not a valid UID: '{args.uid}'. Must be a UID of an event program or data set.")
        sys.exit(1)

    if not 0 < args.amount <= 100000:
        logger.error(f"Amount must be between 1 and 100'000")
        sys.exit(1)

    logger.warning(f"This script will import FAKE data to {api.base_url}")

    uid = args.uid
    data_type = None

    try:
        api.get(f'dataSets/{uid}', params={'fields': 'id,name'})
        data_type = 'dataSets'
    except RequestException as e:
        if e.code == 404:
            try:
                program_info = api.get(f'programs/{uid}', params={'fields': 'id,name,programType'}).json()
                if program_info['programType'] != 'WITHOUT_REGISTRATION':
                    logger.error("Cannot support Tracker programs yet.")
                    sys.exit(1)
                data_type = 'programs'
            except RequestException as e:
                if e.code == 404:
                    logger.error(f"Could not find dataSet or program with UID '{uid}'")

    if data_type == 'programs':
        fake_data_program(uid=args.uid, api=api, amount=args.amount)
    else:
        fake_data_dataset(uid=args.uid, api=api, amount=args.amount)
