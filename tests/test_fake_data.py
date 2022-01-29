import pytest

import datetime

from src.fake_data import (
    random_date,
    random_data_value,
    random_time,
    random_period,
    last_years
)


def test_random_date():
    o = random_date()
    assert isinstance(o, datetime.date)
    assert o <= datetime.date.today()


def test_random_time():
    o = random_time()
    assert isinstance(o, datetime.datetime)
    assert isinstance(o, datetime.date)
    assert o <= datetime.datetime.today()


def test_random_period_yearly():
    o = random_period('Yearly')
    assert isinstance(o, str)
    assert 2000 < int(o) < 2050


def test_random_period_quarterly():
    o = random_period('Quarterly')
    assert isinstance(o, str)
    assert 'Q' in o
    assert 2000 < int(o.split('Q')[0]) < 2050
    assert 1 <= int(o.split('Q')[1]) <= 4


def test_random_period_monthly():
    o = random_period('Monthly')
    assert isinstance(o, str)
    assert len(o) == 6
    assert 2000 < int(o[:-2]) < 2050
    assert 1 <= int(o[4:]) <= 12


def test_last_years():
    o = last_years(years=-3)
    assert all(isinstance(y, int) for y in o)
    assert all(2000 < y < 2050 for y in o)