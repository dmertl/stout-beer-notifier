import argparse
import os
import json
import logging
import re
import urllib2
from datetime import datetime

from lxml.html import fromstring
from unidecode import unidecode

import sys

root_log = logging.getLogger()
root_log.setLevel(logging.WARN)


class ParsingException(Exception):
    pass


class PieceParsingException(Exception):
    pass


class BeverageParser:
    pass


class BeverageParsingStrategy:
    pass


class WineParsingStrategy(BeverageParsingStrategy):
    """
        Campagnola / Pinot Grigio / 2010 / Veneto
          <winery> / <style> / <year> / <loc>
        Don Rodolfo -Malbec / 2010 / Mendoza
          <winery> -<style> / <year> / <loc>
    """

    regex = re.compile('^(.+)[/-](.+)/(.+)/(.+)$')

    def parse(self, name):
        match = self.regex.match(name)
        if match:
            return self.get_details(match)
        else:
            raise ParsingException('Unable to parse details out of wine name "{0}".'.format(name))

    def get_details(self, match):
        details = {
            'winery': match.group(1).strip(),
            'style': match.group(2).strip(),
            'year': match.group(3).strip(),
            'location': match.group(4).strip(),
            'type': 'wine'
        }
        details['name'] = '{0} {1} {2}'.format(details['winery'], details['style'], details['year'])
        return details


class WineParser(BeverageParser):
    def parse(self, name):
        return WineParsingStrategy().parse(name)


class BeveragePieceStrategy:
    pass


class AlcoholPercentagePieceStrategy(BeveragePieceStrategy):
    def parse(self, name):
        if name.endswith('%'):
            return {'alcohol_percentage': name}
        else:
            raise PieceParsingException


class PricePieceStrategy(BeveragePieceStrategy):
    def parse(self, name):
        if name[0] == '$':
            return {'price': name}
        else:
            raise PieceParsingException


class SizePieceStrategy(BeveragePieceStrategy):
    def parse(self, name):
        if name.endswith(('oz', 'ml')):
            return {'size': name}
        else:
            raise PieceParsingException


class NitroPieceStrategy(BeveragePieceStrategy):
    def parse(self, piece):
        if piece == 'Nitro':
            return {'nitro': True}
        else:
            raise PieceParsingException


