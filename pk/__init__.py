import logging
import os

import logzero


def init_logger(logging_to_file=False, debug=False):

    log_format = '%(color)s[%(asctime)s %(levelname)s]%(end_color)s %(message)s'
    formatter = logzero.LogFormatter(fmt=log_format)
    logzero.setup_default_logger(formatter=formatter)

    if logging_to_file:
        logfilename = '/var/log/dhis2-pk.log'
        logzero.logfile(logfilename, loglevel=logging.ERROR)
    elif debug:
        logzero.loglevel(logging.DEBUG)
    else:
        logzero.loglevel(logging.INFO)
    logzero.logfile(None)


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
