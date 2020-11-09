#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

try:
    from src.attributes import main as attributes_main
    from src.css import main as css_main
    from src.indicators import main as indicators_main
    from src.integrity import main as integrity_main
    from src.share import main as share_main
    from src.userinfo import main as userinfo_main
    from src.cmdline_parser import (
        parse_args_share,
        parse_args_userinfo,
        parse_args_integrity,
        parse_args_indicators,
        parse_args_css,
        parse_args_attributes,
        pk_general_help
    )
except ImportError:
    from attributes import main as attributes_main
    from css import main as css_main
    from indicators import main as indicators_main
    from integrity import main as integrity_main
    from share import main as share_main
    from userinfo import main as userinfo_main
    from cmdline_parser import (
        parse_args_share,
        parse_args_userinfo,
        parse_args_integrity,
        parse_args_indicators,
        parse_args_css,
        parse_args_attributes,
        pk_general_help
    )

# valid scripts
scripts = {
    'attribute-setter',
    'data-integrity',
    'indicator-definitions',
    'post-css',
    'share',
    'userinfo'
}


def python2_notice():
    if sys.version_info.major == 2:
        sys.exit("dhis2-pocket-knife cannot support Python 2. "
                 "Please upgrade to Python 3.6+ as Python 2 has reached the end of life.")


def pocketknife_run():
    """
    Entry point.
    First, verify that pocket-knife is called with arguments and the script called is valid
    Then get the arguments and call the script's main function.
    """
    python2_notice()
    if not sys.argv or len(sys.argv) < 2 or sys.argv[1] not in scripts:
        pk_general_help()
    else:
        args = sys.argv
        script_name = args[1]
        if script_name == 'attribute-setter':
            args, password = parse_args_attributes(args[2:])
            attributes_main(args, password)
        if script_name == 'data-integrity':
            args, password = parse_args_integrity(args[2:])
            integrity_main(args, password)
        if script_name == 'indicator-definitions':
            args, password = parse_args_indicators(args[2:])
            indicators_main(args, password)
        if script_name == 'post-css':
            args, password = parse_args_css(args[2:])
            css_main(args, password)
        if script_name == 'share':
            args, password = parse_args_share(args[2:])
            share_main(args, password)
        if script_name == 'userinfo':
            args, password = parse_args_userinfo(args[2:])
            userinfo_main(args, password)


if __name__ == '__main__':
    pocketknife_run()
