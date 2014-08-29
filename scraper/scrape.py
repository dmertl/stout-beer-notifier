import os
import json
import logging
import urllib2
from datetime import datetime, timedelta
import sys
import re

from scraper import parse_menu


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
# Root cache directory
cache_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'menu_cache')


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
    # Name files menu_YYYY-MM-DD_location.json
    file_path = _build_cache_path(location['name'], time=time)
    # Organize cache into directories by location/year/month
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Write file
    with open(file_path, 'w') as fh:
        fh.write(json.dumps(menu))
    return file_path


def get_cache_near(location, time, lean_newer=True):
    # TODO: use huersitic to bound on oldest and newest cache files
    cache_path = _build_cache_path(location, time=time)
    i = 0
    while not os.path.exists(cache_path):
        i += 1
        if lean_newer:
            time = time + timedelta(days=1)
        else:
            time = time - timedelta(days=1)
        cache_path = _build_cache_path(location, time=time)
        if i > 100:
            raise Exception('Unable to find cache file near request date')
    return json.load(open(cache_path))


def get_cache(name=None, location=None, time=None, year=None, month=None, day=None):
    if name:
        regex = re.compile('.*([0-9]{4})-([0-9]{2})-([0-9]{2})_(.*)')
        matches = regex.match(name)
        cache_path = _build_cache_path(matches.group(4), year=matches.group(1), month=matches.group(2),
                                       day=matches.group(3))
    else:
        if time:
            cache_path = _build_cache_path(location=location, time=time)
        else:
            cache_path = _build_cache_path(location=location, year=year, month=month, day=day)

    return json.load(open(cache_path))


def _build_cache_path(location, year=None, month=None, day=None, time=None):
    location = location.replace(' ', '_').lower()
    if time:
        _dir = os.path.join(time.strftime('%Y'), time.strftime('%m'))
        filename = 'menu_{0}_{1}.json'.format(time.strftime('%Y-%m-%d'), location)
    else:
        _dir = os.path.join(year, month)
        filename = 'menu_{0}-{1}-{2}_{3}.json'.format(year, month, day, location)
    return os.path.join(cache_root, _dir, filename)


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
