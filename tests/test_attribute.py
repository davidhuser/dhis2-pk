import os

import pytest

from dhis2 import load_csv

from src.attributes import validate_csv, create_or_update_attribute_values
from src.common.exceptions import PKClientException

TEST_ATTRIBUTE_UID = 'M8fCOxtkURr'

PATH = os.path.join('tests', 'testdata')


def test_csv_file_valid():
    f = list(load_csv(path=os.path.join(PATH, 'valid.csv')))
    assert validate_csv(f)


def test_csv_duplicate_objects():
    f = list(load_csv(path=os.path.join(PATH, 'duplicates.csv')))
    with pytest.raises(PKClientException):
        validate_csv(f)


def test_csv_no_valid_uid():
    f = list(load_csv(path=os.path.join(PATH, 'no_valid_uid.csv')))
    with pytest.raises(PKClientException):
        validate_csv(f)


def test_csv_no_valid_headers():
    f = list(load_csv(path=os.path.join(PATH, 'headers.csv')))
    with pytest.raises(PKClientException):
        validate_csv(f)


@pytest.fixture
def user_with_attributevalue():
    u = {
        "id": "DXyJmlo9rge",
        "firstName": "John",
        "surname": "Barnes",
        "email": "john@hmail.com",
        "attributeValues": [
            {
                "lastUpdated": "2017-09-05T18:55:58.633",
                "created": "2017-09-05T18:55:58.631",
                "value": "hello",
                "attribute": {
                    "id": TEST_ATTRIBUTE_UID
                }
            }
        ],
        "teiSearchOrganisationUnits": [],
        "organisationUnits": [
            {
                "id": "DiszpKrYNg8"
            }
        ],
        "dataViewOrganisationUnits": [
            {
                "id": "YuQRtpLP10I"
            }
        ]
    }
    return u


def test_attribute_value_updated(user_with_attributevalue):
    new_value = 'NEW123'
    updated = create_or_update_attribute_values(obj=user_with_attributevalue, attribute_value=new_value,
                                                attribute_uid=TEST_ATTRIBUTE_UID)
    assert len(updated['attributeValues']) == 1
    assert new_value in [x['value'] for x in updated['attributeValues'] if x['attribute']['id'] == TEST_ATTRIBUTE_UID]

    # assert other values have not changed
    updated.pop('attributeValues')
    pairs = zip(updated, user_with_attributevalue)
    assert any(x != y for x, y in pairs)


@pytest.fixture
def user_without_attributevalues():
    u = {
        "id": "DXyJmlo9rge",
        "firstName": "John",
        "surname": "Barnes",
        "email": "john@hmail.com",
        "teiSearchOrganisationUnits": [],
        "organisationUnits": [
            {
                "id": "DiszpKrYNg8"
            }
        ],
        "dataViewOrganisationUnits": [
            {
                "id": "YuQRtpLP10I"
            }
        ]
    }
    return u


def test_attribute_new_value(user_without_attributevalues):
    new_value = 'NEW123'
    updated = create_or_update_attribute_values(obj=user_without_attributevalues, attribute_value=new_value,
                                                attribute_uid=TEST_ATTRIBUTE_UID)
    assert len(updated['attributeValues']) == 1
    assert new_value in [x['value'] for x in updated['attributeValues'] if x['attribute']['id'] == TEST_ATTRIBUTE_UID]


@pytest.fixture
def user_added_attributevalues():
    u = {
        "id": "DXyJmlo9rge",
        "firstName": "John",
        "surname": "Barnes",
        "email": "john@hmail.com",
        "attributeValues": [
            {
                "lastUpdated": "2017-09-05T18:55:58.633",
                "created": "2017-09-05T18:55:58.631",
                "value": "hello",
                "attribute": {
                    "id": TEST_ATTRIBUTE_UID
                }
            },
            {
                "lastUpdated": "2017-09-05T18:55:58.633",
                "created": "2017-09-05T18:55:58.631",
                "value": "somethingother",
                "attribute": {
                    "id": "DiszpKrYNg6"
                }
            }
        ],
        "teiSearchOrganisationUnits": [],
        "organisationUnits": [
            {
                "id": "DiszpKrYNg8"
            }
        ],
        "dataViewOrganisationUnits": [
            {
                "id": "YuQRtpLP10I"
            }
        ]
    }
    return u


def test_attribute_added_value(user_added_attributevalues):
    new_value = 'NEW123'
    updated = create_or_update_attribute_values(obj=user_added_attributevalues, attribute_value=new_value,
                                                attribute_uid=TEST_ATTRIBUTE_UID)
    assert len(updated['attributeValues']) == 2
    assert set([x['attribute']['id'] for x in updated['attributeValues']]) == {TEST_ATTRIBUTE_UID, 'DiszpKrYNg6'}
    assert new_value in [x['value'] for x in updated['attributeValues'] if x['attribute']['id'] == TEST_ATTRIBUTE_UID]
