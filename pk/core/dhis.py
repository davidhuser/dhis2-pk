#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import json

import requests
from logzero import logger
import six

from .config import Config
from .exceptions import APIException, ClientException


class Dhis(object):

    def __init__(self, server, username, password, api_version):
        cfg = Config(server, username, password, api_version)
        self.api_url = cfg.api_url
        self.dhis_version = self.dhis_version
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

    def dhis_version(self):
        """
        :return: DHIS2 Version as Integer (e.g. 28)
        """
        response = self.get(endpoint='system/info', file_type='json')

        # remove -SNAPSHOT for play.dhis2.org/dev
        version = response.get('version').replace('-SNAPSHOT', '')
        try:
            self.dhis_version = int(version.split('.')[1])
            if self.dhis_version < 22:
                logger.warning("Using DHIS2 Version < 2.22...")
            return self.dhis_version
        except ValueError:
            raise APIException("Could not parse DHIS2 version into an Integer")

    def shareable_objects(self):
        """
        Returns object classes which can be shared
        :return: dict { object name (singular) : object name (plural) }
        """
        params = {
            'fields': 'name,plural,shareable'
        }
        r = self.get(endpoint='schemas', params=params)
        d = {x['name']: x['plural'] for x in r['schemas'] if x['shareable']}
        return d

    def match_shareable(self, argument):
        """
        Match to a valid shareable object. Raise Exception if not found.
        :param argument: Argument for object type desired to share
        :return: tuple(singular, plural) of shareable object type
        """
        shareable = self.shareable_objects()
        for name, plural in six.iteritems(shareable):
            if argument in (name, plural):
                return name, plural
        raise ClientException(u"No shareable object type for '{}'. Shareable are: {}".format(argument, '\n'.join(shareable.values())))
