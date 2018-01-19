#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import json

import requests
from logzero import logger

from .config import Config
from .exceptions import APIException, ClientException
from .static import shareable_object_types, all_object_types


class DhisAccess(object):

    def __init__(self, server, username, password, api_version):
        cfg = Config(server, username, password, api_version)
        self.api_url = cfg.api_url
        self.auth = cfg.auth
        self.session = requests.Session()
        self.file_timestamp = cfg.file_timestamp

    def get(self, endpoint, file_type='json', params=None):
        url = '{}/{}.{}'.format(self.api_url, endpoint, file_type)

        logger.debug(u"GET: {} - parameters: {}".format(url, json.dumps(params)))
        r = self.session.get(url, params=params, auth=self.auth)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise APIException(e)
        else:
            logger.debug(u"RESPONSE: {}".format(r.text))
            if file_type == 'json':
                return r.json()
            else:
                return r.text

    def post(self, endpoint, params, payload):
        url = '{}/{}'.format(self.api_url, endpoint)
        logger.debug(u"POST: {} \n parameters: {} \n payload: {}".format(url, json.dumps(params), json.dumps(payload)))

        r = self.session.post(url, params=params, json=payload, auth=self.auth)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise APIException(e)
        else:
            logger.debug(u"RESPONSE: {}".format(r.text))

    def put(self, endpoint, params, payload):
        url = '{}/{}'.format(self.api_url, endpoint)
        logger.debug(u"PUT: {} \n parameters: {} \n payload: {}".format(url, json.dumps(params), json.dumps(payload)))

        r = self.session.put(url, params=params, json=payload, auth=self.auth)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise APIException(e)
        else:
            logger.debug(u"RESPONSE: {}".format(r.text))

    def post_file(self, endpoint, filename, content_type):
        url = '{}/{}'.format(self.api_url, endpoint)
        headers = {"Content-Type": content_type}
        file_read = open(filename, 'rb').read()
        r = self.session.post(url, data=file_read, headers=headers, auth=self.auth)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise APIException(e)
        else:
            logger.debug(u"RESPONSE: {}".format(r.text))

    def validate(self, obj_type, payload):
        url = '{}/schemas/{}'.format(self.api_url, obj_type)
        logger.debug(u"VALIDATE: {} payload: {}".format(url, json.dumps(payload)))

        r = self.session.post(url, json=payload, auth=self.auth)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise APIException(e)
        else:
            logger.debug(u"RESPONSE: {}".format(r.text))

    def get_dhis_version(self):
        """ return DHIS2 version (e.g. 26) as integer"""
        response = self.get(endpoint='system/info', file_type='json')

        # remove -snapshot for play.dhis2.org/dev
        snapshot = '-SNAPSHOT'
        version = response.get('version')
        if snapshot in version:
            version = version.replace(snapshot, '')
        return int(version.split('.')[1])

    @staticmethod
    def get_shareable_object_type(passed_name):
        obj_types = shareable_object_types()
        valid_obj_name1 = obj_types.get(passed_name.lower(), None)
        if valid_obj_name1 is None:
            valid_obj_name2 = obj_types.get(passed_name[:-1].lower(), None)
            if valid_obj_name2 is None:
                raise ClientException(u"Could not find a shareable object type for -t='{}'".format(passed_name))
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
                raise ClientException(u"Could not find a valid object type for -t='{}'".format(passed_name))
            else:
                return valid_obj_name2
        return valid_obj_name1
