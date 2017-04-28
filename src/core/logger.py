import logging
import logging.handlers
import os

from src.__init__ import ROOT_DIR


def get_pkg_version():
    __version__ = ''
    with open(os.path.join(ROOT_DIR, 'version.py')) as f:
        exec (f.read())
    return __version__


def init_logger(debug_flag):
    logformat = '%(levelname)s:%(asctime)s %(message)s'
    datefmt = '%Y-%m-%d-%H:%M:%S'
    filename = 'dhis2-pk.log'
    debug_flag = debug_flag

    # only log 'requests' library's warning messages (including errors)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    if debug_flag:
        logging.basicConfig(filename=filename, level=logging.DEBUG, format=logformat,
                            datefmt=datefmt)
    else:
        logging.basicConfig(filename=filename, level=logging.INFO, format=logformat,
                            datefmt=datefmt)


def log_start_info(script_path):
    script_name = os.path.splitext(os.path.basename(script_path))[0]
    logging.info(u"\n\n===== dhis2-pocket-knife v{} - {} =====".format(get_pkg_version(), script_name))


def log_info(text):
    if isinstance(text, Exception):
        logging.debug(repr(text))
    else:
        try:
            print(text)
        except UnicodeDecodeError:
            print(text.encode('utf-8'))
        finally:
            logging.info(text.encode('utf-8'))


def log_debug(text):
    logging.debug(text.encode('utf-8'))
