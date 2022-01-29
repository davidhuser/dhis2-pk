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


def last_years(years: int = -2) -> list:
    """Return a list of years ending with this year"""
    if years > 0:
        raise ValueError("Years must be 0 or smaller")
    this_year = int(datetime.date.today().strftime("%Y"))
    year_list = [this_year]
    for i in range(years, 0, 1):
        year_list.append(this_year + i)
    return sorted(year_list, reverse=True)


def random_date() -> datetime.date:
    """Get a random date between January 1 of last year and today"""
    today = datetime.date.today()
    start_year = int(today.strftime("%Y")) - 1
    start_date = datetime.date(start_year, 1, 1)
    end_date = today
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + datetime.timedelta(days=random_number_of_days)


def random_time() -> datetime:
    """Return random datetime up to 101 days ago"""
    return datetime.datetime.now() - datetime.timedelta(
        days=random.randint(1, 100),
        hours=random.randint(1, 24),
        minutes=random.randint(1, 60),
        seconds=random.randint(1, 60)
    )


def random_data_value(value_type: str, org_units: set) -> str:
    """Return a random data value based on the DHIS2 data element valueType"""
    if value_type in ('INTEGER_POSITIVE', 'INTEGER'):
        return str(random.randint(1, 1000))
    elif value_type == 'INTEGER_ZERO_OR_POSITIVE':
        return str(random.randint(0, 1000))
    elif value_type == 'NUMBER':
        return str(round(random.uniform(0, 100), 3))
    elif value_type == 'BOOLEAN':
        return str(random.choice([True, False])).lower()
    elif value_type in ('LONG_TEXT', 'TEXT'):
        return str(uuid.uuid4())[:8]
    elif value_type == 'TRUE_ONLY':
        return 'true' if random.choice([True, False]) else None
    elif value_type == 'NEGATIVE_INTEGER':
        return str(random.randint(-1000, -1))
    elif value_type == 'PERCENTAGE':
        return str(random.randint(0, 100))
    elif value_type == 'UNIT_INTERVAL':
        return str(round(random.uniform(0, 1), 4))
    elif value_type == 'ORGANISATION_UNIT':
        return random.choice(list(org_units))
    elif value_type == 'URL':
        return f"https://{str(uuid.uuid4())[:8]}.org/"
    elif value_type == 'DATE':
        return str(random_date().strftime('%Y-%m-%d'))
    elif value_type == 'DATETIME':
        return str(random_time().strftime('%Y-%m-%dT%H:%M:%S.000000'))
    elif value_type == 'TIME':
        return str(random_time().strftime('%H:%M:%S.000000'))
    elif value_type == 'EMAIL':
        return "mail@example.org"
    else:
        logger.warning(f"Not supported valueType: {value_type}")


def random_period(period_type: str) -> str:
    """Return a random period based on the DHIS2 period type"""
    if period_type == 'Yearly':
        return str(random.choice(last_years()))
    elif period_type == 'Monthly':
        return str(random_date().strftime('%Y%m'))
    elif period_type == 'Quarterly':
        quarter = random.choice([1, 2, 3, 4])
        year = random.choice(last_years())
        return f"{year}Q{quarter}"
    else:
        raise ValueError(f"Not yet supported period: {period_type}")


def human_size(bytes_num: int, units=None) -> str:
    """ Returns a human readable string representation of bytes """
    units = [' bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'] if not units else units
    return str(bytes_num) + units[0] if bytes_num < 1024 else human_size(bytes_num >> 10, units[1:])


def get_today() -> str:
    """Return today in YYYY-MM-DD format"""
    return datetime.datetime.today().strftime('%Y-%m-%d')


