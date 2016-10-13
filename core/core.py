#!/usr/bin/env python

import logging
import requests
import json
import sys


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

    def __init__(self, server, username, password):
        if "http://" not in server and "https://" not in server:
            self.server = "https://" + server
        else:
            self.server = server
        self.auth = (username, password)
        self.log = Logger()

    def get(self, endpoint, params):
        url = self.server + "/api/" + endpoint + ".json"
        self.log.debug(url + " - parameters: " + json.dumps(params))

        req = requests.get(url, params=params, auth=self.auth)

        if req.status_code == 200:
            self.log.debug(req.text)
            return req.json()
        else:
            self.log.info(req.text)
            sys.exit()

    def post(self, endpoint, params, payload):
        url = self.server + "/api/" + endpoint
        self.log.debug(url + " - parameters: " + json.dumps(params) + " - payload " + json.dumps(payload))

        req = requests.post(url, params=params, json=payload, auth=self.auth)

        if req.status_code != 200:
            msg = "[" + str(req.status_code) + "] " + req.url
            print(msg)
            self.log.info(msg)
            self.log.debug(req.text)
            sys.exit()

    def delete(self, endpoint, uid):
        url = self.server + "/api/" + endpoint + "/" + uid

        req = requests.delete(url, auth=self.auth)

        msg = "[" + str(req.status_code) + "] " + req.url
        print(msg)
        self.log.info(msg)
        if req.status_code != 200 or req.status_code != 204:
            print(req.text)
            self.log.info(req.text)
            sys.exit()


class Logger(object):
    # DEBUG TO LOG FILE FLAG
    debug_flag = False

    def __init__(self):
        format = '%(levelname)s:%(asctime)s %(message)s'
        datefmt = '%Y-%m-%d-%H:%M:%S'
        filename = 'dhis2-pocket-knife.log'

        # only log 'requests' library's warning messages (including errors)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        if Logger.debug_flag:
            logging.basicConfig(filename=filename, level=logging.DEBUG, format=format,
                                datefmt=datefmt)
            logging.debug("********************************")

        else:
            logging.basicConfig(filename=filename, level=logging.INFO, format=format,
                                datefmt=datefmt)
            logging.info("********************************")

    def info(self, text):
        print(text)
        logging.info(text)

    def debug(self, text):
        logging.debug(text)
