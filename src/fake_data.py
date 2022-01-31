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


def random_data_value(value_type: str, org_units: list) -> str:
    """Return a random data value based on the DHIS2 data element valueType"""
    if value_type in ('INTEGER_POSITIVE', 'INTEGER'):
        return str(abs(int(random.gauss(100, 49))))
    elif value_type == 'INTEGER_ZERO_OR_POSITIVE':
        return str(abs(int(random.gauss(200, 49))))
    elif value_type == 'NUMBER':
        return str(int(random.gauss(100, 49)))
    elif value_type == 'BOOLEAN':
        return str(bool(random.getrandbits(1))).lower()
    elif value_type in ('LONG_TEXT', 'TEXT'):
        return str(uuid.uuid4())[:8]
    elif value_type == 'TRUE_ONLY':
        return 'true' if bool(random.getrandbits(1)) else None
    elif value_type == 'NEGATIVE_INTEGER':
        return str(random.randint(-1000, -1))
    elif value_type == 'PERCENTAGE':
        return str(random.randint(0, 100))
    elif value_type == 'UNIT_INTERVAL':
        return str(round(random.uniform(0, 1), 4))
    elif value_type == 'ORGANISATION_UNIT':
        return random.choice(org_units)
    elif value_type == 'URL':
        return f"https://{str(uuid.uuid4())[:8]}.org/"
    elif value_type == 'DATE':
        return str(random_date().strftime('%Y-%m-%d'))
    elif value_type == 'DATETIME':
        return str(random_time().strftime('%Y-%m-%dT%H:%M:%S.000000'))
    elif value_type == 'TIME':
        return str(random_time().strftime('%M:%S'))
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

    # load program metadata
    metadata = api.get(f'programs/{uid}', params={
        'fields': 'id,name,organisationUnits,'
                  'programStages[programStageDataElements[dataElement[id,valueType,optionSet[options[code]]]]]'}).json()

    logger.info("Generating random fake data.")
    logger.info(f"Event program: name='{metadata['name']}' uid='{metadata['id']}'")

    # map data element to its valueType
    de_valuetype_map = {
        de['dataElement']['id']: de['dataElement']['valueType']
        for de in metadata['programStages'][0]['programStageDataElements']
    }

    # map data elements to available options
    data_elements_options = {}
    for de in metadata['programStages'][0]['programStageDataElements']:
        if 'optionSet' in de['dataElement']:
            data_element_uid = de['dataElement']['id']
            data_elements_options[data_element_uid] = [o['code'] for o in de['dataElement']['optionSet']['options']]

    # load the program's assigned metadata
    org_units = [ou['id'] for ou in metadata['organisationUnits']]
    if not org_units:
        logger.error("Data set is not assigned to any org unit")
        sys.exit(1)

    # load the program's category combo > attribute options
    attribute_options = [
        coc['categoryOptions'][0]['id'] for coc
        in api.get(
            f'programs/{uid}',
            params={'fields': 'id,name,categoryCombo[categoryOptionCombos[categoryOptions]]'}
        ).json()['categoryCombo']['categoryOptionCombos']
    ]

    # create events (without data values yet)
    payload = {"events": []}
    for _ in range(amount):
        event = {
            "event": generate_uid(),
            "program": uid,
            "orgUnit": random.choice(org_units),
            "eventDate": random_date().strftime('%Y-%m-%d'),
            "status": "COMPLETED",
            "storedBy": "fake-data",
            "completedDate": get_today(),
            "dataValues": [],
            "attributeCategoryOptions": random.choice(attribute_options),
            "geometry": {
                "type": "Point",
                "coordinates": [
                    str(round(random.uniform(4, 13), 3)),
                    str(round(random.uniform(2.7, 14.5), 3))
                ]
            }
        }

        # create the event's data values
        for de_uid, de_value_type in de_valuetype_map.items():
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

    file_size = os.path.getsize(filename)
    logger.info(f"Event count: {len(payload['events'])}")
    logger.info(f"Event file: {filename}")
    logger.info(f"Event file size: {human_size(file_size)}")

    if file_size > 20 ** 7:
        logger.warning("File size exceeds 20MB. Consider reducing the amount.")

    time.sleep(3)

    # async event import
    job_uid = api.post(
        'events',
        data=payload,
        params={'async': 'true', 'payloadFormat': 'json'}
    ).json()['response']['id']
    logger.info(f"Event import job started: {job_uid} - waiting...")
    while True:
        ping = api.get(f'system/tasks/EVENT_IMPORT/{job_uid}')
        ping.raise_for_status()
        done = [item for item in ping.json() if item['completed'] is True and 'Import done' in item['message']]
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

    # load the data set name and periodType
    metadata = api.get(f'dataSets/{uid}', params={'fields': 'id,name,periodType'}).json()
    logger.info("Generating random fake data")
    logger.info(f"Data Set: name='{metadata['name']}' uid='{metadata['id']}'")

    # load the DataValueSet template
    dvs_template = api.get(f'dataSets/{uid}/dataValueSet').json()

    # load DE.uid : DE.valueType dict
    de_valuetype_map = {
        de['id']: de['valueType']
        for de in api.get_paged(
            'dataElements',
            params={'fields': 'id,name,valueType', 'filter': 'domainType:eq:AGGREGATE'},
            merge=True,
            page_size=300
        ).get('dataElements')
    }

    # load the data set's org units
    org_units = [
        ou['id'] for ou in
        api.get(
            f'dataSets/{uid}',
            params={'fields': 'id,name,organisationUnits[id]'}
        ).json().get('organisationUnits', [])
    ]
    if not org_units:
        logger.error("Data set is not assigned to any org unit")
        sys.exit(1)

    payload = {"dataValues": []}

    # load the data set's category combo > attribute options
    attribute_option_combos = [
        coc['id'] for coc in api.get(
            f'dataSets/{uid}',
            params={'fields': 'id,name,categoryCombo[categoryOptionCombos]'}
        ).json()['categoryCombo']['categoryOptionCombos']
    ]

    # log a warning in case of huge amount of data values
    possible_data_values = amount * len(dvs_template['dataValues'])
    if possible_data_values > 10000:
        logger.warning(f"Lots of data values: {possible_data_values}. Consider reducing the amount.")
        time.sleep(6)

    # create as many data value set templates as given as argument
    for _ in range(amount):
        for dv in dvs_template['dataValues']:
            de_uid = dv['dataElement']
            de_value_type = de_valuetype_map[de_uid]
            payload['dataValues'].append(
                {
                    "dataElement": de_uid,
                    "categoryOptionCombo": dv['categoryOptionCombo'],
                    "period": random_period(metadata['periodType']),
                    "value": random_data_value(de_value_type, org_units),
                    "storedBy": "fake-data",
                    "orgUnit": random.choice(org_units),
                    "attributeOptionCombo": random.choice(attribute_option_combos)
                }
            )

    filename = f'fake_data_dataset_{uid}_{get_today()}.json'
    with open(filename, 'w') as f:
        json.dump(payload, f)

    dv_amount = len(payload['dataValues'])
    file_size = os.path.getsize(filename)
    logger.info(f"Amount (-n): {amount}")
    logger.info(f"Data value count: {dv_amount}")
    logger.info(f"Data file: {filename}")
    logger.info(f"Data file size: {human_size(file_size)}")

    if file_size > 20**7:
        logger.warning("File size exceeds 20MB. Consider reducing the amount.")

    time.sleep(3)

    preheat_cache = dv_amount > 3000
    # async data import
    job_uid = api.post(
        'dataValueSets', data=payload,
        params={'skipAudit': 'true', 'async': 'true', 'preheatCache': str(preheat_cache).lower()}
    ).json()['response']['id']
    logger.info(f"Data import job started: {job_uid} - waiting...")
    while True:
        ping = api.get(f'system/tasks/DATAVALUE_IMPORT/{job_uid}')
        ping.raise_for_status()
        done = [item for item in ping.json() if item['completed'] is True and item['message'] == 'Import done']
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

    logger.warning(f"URL: {api.base_url}")

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
        else:
            logger.error(e)
            sys.exit(1)

    if data_type == 'events':
        fake_data_program(uid=args.uid, api=api, amount=args.amount)
    elif data_type == 'dataSets':
        fake_data_dataset(uid=args.uid, api=api, amount=args.amount)
    else:
        raise ValueError("Not supported data type")