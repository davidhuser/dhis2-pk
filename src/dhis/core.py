#!/usr/bin/env python

import json
import logging
import os
import sys

import requests

from src.dhis.collection_names import object_types
from src.__init__ import ROOT_DIR


def get_pkg_version():
    __version__ = ''
    with open(os.path.join(ROOT_DIR, 'version.py')) as f:
        exec (f.read())
    return __version__


class Dhis(object):
    """Core class for accessing DHIS2 web API"""

    public_access = {
        'none': '--------',
        'readonly': 'r-------',
        'readwrite': 'rw------'
    }

    def __init__(self, server, username, password, api_version, debug_flag):
        if not server.startswith('https://'):
            server = "https://{}".format(server)
        self.auth = (username, password)
        if api_version:
            self.api_url = "{}/api/{}".format(server, api_version)
        else:
            self.api_url = "{}/api".format(server)
        self.log = Logger(debug_flag)

    def get_object_type(self, passed_name):
        valid_obj_name = object_types().get(passed_name.lower(), None)
        if valid_obj_name is None:
            real = object_types().get(passed_name[:-1].lower(), None)
            if real is None:
                self.log.info('Could not find a valid object type for -f="{}"'.format(passed_name))
                sys.exit()
        return valid_obj_name

    def get(self, endpoint, params=None):
        url = "{}/{}.json".format(self.api_url, endpoint)

        self.log.debug("GET: {} - parameters: {}".format(url, json.dumps(params)))

        try:
            req = requests.get(url, params=params, auth=self.auth)
        except requests.RequestException as e:
            self.log.info(e)
            sys.exit("Error: Check dhis2-pk.log or use debug argument -d")

        self.log.debug("URL: {}".format(req.url))

        if req.status_code == 200:
            try:
                self.log.debug("RESPONSE: {}".format(req.text))
            except UnicodeEncodeError:
                self.log.debug("RESPONSE: {}".format(req.text.encode('ascii', 'replace').decode('ascii')))
            finally:
                return req.json()
        else:
            self.log.info(req.text)
            sys.exit("Error: Check dhis2-pk.log or use debug argument -d")

    def post(self, endpoint, params, payload):
        url = "{}/{}".format(self.api_url, endpoint)
        self.log.debug("POST: {} \n parameters: {} \n payload: {}".format(url, json.dumps(params), json.dumps(payload)))

        try:
            req = requests.post(url, params=params, json=payload, auth=self.auth)
        except requests.RequestException as e:
            self.log.info(e)
            sys.exit("Error: Check dhis2-pk.log or use debug argument -d")

        self.log.debug(req.url)

        if req.status_code != 200:
            msg = "[{} {}] {}".format(str(req.status_code), req.url, req.text)
            self.log.info(msg)
            self.log.debug(req.text)
            sys.exit()

    def delete(self, endpoint, uid):
        url = "{}/{}/{}".format(self.api_url, endpoint, uid)

        try:
            req = requests.delete(url, auth=self.auth)
        except requests.RequestException as e:
            self.log.info(e)
            sys.exit("Error: Check dhis2-pk.log or use debug argument -d")

        msg = "[{}] {}".format(str(req.status_code), req.url)
        self.log.info(msg)
        if req.status_code != 200 or req.status_code != 204:
            self.log.info(req.text)
            sys.exit()


class Logger(object):
    """Core class for Logging to file"""

    def __init__(self, debug_flag):
        logformat = '%(levelname)s:%(asctime)s %(message)s'
        datefmt = '%Y-%m-%d-%H:%M:%S'
        filename = 'dhis2-pk.log'
        self.debug_flag = debug_flag

        # only log 'requests' library's warning messages (including errors)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        if self.debug_flag:
            logging.basicConfig(filename=filename, level=logging.DEBUG, format=logformat,
                                datefmt=datefmt)
        else:
            logging.basicConfig(filename=filename, level=logging.INFO, format=logformat,
                                datefmt=datefmt)

    @staticmethod
    def startinfo(script_path):
        script_name = os.path.splitext(os.path.basename(script_path))[0]
        logging.info("\n+++ dhis2-pocket-knife v{} +++ {}".format(get_pkg_version(), script_name))

    @staticmethod
    def info(text):
        print(text)
        logging.info(text)

    @staticmethod
    def debug(text):
        logging.debug(text)
