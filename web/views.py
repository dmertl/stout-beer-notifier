from web import app
from scraper.scrape import get_cache, get_cache_near, get_cache_extreme
from flask import render_template, request
from datetime import datetime, timedelta
from scraper.menu_diff import diff


@app.route('/')
def home():
    return 'Home page'


@app.route('/menu/')
def menu_index():
    # TODO: List all menus, click to view
    return 'Menu index'


@app.route('/menu/<menu_name>/')
def menu_view(menu_name):
    menu = get_cache(name=menu_name)
    return render_template('table_view.html', menu=menu)


@app.route('/menu/diff/')
def menu_diff():
    # TODO: Display note if exact cache wasn't available
    # TODO: JS datepicker widget
    # Grab parameters
    location = request.args.get('location')
    start = request.args.get('start')
    end = request.args.get('end')
    # Compute menu diff
    _diff = None
    if location and start:
        start_date = datetime.strptime(start, '%Y-%m-%d')
        start_menu = get_cache_near(location, start_date, True)
        if end:
            end_date = datetime.strptime(end, '%Y-%m-%d')
            end_menu = get_cache_near(location, end_date, False)
        else:
            end_menu = get_cache_extreme(location, 'new')
        _diff = diff(start_menu, end_menu)
    # Form defaults
    if not start:
        start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    if not end:
        end = datetime.now().strftime('%Y-%m-%d')
    return render_template('diff.html', diff=_diff, location=location, start=start, end=end)
