import sys
from lxml.html import fromstring
from unidecode import unidecode
import logging

root_log = logging.getLogger()
root_log.addHandler(logging.StreamHandler(sys.stdout))


def parse_menu(html):
    parsed_sections = []

    tree = fromstring(html)

    beer_menu = tree.xpath('//div[@id="second-menu"]')
    if beer_menu:
        beer_menu = beer_menu[0]

        menu_headers = beer_menu.xpath('.//header')
        menu_sections = beer_menu.xpath('.//section')

        log('Found {0} headers and {1} sections in menu.'.format(len(menu_headers), len(menu_sections)), logging.INFO)

        if len(menu_headers) != len(menu_sections):
            log('Number of headers {0} does not match number of sections {1}'
                .format(len(menu_headers), len(menu_sections)), logging.WARN)

        section_count = 0
        for header, section in zip(menu_headers, menu_sections):
            section_count += 1
            header_title = header.xpath('.//h2')
            if header_title:
                header_title = header_title[0].text_content().strip()
                log('Parsing section {0} "{1}".'.format(section_count, header_title))
                section_obj = {
                    'name': header_title,
                    'items': []
                }

                section_items = section.xpath('.//article')
                log('Found {0} item in section.'.format(len(section_items)))
                item_count = 0
                for item in section_items:
                    item_name = item.xpath('.//p[@class="title"]')
                    item_count += 1
                    if item_name:
                        item_name = item_name[0].text_content().strip()
                        if type(item_name) is unicode:
                            # Convert any fancy unicode characters to more common ascii equivalents
                            item_name = unidecode(item_name)
                        log('Found item {0} "{1}".'.format(item_count, item_name))
                        section_obj['items'].append({
                            'name': item_name
                        })
                    else:
                        log('Unable to find "p.title" in section {0} item {1}.'.format(section_count, item_count))
                parsed_sections.append(section_obj)
            else:
                log('Unable to find "h2" in header {0}'.format(section_count))
    else:
        log('Unable to find "div#second-menu" when parsing menu.', logging.ERROR)

    return parsed_sections


def log(message, level=logging.INFO):
    print message
    #root_log.log(level, message)


filename = sys.argv[1]
fh = open(filename, 'r')
contents = fh.read()

sections = parse_menu(contents)
print sections

# tree = fromstring(contents)
# # tree = etree.HTML(filename)
# # tree = etree.parse(filename, parser=etree.HTMLParser())
# # tree = etree.parse(filename, parser=html5parser)
#
# beer_menu = tree.xpath('//div[@id="second-menu"]')[0]
#
# menu_headers = beer_menu.xpath('.//header')
# menu_sections = beer_menu.xpath('.//section')
#
# # headers should equal sections
# for header, section in zip(menu_headers, menu_sections):
#     header_title = header.xpath('.//h2')[0].text_content().strip()
#     print "**{0}**".format(header_title)
#     section_items = section.xpath('.//article')
#     for item in section_items:
#         item_name = item.xpath('.//p[@class="title"]')[0].text_content().strip()
#         # Convert any fancy unicode characters to more common ascii equivalents
#         item_name = unidecode(item_name)
#         print "\t{0}".format(item_name)

"""
#second-menu .menu-item

First <section> is beer
Second <section> is red wine
Third <section> is specialty bottled beer
...

Can get section names from #second-menu .menu-header h2 and strip all inner tags (span, i, etc)
"""


