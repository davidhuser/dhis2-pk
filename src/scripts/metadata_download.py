#!/usr/bin/env python

"""
metadata
~~~~~~~~~~~~~~~~~
Download metadata from the commandline
"""

import argparse
import codecs
import json
import traceback
import requests

from src.core.dhis import Dhis
from src.core.helpers import properties_to_remove, csv_import_objects
from src.core.logger import *


class Downloader(Dhis):

    def get(self, endpoint, file_type='json', params=None, compressed=False):
        url = '{}/{}.{}'.format(self.api_url, endpoint, file_type)

        log_debug(u"GET: {} - parameters: {}".format(url, json.dumps(params)))

        try:
            req = requests.get(url, params=params, auth=self.auth)
        except requests.RequestException as e:
            self.abort(req)

        log_debug(u"URL: {}".format(req.url))

        if req.status_code == 200:
            log_debug(u"RESPONSE: {}".format(req.text))
            if compressed:
                return req.content
            elif file_type == 'json':
                return req.json()
            else:
                return req.text
        else:
            self.abort(req)

    def get_metadata(self, o_type, o_filter, file_type, fields, compressed, dhis_version):

        if o_type in {'dataSets', 'programs', 'categoryCombos'}:
            print("Looking for export {} with dependencies? "
                  "Look at docs.dhis2.org > Dev guide > 'Metadata export with dependencies'".format(o_type))
        if file_type == 'csv':
            print("WARNING: CSV file needs to be edited correctly before importing.")
            if o_type not in csv_import_objects:
                print("WARNING: {} cannot be imported to DHIS2 directly with CSV files.".format(o_type))

        params = {o_type: True}

        if compressed:
            if file_type != 'csv':
                file_type += ".gz"
            else:
                print("Can't zip CSVs.")

        # DHIS 2.22 and older
        if dhis_version < 23:
            params['assumeTrue'] = False
            endpoint = 'metaData'
            if fields or o_filter:
                print("Can't filter objects or fields on metadata export in version 2.{}".format(dhis_version))

        # DHIS 2.23 and newer
        else:
            if fields:
                params['fields'] = fields
            else:
                to_remove = ",!{}".format(",!".join(properties_to_remove))
                params['fields'] = ":owner{}".format(to_remove)
            if o_filter:
                params['filter'] = o_filter
            if dhis_version == 24:
                endpoint = '23/metadata'
            else:
                endpoint = '{}/metadata'.format(dhis_version)

        return self.get(endpoint=endpoint, file_type=file_type, params=params, compressed=compressed)


def parse_args():
    file_types = ['json', 'xml', 'csv']

    parser = argparse.ArgumentParser(description="Download metadata")
    parser.add_argument('-s', dest='server', action='store', help="Server, e.g. play.dhis2.org/demo", required=True)
    parser.add_argument('-t', dest='object_type', action='store', required=True,
                        help="DHIS2 object types to get, e.g. -t=dataElements")
    parser.add_argument('-f', dest='object_filter', action='store', help="Object filter, e.g. -f='name:like:Acute'",
                        required=False)
    parser.add_argument('-e', dest='fields', action='store', help="Fields to include, e.g. -f='id,name'",
                        required=False)
    parser.add_argument('-y', dest='file_type', action='store', help="File format, defaults to JSON", required=False,
                        choices=file_types, default='json')
    parser.add_argument('-z', dest='compress', action='store_true', help="Compress/zip download", default=False,
                        required=False)
    parser.add_argument('-u', dest='username', action='store', help="DHIS2 username", required=True)
    parser.add_argument('-p', dest='password', action='store', help="DHIS2 password", required=True)
    parser.add_argument('-d', dest='debug', action='store_true', default=False, required=False,
                        help="Debug flag - writes more info to log file")

    return parser.parse_args()


def main():
    args = parse_args()
    init_logger(args.debug)
    log_start_info(__file__)

    if args.object_filter:
        o_filter = args.object_filter.decode()
    else:
        o_filter = None

    dhis = Downloader(server=args.server, username=args.username, password=args.password, api_version=None)
    version = dhis.get_dhis_version()
    o_type = dhis.get_all_object_type(args.object_type)

    data = dhis.get_metadata(o_type=o_type, o_filter=o_filter, file_type=args.file_type, fields=args.fields,
                             compressed=args.compress, dhis_version=version)

    if args.compress and args.file_type != 'csv':
            fn_file_type = "{}.gz".format(args.file_type)
    else:
        fn_file_type = args.file_type
    if o_filter:
        # replace special characters in filter for file name
        remove = ":^!$"
        filter_sanitized = o_filter
        for char in remove:
            filter_sanitized = filter_sanitized.replace(char, "-")
        file_name = "metadata-{}_{}_{}.{}".format(o_type, dhis.file_timestamp, filter_sanitized, fn_file_type)
    else:
        file_name = "metadata-{}_{}.{}".format(o_type, dhis.file_timestamp, fn_file_type)

    # saving the file depending on format
    try:
        if args.compress:
            with codecs.open(file_name, 'wb') as zip_file:
                zip_file.write(data)
        else:
            if args.file_type == 'json':
                # https://stackoverflow.com/questions/12309269/how-do-i-write-json-data-to-a-file-in-python
                with open(file_name, 'wb') as json_file:
                    json.dump(data, codecs.getwriter('utf-8')(json_file), ensure_ascii=False, indent=4)
            elif args.file_type == 'xml':
                with codecs.open(file_name, 'wb', encoding='utf-8') as xml_file:
                    xml_file.write(data)
            elif args.file_type == 'csv':
                with codecs.open(file_name, 'wb', encoding='utf-8') as csv_file:
                    csv_file.write(data)
        log_info(u"+++ Success! {} file exported to {}".format(args.file_type.upper(), file_name))
    except Exception as e:
        try:
            os.remove(file_name)
        except OSError:
            pass
        log_info("{}\n{}".format(e, traceback.print_exc()))


if __name__ == "__main__":
    main()
