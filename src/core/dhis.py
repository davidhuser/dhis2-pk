#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import sys
from datetime import datetime

import requests

from src.core.helpers import shareable_object_types, all_object_types
from src.core.logger import *


class Dhis(object):
    """Core class for accessing DHIS2 web API"""

    public_access = {
        'none': '--------',
        'readonly': 'r-------',
        'readwrite': 'rw------'
    }

    def __init__(self, server, username, password, api_version):
        if '/api' in server:
            print('Please do not specify /api/ in the server argument: e.g. -s=play.dhis2.org/demo')
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
        server_name = server.replace('https://', '').replace('.', '-').replace('/', '-')
        self.file_timestamp = '{}_{}'.format(now, server_name)

    def get(self, endpoint, file_type='json', params=None):
        url = '{}/{}.{}'.format(self.api_url, endpoint, file_type)

        log_debug(u"GET: {} - parameters: {}".format(url, json.dumps(params)))

        try:
            req = requests.get(url, params=params, auth=self.auth)
        except requests.RequestException as e:
            self.abort(req)

        log_debug(u"URL: {}".format(req.url))

        if req.status_code == 200:
            log_debug(u"RESPONSE: {}".format(req.text))
            if file_type == 'json':
                return req.json()
            else:
                return req.text
        else:
            self.abort(req)

    def post(self, endpoint, params, payload):
        url = '{}/{}'.format(self.api_url, endpoint)
        log_debug(u"POST: {} \n parameters: {} \n payload: {}".format(url, json.dumps(params), json.dumps(payload)))

        try:
            req = requests.post(url, params=params, json=payload, auth=self.auth)
        except requests.RequestException as e:
            self.abort(req)

        log_debug(req.url)

        if req.status_code != 200:
            self.abort(req)

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
    def abort(request):
        msg = u"++++++ ERROR ++++++\n+++HTTP code: {}\n+++URL: {}\n+++RESPONSE: {}"
        log_info(msg.format(request.status_code, request.url, request.text))
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
