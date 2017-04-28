import pytest

from src.scripts.indicator_definitions import *


@pytest.fixture()
def dhis():
    return Dhis(server='play.dhis2.org/demo', username='admin', password='district', api_version=None)


def test_get_indicators_with_filter(dhis):
    filter = 'name:like:ANC'
    assert True


