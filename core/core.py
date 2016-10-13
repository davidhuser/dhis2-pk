#!/usr/bin/env python

import json
import logging
import sys

import requests


class Dhis(object):
    """Core class for accessing DHIS2 web API"""

    objects_types = ['categories', 'categoryOptionGroupSets', 'categoryOptionGroups', 'categoryOptionSets',
                     'categoryOptions', 'charts', 'constants', 'dashboards', 'dataApprovalLevels',
                     'dataElementGroupSets', 'dataElementGroups', 'dataElements', 'dataSets', 'documents',
                     'eventCharts', 'eventReports', 'indicatorGroupSets', 'indicatorGroups', 'indicators',
                     'interpretations', 'maps', 'option', 'optionSets', 'organisationUnitGroupSets',
                     'organisationUnitGroups', 'programIndicators', 'programs', 'reportTables', 'reports',
                     'sqlViews', 'trackedEntityAttributes', 'userRoles', 'validationRuleGroups']

    public_access = {
        'none': '--------',
        'readonly': 'r-------',
        'readwrite': 'rw------'
    }

    def __init__(self, server, username, password, debug_flag):
        if "http://" not in server and "https://" not in server:
            self.server = "https://" + server
        else:
            self.server = server
        self.auth = (username, password)
        self.log = Logger(debug_flag)

    def get(self, endpoint, params):
        url = self.server + "/api/" + endpoint + ".json"
        self.log.debug("{} - parameters: {}".format(url, json.dumps(params)))

        req = requests.get(url, params=params, auth=self.auth)
        self.log.debug(req.url)

        if req.status_code == 200:
            self.log.debug(req.text)
            return req.json()
        else:
            self.log.info(req.text)
            sys.exit()

    def post(self, endpoint, params, payload):
        url = self.server + "/api/" + endpoint
        self.log.debug("{} - parameters: {} \n payload: {}".format(url, json.dumps(params), json.dumps(payload)))

        req = requests.post(url, params=params, json=payload, auth=self.auth)
        self.log.debug(req.url)

        if req.status_code != 200:
            msg = "[{}] {}".format(str(req.status_code), req.url)
            print(msg)
            self.log.info(msg)
            self.log.debug(req.text)
            sys.exit()

    def delete(self, endpoint, uid):
        url = "{}/api/{}/{}".format(self.server, endpoint, uid)

        req = requests.delete(url, auth=self.auth)

        msg = "[{}] {}".format(str(req.status_code), req.url)
        print(msg)
        self.log.info(msg)
        if req.status_code != 200 or req.status_code != 204:
            print(req.text)
            self.log.info(req.text)
            sys.exit()


class Logger(object):
    """Core class for Logging to file"""

    def __init__(self, debug_flag):
        format = '%(levelname)s:%(asctime)s %(message)s'
        datefmt = '%Y-%m-%d-%H:%M:%S'
        filename = 'dhis2-pk.log'
        self.debug_flag = debug_flag

        # only log 'requests' library's warning messages (including errors)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        if self.debug_flag:
            logging.basicConfig(filename=filename, level=logging.DEBUG, format=format,
                                datefmt=datefmt)
            logging.debug("***** START *****")
        else:
            logging.basicConfig(filename=filename, level=logging.INFO, format=format,
                                datefmt=datefmt)
            logging.info("***** START *****")

    def info(self, text):
        print(text)
        logging.info(text)

    def debug(self, text):
        logging.debug(text)
