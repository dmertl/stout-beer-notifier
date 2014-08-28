from web import app
from scraper.scrape import get_cache
from flask import render_template

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
    # TODO: display a form and display diff between two menus
    return 'Menu diff'
