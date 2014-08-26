import argparse
import os
import json
import logging
import re
import urllib2

from lxml.html import fromstring
from unidecode import unidecode

import sys

root_log = logging.getLogger()
root_log.setLevel(logging.WARN)


class Exception(Exception):
    pass


def diff(original, modified):
    _diff = {
        'added': [],
        'removed': []
    }

    original = json.loads(original)
    modified = json.loads(modified)

    for section in modified['sections']:
        o_section = None
        for s in original['sections']:
            if s['name'] == section['name']:
                o_section = s
        for beverage in section['beverages']:
            o_beverage = None
            for b in o_section['beverages']:
                if b['name'] == beverage['name']:
                    o_beverage = b
            if not o_beverage:
                _diff['added'].append({'section': section['name'], 'beverage': beverage['name']})

    for section in original['sections']:
        m_section = None
        for s in modified['sections']:
            if s['name'] == section['name']:
                m_section = s
        for beverage in section['beverages']:
            m_beverage = None
            for b in m_section['beverages']:
                if b['name'] == beverage['name']:
                    m_beverage = b
            if not m_beverage:
                _diff['removed'].append({'section': section['name'], 'beverage': beverage['name']})

    return _diff


def _log(message, level=logging.INFO):
    root_log.log(level, message)


if __name__ == '__main__':
    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    # Command line arguments
    parser = argparse.ArgumentParser(description='Create a diff from two menu parsed by parse_menu.py.')
    parser.add_argument('original', type=str, help='file path to original menu')
    parser.add_argument('modified', type=str, help='file path to modified menu')
    parser.add_argument('--pretty', action='store_true', help='pretty print JSON output')
    args = parser.parse_args()

    # Get file contents
    if os.path.exists(args.original):
        original_contents = urllib2.urlopen('file:{0}'.format(urllib2.quote(os.path.abspath(args.original)))).read()
    else:
        raise Exception('Unable to open file "{0}".'.format(args.original))
    if os.path.exists(args.modified):
        modified_contents = urllib2.urlopen('file:{0}'.format(urllib2.quote(os.path.abspath(args.modified)))).read()
    else:
        raise Exception('Unable to open file "{0}".'.format(args.modified))

    # Create diff of menus
    menu_diff = diff(original_contents, modified_contents)

    # Output diff as JSON
    if args.pretty:
        print json.dumps(menu_diff, indent=2)
    else:
        print json.dumps(menu_diff)
