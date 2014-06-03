import argparse
import sys
import os
import json
import logging
import urllib2
from lxml.html import fromstring
from unidecode import unidecode

root_log = logging.getLogger()
root_log.setLevel(logging.WARN)


class Exception(Exception):
    pass


class ParsingException(Exception):
    pass


def parse_menu(html):
    """

    :param html: Stout menu web page HTML
    :type html: str
    :return:
    :rtype: dict
    """
    parsed_sections = []

    tree = fromstring(html)

    # Find menu element
    beer_menu = tree.xpath('//div[@id="second-menu"]')
    if beer_menu:
        beer_menu = beer_menu[0]

        # Find all headers and sections in the menu
        menu_headers = beer_menu.xpath('.//header')
        menu_sections = beer_menu.xpath('.//section')

        _log('Found {0} headers and {1} sections in menu.'.format(len(menu_headers), len(menu_sections)), logging.INFO)

        if len(menu_headers) != len(menu_sections):
            _log('Number of headers {0} does not match number of sections {1}'
                 .format(len(menu_headers), len(menu_sections)), logging.WARN)

        section_count = 0
        # Header does not contain section, but they should match up sequentially
        for header_element, section_element in zip(menu_headers, menu_sections):
            section_count += 1
            section = _parse_section(header_element, section_element, section_count)
            try:
                parsed_sections.append(section)
            except ParsingException as e:
                _log(e.message, logging.WARN)
    else:
        _log('Unable to find "div#second-menu" when parsing menu.', logging.ERROR)
        raise ParsingException('Unable to find "div#second-menu" when parsing menu.')

    return parsed_sections


def _parse_section(header_element, section_element, section_count):
    """
    Parse a menu header and section element into a section dict.

    :param header_element:
    :type header_element: etree.Element
    :param section_element:
    :type section_element: etree.Element
    :param section_count:
    :type section_count: int
    :return:
    :rtype: dict
    """
    # H2 inside the header has the section name
    name = header_element.xpath('.//h2')
    if name:
        name = name[0].text_content().strip()
        _log('Parsing section {0} "{1}".'.format(section_count, name))
        section_obj = {
            'name': name,
            'beverages': []
        }

        # Find all article elements inside the section
        beverage_elements = section_element.xpath('.//article')
        _log('Found {0} beverages.'.format(len(beverage_elements)))
        beverage_count = 0
        for beverage_element in beverage_elements:
            beverage_count += 1
            try:
                beverage = _parse_beverage(beverage_element, beverage_count, section_count)
                _log('Parsed beverage {0} "{1}".'.format(beverage_count, beverage['name']))
                section_obj['beverages'].append(beverage)
            except ParsingException as e:
                _log(e.message, logging.WARN)
        return section_obj
    else:
        raise ParsingException('Unable to find "h2" in header {0}'.format(section_count))


def _parse_beverage(beverage_element, beverage_count, section_count):
    """
    Parse a beverage element into an item.

    :param beverage_element:
    :type beverage_element: etree.Element
    :param beverage_count:
    :type beverage_count: int
    :param section_count:
    :type section_count: int
    :return:
    :rtype: dict
    """
    # .title element contains the beverage name
    name = beverage_element.xpath('.//p[@class="title"]')
    if name:
        name = name[0].text_content().strip()
        if type(name) is unicode:
            # Convert any fancy unicode characters to more common ascii equivalents
            name = unidecode(name)
        return {
            'name': name
        }
    else:
        raise ParsingException('Unable to find "p.title" in section {0} item {1}.'.format(section_count, beverage_count))


def _log(message, level=logging.INFO):
    root_log.log(level, message)


if __name__ == '__main__':
    # Setup logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_log.addHandler(sh)

    # Command line arguments
    parser = argparse.ArgumentParser(description='Parse http://www.stoutburgersandbeers.com/ beer menu into JSON.')
    parser.add_argument('filename', type=str, help='file path or URL to beverage menu')
    parser.add_argument('--pretty', action='store_true', help='pretty print JSON output')
    args = parser.parse_args()

    # Parse menu file
    filename = args.filename
    if os.path.exists(filename):
        contents = urllib2.urlopen('file:{0}'.format(urllib2.quote(os.path.abspath(filename)))).read()
    else:
        contents = urllib2.urlopen(filename).read()

    if contents:
        # Parse menu
        sections = parse_menu(contents)

        # Output parsed menu as JSON
        if args.pretty:
            print json.dumps(sections, indent=2)
        else:
            print json.dumps(sections)
    else:
        print 'Unable to read menu from "{0}".'.format(filename)
