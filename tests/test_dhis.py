import pytest

from pk.core.dhis import Dhis
from pk.core.exceptions import ClientException


@pytest.fixture()
def dhis():
    return Dhis(server='play.dhis2.org/demo', username='admin', password='district', api_version=None)


@pytest.fixture()
def dhis_with_api_version():
    return Dhis(server='play.dhis2.org/demo', username='admin', password='district', api_version=26)


@pytest.fixture()
def dhis_with_https():
    return Dhis(server='https://play.dhis2.org/demo', username='admin', password='district', api_version=None)


@pytest.fixture()
def dhis_without_https():
    return Dhis(server='http://play.dhis2.org/demo', username='admin', password='district', api_version=None)


@pytest.fixture()
def dhis_localhost():
    return Dhis(server='localhost:8080', username='admin', password='district', api_version=None)


@pytest.fixture()
def dhis_localhost_ip():
    return Dhis(server='127.0.0.1:8080', username='admin', password='district', api_version=None)


def test_demo_server_200(dhis):
    response = dhis.get(endpoint='me')
    assert response['email'] == 'someone@dhis2.org'


def test_api_version(dhis_with_api_version):
    assert dhis_with_api_version.api_url == 'https://play.dhis2.org/demo/api/26'


def test_no_api_version(dhis):
    assert dhis.api_url == 'https://play.dhis2.org/demo/api'


def test_https_in_url(dhis):
    assert dhis.api_url.startswith('https://')


def test_localhost_url(dhis_localhost):
    assert dhis_localhost.api_url.startswith('http://localhost:8080')


def test_double_https_url(dhis_with_https):
    assert dhis_with_https.api_url == 'https://play.dhis2.org/demo/api'


def test_localhost_ip(dhis_localhost_ip):
    assert dhis_localhost_ip.api_url == 'http://127.0.0.1:8080/api'


def test_url_with_api():
    with pytest.raises(ClientException):
        Dhis(server='play.dhis2.org/demo/api', username='admin', password='district', api_version=None)
