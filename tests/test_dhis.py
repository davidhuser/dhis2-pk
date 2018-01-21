import pytest

from pk.core.dhis import Dhis
from pk.core.exceptions import ClientException


def test_no_api_version():
    dhis = Dhis(server='play.dhis2.org/demo', username='admin', password='district', api_version=None)
    assert dhis.api_url == 'https://play.dhis2.org/demo/api'


def test_https_in_url():
    dhis = Dhis(server='https://play.dhis2.org/demo', username='admin', password='district', api_version=None)
    assert dhis.api_url.startswith('https://')


def test_demo_server_200():
    dhis = Dhis(server='play.dhis2.org/demo', username='admin', password='district', api_version=None)
    response = dhis.get(endpoint='me')
    assert response['email'] == 'someone@dhis2.org'


def test_api_version():
    dhis = Dhis(server='play.dhis2.org/demo', username='admin', password='district', api_version=27)
    assert dhis.api_url == 'https://play.dhis2.org/demo/api/27'


def test_localhost_url():
    dhis = Dhis(server='localhost:8080', username='admin', password='district', api_version=None)
    assert dhis.api_url.startswith('http://localhost:8080')


def test_double_https_url():
    dhis = Dhis(server='https://play.dhis2.org/demo', username='admin', password='district', api_version=None)
    assert dhis.api_url == 'https://play.dhis2.org/demo/api'


def test_localhost_ip():
    dhis = Dhis(server='127.0.0.1:8080', username='admin', password='district', api_version=None)
    assert dhis.api_url == 'http://127.0.0.1:8080/api'


def test_url_with_api():
    with pytest.raises(ClientException):
        Dhis(server='play.dhis2.org/demo/api', username='admin', password='district', api_version=None)
