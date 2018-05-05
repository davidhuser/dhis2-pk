import logging
import os
import errno

import logzero


def create_folders(file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


def init(logging_to_file='', debug=False):
    # Default logger
    log_format = '%(color)s* %(levelname)1s  %(asctime)s%(end_color)s %(message)s'
    formatter = logzero.LogFormatter(fmt=log_format)
    logzero.setup_default_logger(formatter=formatter)

    if logging_to_file:
        create_folders(logging_to_file)
        print(u"Logging to {}".format(logging_to_file))

        log_format_no_color = '* %(levelname)1s  %(asctime)s %(message)s [%(module)s:%(lineno)d]'
        formatter_no_color = logzero.LogFormatter(fmt=log_format_no_color)

        # Log rotation of 20 files for 10MB each
        logzero.logfile(logging_to_file, formatter=formatter_no_color, loglevel=logging.INFO, maxBytes=int(1e7),
                        backupCount=20)

    else:
        logzero.logfile(None)

    if debug:
        logzero.loglevel(logging.DEBUG)
    else:
        logzero.loglevel(logging.INFO)
