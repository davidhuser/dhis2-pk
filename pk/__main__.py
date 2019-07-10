import sys

from pk.attributes import main as attributes_main
from pk.css import main as css_main
from pk.indicators import main as indicators_main
from pk.integrity import main as integrity_main
from pk.share import main as share_main
from pk.userinfo import main as userinfo_main


def main():
    if len(sys.argv) < 1:
        print("help")
    if sys.argv[1] == 'attributes':
        attributes_main()
    if sys.argv[1] == 'css':
        css_main()
    if sys.argv[1] == 'indicators':
        indicators_main()
    if sys.argv[1] == 'integrity':
        integrity_main()
    if sys.argv[1] == 'share':
        share_main()
    if sys.argv[1] == 'userinfo':
        userinfo_main()
