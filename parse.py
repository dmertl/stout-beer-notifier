import sys
from lxml import etree
from lxml.html import fromstring
from unidecode import unidecode

filename = sys.argv[1]
fh = open(filename, 'r')
contents = fh.read()
tree = fromstring(contents)
# tree = etree.HTML(filename)
# tree = etree.parse(filename, parser=etree.HTMLParser())
# tree = etree.parse(filename, parser=html5parser)

beer_menu = tree.xpath('//div[@id="second-menu"]')[0]

menu_headers = beer_menu.xpath('.//header')
menu_sections = beer_menu.xpath('.//section')

# headers should equal sections
for header, section in zip(menu_headers, menu_sections):
    header_title = header.xpath('.//h2')[0].text_content().strip()
    print "**{0}**".format(header_title)
    section_items = section.xpath('.//article')
    for item in section_items:
        item_name = item.xpath('.//p[@class="title"]')[0].text_content().strip()
        # Convert any fancy unicode characters to more common ascii equivalents
        item_name = unidecode(item_name)
        print "\t{0}".format(item_name)

"""
#second-menu .menu-item

First <section> is beer
Second <section> is red wine
Third <section> is specialty bottled beer
...

Can get section names from #second-menu .menu-header h2 and strip all inner tags (span, i, etc)
"""
