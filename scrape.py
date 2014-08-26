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

locations = [
    {
        'name': 'Hollywood',
        'url': 'http://www.stoutburgersandbeers.com/hollywood-beer-menu/'
    },
    {
        'name': 'Studio City',
        'url': 'http://www.stoutburgersandbeers.com/studio-city-beer-menu/'
    },
    {
        'name': 'Santa Monica',
        'url': 'http://www.stoutburgersandbeers.com/santa-monica-beer-menu/'
    },
]


def scrape_location(location):
    """
    Scrape the stout menu, parse it into JSON, and cache it by date.

    :param location: Stout location to scrape.
    :type location: dict
    :return:
    :rtype:
    """
    _log('Scraping {0} - {1}'.format(location['name'], location['url']), logging.INFO)
    menu_html = urllib2.urlopen(location['url']).read()
    if menu_html:
        _log('Read {0} bytes'.format(len(menu_html)), logging.INFO)
        scrape_time = datetime.now()
        menu_json = parse_menu.parse_menu(menu_html, location['name'], scrape_time)
        cache_menu(menu_json, location, scrape_time)
    else:
        _log('Unable to retrieve menu from {0}'.format(location['url']), logging.ERROR)


def cache_menu(menu, location, time):
    """
    Cache the parsed menu JSON on the filesystem organized by date.

    :param menu: Parsed menu JSON.
    :type menu: str
    :param location: Stout location menu is for.
    :type location: dict
    :param time: When menu was downloaded.
    :type time: datetime
    :return: Path to the cached file.
    :rtype: str
    """
    # Organize cache into directories by location/year/month
    directory = os.path.join('menu_cache', time.strftime('%Y'), time.strftime('%m'))
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Name files menu_YYYY-MM-DD_location.json
    location_path = location['name'].replace(' ', '_').lower()
    filename = 'menu_{0}_{1}.json'.format(time.strftime('%Y-%m-%d'), location_path)
    file_path = os.path.join(directory, filename)
    with open(file_path, 'w') as fh:
        fh.write(json.dumps(menu))
    return file_path


def _log(message, level=logging.INFO):
    root_log.log(level, message)


if __name__ == '__main__':
    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    for loc in locations:
        scrape_location(loc)