class BeerParser(BeverageParser):
    """
    Parse beer title into detailed information.

    Split beer on "/" into pieces. Identify data in pieces by formatting or position.
        Old Speckled Hen - Green King / UK / Cream Ale / Nitro / 5.2%
          <name> - <brewery> / <loc> / <style> / <nitro> / <alc>%
        RazzMaTazz - Julian / CA / Rasp Cider / 22oz / 6.9% / $12
          <name> - <brewery> / <loc> / <style> / <size>oz / <alc>% / $<cost>
        Saison Dupont Cuvee Dry Hop - Dupont / Belg / Saison / 6.5% / $10
          <name> - <brewery> / <geo> / <style> / <alc>% / $<cost>
        Avec Les Bons Voeux 2012 - Dupont / Belg / Xmas Saison / 9.5%
          <name> <year> - <brewery> / <loc> / <style> / <%>
        Weihenstephaner Original - Germ / Helles Lager / 5.1%
          <name> - <loc> / <style> / <alc>%
    """
    strategies = [
        AlcoholPercentagePieceStrategy(),
        PricePieceStrategy(),
        SizePieceStrategy(),
        NitroPieceStrategy()
    ]

    def parse(self, name):
        clean_name = self._clean_name(name)
        pieces = [i.strip() for i in clean_name.split('/')]
        total_count = len(pieces)
        if 3 <= len(pieces) <= 6:
            details = {'type': 'beer'}
            # First piece is always the name
            details = dict(details.items() + self._parse_name(pieces[0]).items())
            del pieces[0]

            # Match easily identifiable pieces
            unidentified = []
            for piece in pieces:
                if len(piece):
                    parsed = False
                    for strategy in self.strategies:
                        try:
                            details = dict(details.items() + strategy.parse(piece).items())
                            parsed = True
                            break
                        except PieceParsingException:
                            pass
                    if not parsed:
                        unidentified.append(piece)

            # Make assumptions on remaining pieces by position
            try:
                details = dict(details.items() + self._parse_positional(unidentified, total_count).items())
            except ParsingException as e:
                _log('{0} from name {1}'.format(e.message, name), logging.WARN)

            try:
                details = dict(details.items() + self._parse_year(details['name']).items())
            except PieceParsingException:
                pass

            return details
        else:
            raise ParsingException('Unable to parse beer name: {0}'.format(name))

    def _clean_name(self, name):
        """
        Clean various shit out of name that screws with the parsing.
        """
        return name.replace('w/', 'with ').replace('IPAw / ', 'IPA with ')

    def _parse_name(self, piece):
        regex = re.compile('^([^-]+)-(.+)$')
        match = regex.match(piece)
        if match:
            return {'name': match.group(1).strip(), 'brewery': match.group(2).strip()}
        else:
            return {'name': piece}

    def _parse_year(self, name):
        year_re = re.compile('([0-9]{4})')
        year_match = year_re.search(name)
        if year_match:
            year = int(year_match.group(1))
            if year and year > 1990 and year < 2020:
                return {'year': year}
        raise PieceParsingException

    def _parse_positional(self, pieces, total_count):
        """
        Parse the remaining unidentified pieces by position.
        """
        details = {}
        if 1 <= len(pieces) <= 2:
            # Special case for 3 piece title, style will be only remaining piece
            if total_count == 3:
                details['style'] = pieces[0]
            else:
                details['location'] = pieces[0]
                try:
                    details['style'] = pieces[1]
                except IndexError:
                    pass
            return details
        else:
            raise ParsingException('Unable to identify remaining beer name pieces: {0}'.format(str(pieces)))


def parse_menu(html, location, date):
    # TODO: parse location from menu
    return {
        'location': location,
        'parsed': str(date),
        'sections': parse_sections(html)
    }


def parse_sections(html):
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
        section = {
            'name': name,
            'type': 'wine' if 'Wine' in name else 'beer',
            'beverages': []
        }

        # Find all article elements inside the section
        beverage_elements = section_element.xpath('.//article')
        _log('Found {0} beverages.'.format(len(beverage_elements)))
        beverage_count = 0
        for beverage_element in beverage_elements:
            beverage_count += 1
            try:
                beverage = _parse_beverage(beverage_element, section['type'] == 'wine', beverage_count, section_count)
                _log('Parsed beverage {0} "{1}".'.format(beverage_count, beverage['name']))
                section['beverages'].append(beverage)
            except ParsingException as e:
                _log(e.message, logging.DEBUG)
        return section
    else:
        raise ParsingException('Unable to find "h2" in header {0}'.format(section_count))


def _parse_beverage(beverage_element, is_wine, beverage_count, section_count):
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
        if name:
            if type(name) is unicode:
                # Convert any fancy unicode characters to more common ascii equivalents
                name = unidecode(name)
            beverage = {
                'name': name
            }
            try:
                beverage['details'] = _parse_beverage_details(name, is_wine)
            except ParsingException as e:
                _log(e.message, logging.DEBUG)
            return beverage
        else:
            raise ParsingException('Empty beverage in section {0} item {1}'.format(section_count, beverage_count))
    else:
        raise ParsingException(
            'Unable to find "p.title" in section {0} item {1}.'.format(section_count, beverage_count))


def _parse_beverage_details(name, is_wine):
    if is_wine:
        parser = WineParser()
        return parser.parse(name)
    else:
        parser = BeerParser()
        return parser.parse(name)


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
        menu = parse_menu(contents, 'Studio City', datetime.now())

        # Output parsed menu as JSON
        if args.pretty:
            print json.dumps(menu, indent=2)
        else:
            print json.dumps(menu)
    else:
        print 'Unable to read menu from "{0}".'.format(filename)
