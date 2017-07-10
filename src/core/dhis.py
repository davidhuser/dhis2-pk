#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import sys
from datetime import datetime

import requests

from src.core.logger import *
from src.core.static import shareable_object_types, all_object_types


class ConfigException(Exception):
    pass


class Config(object):
    def __init__(self, server, username, password, api_version):

        if not server:
            dish = self.get_dish()
            server = dish['server']
            username = dish['username']
            password = dish['password']

        if '/api' in server:
            print('Please do not specify /api/ in the server url')
            sys.exit()
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
            raise ConfigException("dish.json not found - searches in $DHIS_HOME and in your home folder")

        with open(dish_location, 'r') as f:
            dish = json.load(f)
            valid = False
            try:
                valid = all([dish['dhis'], dish['dhis']['baseurl'], dish['dhis']['username'], dish['dhis']['password']])
            except KeyError:
                pass
            if not valid:
                raise ConfigException(
                    "dish.json found at {} but not configured according dish.json format "
                    "(see github.com/baosystems/dish#Configuration)".format(dish_location))

            return {'baseurl': dish['dhis']['baseurl'], 'username': dish['dhis']['username'],
                    'password': dish['dhis']['password']}


class Dhis(Config):
    public_access = {
        'none': '--------',
        'readonly': 'r-------',
        'readwrite': 'rw------'
    }

    def __init__(self, server, username, password, api_version):
        Config.__init__(self, server, username, password, api_version)

    def get(self, endpoint, file_type='json', params=None):
        url = '{}/{}.{}'.format(self.api_url, endpoint, file_type)

        log_debug(u"GET: {} - parameters: {}".format(url, json.dumps(params)))

        try:
            r = requests.get(url, params=params, auth=self.auth)
        except requests.RequestException:
            self.abort(r)

        log_debug(u"URL: {}".format(r.url))

        if r.status_code == 200:
            log_debug(u"RESPONSE: {}".format(r.text))
            if file_type == 'json':
                return r.json()
            else:
                return r.text
        else:
            self.abort(r)

    def post(self, endpoint, params, payload):
        url = '{}/{}'.format(self.api_url, endpoint)
        log_debug(u"POST: {} \n parameters: {} \n payload: {}".format(url, json.dumps(params), json.dumps(payload)))

        try:
            r = requests.post(url, params=params, json=payload, auth=self.auth)
        except requests.RequestException as e:
            self.abort(r)

        log_debug(r.url)

        if r.status_code != 200:
            self.abort(r)

    def post_file(self, endpoint, filename, content_type):
        url = '{}/{}'.format(self.api_url, endpoint)
        headers = {"Content-Type": content_type}
        fileread = open(filename, 'rb').read()
        r = requests.post(url, data=fileread, headers=headers, auth=self.auth)
        if r.status_code not in range(200, 204):
            self.abort(r)

    def get_dhis_version(self):
        """ return DHIS2 verson (e.g. 26) as integer"""
        response = self.get(endpoint='system/info', file_type='json')

        # remove -snapshot for play.dhis2.org/dev
        snapshot = '-SNAPSHOT'
        version = response.get('version')
        if snapshot in version:
            version = version.replace(snapshot, '')

        return int(version.split('.')[1])

    @staticmethod
    def abort(r):
        msg = u"++++++ ERROR ++++++\nHTTP code: {}\nURL: {}\nRESPONSE:\n{}"
        log_info(msg.format(r.status_code, r.url, r.text))
        sys.exit()

    @staticmethod
    def get_shareable_object_type(passed_name):
        obj_types = shareable_object_types()
        valid_obj_name1 = obj_types.get(passed_name.lower(), None)
        if valid_obj_name1 is None:
            valid_obj_name2 = obj_types.get(passed_name[:-1].lower(), None)
            if valid_obj_name2 is None:
                log_info(u"+++ Could not find a shareable object type for -t='{}'".format(passed_name))
                sys.exit()
            else:
                return valid_obj_name2
        return valid_obj_name1

    @staticmethod
    def get_all_object_type(passed_name):
        obj_types = all_object_types()
        valid_obj_name1 = obj_types.get(passed_name.lower(), None)
        if valid_obj_name1 is None:
            valid_obj_name2 = obj_types.get(passed_name[:-1].lower(), None)
            if valid_obj_name2 is None:
                log_info(u"+++ Could not find a valid object type for -t='{}'".format(passed_name))
                sys.exit()
            else:
                return valid_obj_name2
        return valid_obj_name1
