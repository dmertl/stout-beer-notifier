stout-beer-notifier
===================

Get a notification when stout updates their beer list.

TODO
====

- Sanity check beer piece parsing, check size/price/alcohol percentage are numbers
- Parse location from menu (maybe not necessary)
- View
- Table view for debugging that is easy to scan columns of data
- Set up on web server with cron for automation
- Notifications
- Unit tests
- Configurable logging

Future Features
---------------

- Check for modified beverages in addition to added and removed. Same name, but different alcohol % or brewery, etc.
- Some kind of user login to view differences since you last visited the site.

Known Issues
------------

- Need a better way of identifying location vs. brewery vs. style. Currently have to use position which is not always consistent.
- Some beers have location swapped with brewery "St Louis Framboise – Belgium / Lambic-Fruit / 375ml / 4.5% / $15"

System
======

Menu Parsing
-------------
parse_menu.py takes stoutburgersandbeers.com menu and parses it into JSON.

Menu Diff
---------
menu_diff.py takes two JSON menu generated by parse_menu.py and computes the difference.

Automation
----------

- Run parse_menu.py daily for each location.
- Save file with day timestamp.

Viewing Diff
------------

- Prompt for a location, start day and end day.
- Retrieve cached menu files for location on start and end day (or nearest available).
- Calculate diff of menu files.
- Display diff.

Notifications
-------------

TBD

Specify frequency, daily/weekly, etc.
Specify location
Specify categories of interest beer, on tap, wine, etc.

Testing
=======

Sample Testing
--------------

_View menu parsing_
python parse_menu.py sample/old.html --pretty
python parse_menu.py sample/new.html --pretty

_View menu diff_
python menu_diff.py sample/old.json sample/new.json --pretty

_Test menu parsing (diff should be empty)_
diff <(python parse_menu.py sample/old.html --pretty) sample/old.json

Unit Tests
----------

Someday
