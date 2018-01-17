#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import json
from datetime import datetime

from .exceptions import ClientException


class Config(object):
    def __init__(self, server, username, password, api_version):

        if not server:
            dish = self.get_dish()
            server = dish['baseurl']
            username = dish['username']
            password = dish['password']

        if '/api' in server:
            raise ClientException('Please do not specify /api/ in the server url')
        if server.startswith('localhost') or server.startswith('127.0.0.1'):
            server = 'http://{}'.format(server)
        elif server.startswith('http://'):
            server = server
        elif not server.startswith('https://'):
            server = 'https://{}'.format(server)
        self.auth = (username, password)
        if api_version:
            self.api_url = '{}/api/{}'.format(server, api_version)
        else:
            self.api_url = '{}/api'.format(server)
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.file_timestamp = '{}_{}'.format(now, server.replace('https://', '').replace('.', '-').replace('/', '-'))

    @staticmethod
    def get_dish():

        print("No Server URL given, searching for dish.json ...")

        fn = 'dish.json'
        dish_location = ''

        if 'DHIS_HOME' in os.environ:
            dish_location = os.path.join(os.environ['DHIS_HOME'], fn)
        else:
            home_path = os.path.expanduser(os.path.join("~"))
            for root, dirs, files in os.walk(home_path):
                if fn in files:
                    dish_location = os.path.join(root, fn)
                    break
        if not dish_location:
            raise ClientException("dish.json not found - searches in $DHIS_HOME and in your home folder")

        with open(dish_location, 'r') as f:
            dish = json.load(f)
            valid = False
            try:
                valid = all([dish['dhis'], dish['dhis']['baseurl'], dish['dhis']['username'], dish['dhis']['password']])
            except KeyError:
                pass
            if not valid:
                raise ClientException(
                    "dish.json found at {} but not configured according dish.json format "
                    "(see https://github.com/baosystems/dish#Configuration for details)".format(dish_location))

            return {'baseurl': dish['dhis']['baseurl'],
                    'username': dish['dhis']['username'],
                    'password': dish['dhis']['password']
                    }
