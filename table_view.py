import argparse
import os
import json
import logging
import re
import urllib2
from datetime import datetime
import parse_menu

from lxml.html import fromstring
from unidecode import unidecode

import sys

root_log = logging.getLogger()
root_log.setLevel(logging.INFO)

columns = [
    'name',
    'brewery',
    'style',
    'location',
    'alcohol_percentage',
    'size',
    'price',
    'year',
    'section',
]


def menu_to_table(menu):
    menu = json.loads(menu)
    rows = []
    for section in menu['sections']:
        for beverage in section['beverages']:
            # Create dict with all columns
            row = []
            for column in columns:
                try:
                    # Sub winery for brewery if it's a wine
                    if column == 'brewery' and beverage['details']['type'] == 'wine':
                        column = 'winery'
                    row.append(str(beverage['details'][column]))
                except KeyError:
                    row.append('')
            rows.append(row)
    table = '<table>' + "\n"
    table += '<tr><th>' + '</th><th>'.join(columns) + '</th></tr>' + "\n"
    for row in rows:
        table += '<tr><td>' + '</td><td>'.join(row) + '</td></tr>' + "\n"
    table += '</table>' + "\n"
    return table


def _log(message, level=logging.INFO):
    root_log.log(level, message)


if __name__ == '__main__':
    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    # Command line arguments
    parser = argparse.ArgumentParser(description='Generate a simple HTML table view of menu.')
    parser.add_argument('file', type=str, help='file path to menu JSON')
    args = parser.parse_args()

    menu_json = urllib2.urlopen('file:{0}'.format(urllib2.quote(os.path.abspath(args.file)))).read()
    print menu_to_table(menu_json)