def fake_data_program(uid: str, amount: int, api: Api):
    """Import fake events"""
    metadata = api.get(f'programs/{uid}', params={
        'fields': 'id,name,organisationUnits,'
                  'programStages[programStageDataElements[dataElement[id,valueType,optionSet[options[code]]]]]'}).json()

    logger.info(f"Program: {metadata['name']} ({metadata['id']})")
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

    if not org_units:
        logger.error("Data set is not assigned to any org unit")
        sys.exit(1)

    attribute_options = {
        coc['categoryOptions'][0]['id'] for coc
        in api.get(
            f'programs/{uid}',
            params={'fields': 'id,name,categoryCombo[categoryOptionCombos[categoryOptions]]'}
        ).json()['categoryCombo']['categoryOptionCombos']
    }

    payload = {"events": []}
    for _ in range(amount):
        event = {
            "event": generate_uid(),
            "program": uid,
            "orgUnit": random.choice(list(org_units)),
            "eventDate": random_date().strftime('%Y-%m-%d'),
            "status": "COMPLETED",
            "completedDate": get_today(),
            "dataValues": [],
            "attributeCategoryOptions": random.choice(list(attribute_options)),
            "coordinate": {  # Nigeria
                "latitude": round(random.uniform(4, 13), 3),
                "longitude": round(random.uniform(2.7, 14.5), 3)
            }
        }

        for de_uid, de_value_type in data_elements.items():
            if de_uid in data_elements_options:
                # if DE has a optionSet, choose a random option
                dv_value = random.choice(data_elements_options[de_uid])
            else:
                dv_value = random_data_value(de_value_type, org_units)
            if dv_value:
                event['dataValues'].append({"dataElement": de_uid, "value": dv_value})
        payload["events"].append(event)

    filename = f'fake_data_events_{uid}_{get_today()}.json'
    with open(filename, 'w') as f:
        json.dump(payload, f)

    logger.info("File stored: {}".format(filename))
    logger.info("Events: {} - file size: {}".format(
        len(payload['events']),
        human_size(os.path.getsize(filename))
    ))

    time.sleep(3)

    job_uid = api.post(
        'events',
        data=payload,
        params={'async': 'true', 'payloadFormat': 'json'}
    ).json()['response']['id']
    logger.info(f"Started async events import job {job_uid} - waiting...")
    while True:
        ping = api.get(f'system/tasks/EVENT_IMPORT/{job_uid}').json()
        done = [item for item in ping if item['completed'] is True and 'Import done' in item['message']]
        if done:
            break
        time.sleep(1)
    summary = api.get(f'system/taskSummaries/EVENT_IMPORT/{job_uid}').json()
    summary.pop('responseType', None)
    summary.pop('importSummaries', None)
    summary.pop('total', None)
    status = summary.get('status', 'unknown')
    summary.pop('status', None)
    logger.info(f"{status.capitalize()} - {summary}")


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

    org_units = {
        ou['id'] for ou in
        api.get(
            f'dataSets/{uid}',
            params={'fields': 'id,name,organisationUnits[id]'}
        ).json().get('organisationUnits', [])
    }
    if not org_units:
        logger.error("Data set is not assigned to any org unit")
        sys.exit(1)

    payload = {"dataValues": []}

    metadata = api.get(f'dataSets/{uid}', params={'fields': 'id,name,periodType'}).json()
    logger.info(f"Dataset: {metadata['name']} ({uid})")

    attribute_options = {
        coc['id'] for coc in api.get(
            f'dataSets/{uid}',
            params={'fields': 'id,name,categoryCombo[categoryOptionCombos]'}
        ).json()['categoryCombo']['categoryOptionCombos']
    }

    for i in range(amount):
        for dv in dvs_template['dataValues']:
            de_uid = dv['dataElement']
            de_value_type = data_elements[de_uid]
            payload['dataValues'].append(
                {
                    "dataElement": de_uid,
                    "categoryOptionCombo": dv['categoryOptionCombo'],
                    "period": random_period(metadata['periodType']),
                    "value": random_data_value(de_value_type, org_units),
                    "orgUnit": random.choice(list(org_units)),
                    "attributeOptionCombo": random.choice(list(attribute_options))
                }
            )

    filename = f'fake_data_dataset_{uid}_{get_today()}.json'
    with open(filename, 'w') as f:
        json.dump(payload, f)

    logger.info("File stored: {}".format(filename))
    logger.info("Data values: {} - file size: {}".format(
        len(payload['dataValues']),
        human_size(os.path.getsize(filename))
    ))

    time.sleep(3)

    job_uid = api.post(
        'dataValueSets', data=payload,
        params={'skipAudit': 'true', 'async': 'true', 'preheatCache': 'true'}
    ).json()['response']['id']
    logger.info(f"Started async aggregate data import job {job_uid} - waiting...")
    while True:
        ping = api.get(f'system/tasks/DATAVALUE_IMPORT/{job_uid}').json()
        done = [item for item in ping if item['completed'] is True and item['message'] == 'Import done']
        if done:
            break
        time.sleep(1)
    summary = api.get(f'system/taskSummaries/DATAVALUE_IMPORT/{job_uid}').json()
    logger.info(f"{summary.get('description')} - {summary.get('importCount')}")


def main(args, password):
    setup_logger(include_caller=False)

    api = create_api(server=args.server, username=args.username, password=password)

    if not is_valid_uid(args.uid):
        logger.error(f"Not a valid UID: '{args.uid}'. Must be a UID of an event program or data set.")
        sys.exit(1)

    if not 0 < args.amount <= 100000:
        logger.error(f"Amount must be between 1 and 100000")
        sys.exit(1)

    logger.warning(f"Importing FAKE data to {api.base_url}")

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
                data_type = 'events'
            except RequestException as e:
                if e.code == 404:
                    logger.error(f"Could not find dataSet or program with UID '{uid}'")
        else:
            logger.error(e)
            sys.exit(1)

    if data_type == 'events':
        fake_data_program(uid=args.uid, api=api, amount=args.amount)
    elif data_type == 'dataSets':
        fake_data_dataset(uid=args.uid, api=api, amount=args.amount)
    else:
        raise ValueError("Not supported data type")