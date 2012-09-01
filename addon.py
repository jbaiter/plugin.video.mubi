#!/usr/bin/env python

from xbmcswift import Plugin
from resources.lib.mubi import Mubi

PLUGIN_NAME = 'MUBI'
PLUGIN_ID = 'plugin.video.mubi'

plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)

if not plugin.get_setting("username"):
    plugin.open_settings()

mubi_session = Mubi()
mubi_session.login(plugin.get_setting("username"),
                   plugin.get_setting("password"))

@plugin.route('/')
def index():
    items = [ {'label': 'Films', 'is_folder': True,
               'url': plugin.url_for('select_filter')},
             {'label': 'Cinemas', 'is_folder': True,
               'url': plugin.url_for('show_cinemas')},
              {'label': 'Watchlist', 'is_folder': True,
               'url': plugin.url_for('show_films', filter='watchlist', argument='0', page='1')},
              {'label': 'Search', 'is_folder': True,
               'url': plugin.url_for('show_search_targets')}]
    return plugin.add_items(items)

@plugin.route('/films')
def select_filter():
    options = [ {'label': 'All Films', 'is_folder': True,
                 'url': plugin.url_for('show_films', filter='all', argument='0', page='1')},
                {'label': 'By Genre', 'is_folder': True,
                 'url': plugin.url_for('show_genres')},
                {'label': 'By Country', 'is_folder': True,
                 'url': plugin.url_for('show_countries')},
                {'label': 'By Language', 'is_folder': True,
                 'url': plugin.url_for('show_languages')} ]
    return plugin.add_items(options)

@plugin.route('/cinemas')
def show_cinemas():
    cinemas = mubi_session.get_all_programs()
    items = [{'label': x[0], 'is_folder': True, 'thumbnail': x[2],
              'url': plugin.url_for('show_cinema_films', cinema=x[1])}
              for x in cinemas]
    return plugin.add_items(items)

@plugin.route('/cinemas/<cinema>')
def show_cinema_films(cinema):
    films = mubi_session.get_program_films(cinema)
    items = [{'label': x[0], 'is_folder': False, 'is_playable': True,
              'thumbnail': x[2],
              'url': plugin.url_for('play_film', identifier=x[1])}
              for x in films]
    return plugin.add_items(items)

@plugin.route('/search')
def show_search_targets():
    targets = [{'label': 'Film', 'is_folder': True,
                'url': plugin.url_for('show_search', target='film')},
               {'label': 'Person', 'is_folder': True,
                'url': plugin.url_for('show_search', target='person')}]
    return plugin.add_items(targets)

@plugin.route('/search/<target>')
def show_search(target=None):
    #TODO: Display onscreen keyboard and call show_search_results
    raise NotImplementedError

@plugin.route('/search/<target>/<term>')
def show_search_results(target, term):
    #TODO: Display query results
    raise NotImplementedError

@plugin.route('/films/<filter>/<argument>/<page>')
def show_films(filter, argument, page):
    page = int(page)
    if filter == 'all':
        num_pages, films = mubi_session.get_all_films(page=page)
    elif filter == 'watchlist':
        films = mubi_session.get_watchlist()
        num_pages = 1
    elif filter == 'genre':
        num_pages, films = mubi_session.get_all_films(genre=argument,page=page)
    elif filter == 'country':
        num_pages, films = mubi_session.get_all_films(country=argument,page=page)
    elif filter == 'language':
        num_pages, films = mubi_session.get_all_films(language=argument,page=page)
    #TODO: Display error message when there are no films
    items = [{'label': x[0], 'is_folder': False, 'is_playable': True,
              'url': plugin.url_for('play_film', identifier=x[1]),
              'thumbnail': x[2]}
              for x in films]
    if page > 1:
        items.append({'label': 'Previous...', 'is_folder': True,
                      'url': plugin.url_for('show_films', filter=filter,
                                             argument=argument, page=unicode(page-1))})
    if (num_pages - page) > 0:
        items.append({'label': 'Next...', 'is_folder': True,
                    'url': plugin.url_for('show_films', filter=filter,
                                            argument=argument, page=unicode(page+1))})
    return plugin.add_items(items)

@plugin.route('/play/<identifier>')
def play_film(identifier):
    return plugin.set_resolved_url(mubi_session.get_play_url(identifier))
    #return plugin.add_items([{'label': 'Play', 'is_playable': True, 'is_folder': False,
                              #'url': mubi_session.get_play_url(identifier)}])

@plugin.route('/list/genres')
def show_genres():
    items = [{'label': x, 'is_folder': True,
              'url': plugin.url_for('show_films', filter='genre',
                                     argument=unicode(mubi_session._CATEGORIES[x]),
                                     page='1')}
              for x in sorted(mubi_session._CATEGORIES)]
    return plugin.add_items(items)

@plugin.route('/list/countries')
def show_countries():
    items = [{'label': x, 'is_folder': True,
              'url': plugin.url_for('show_films', filter='country',
                                     argument=unicode(mubi_session._COUNTRIES[x]),
                                     page='1')}
              for x in sorted(mubi_session._COUNTRIES)]
    return plugin.add_items(items)

@plugin.route('/list/languages')
def show_languages():
    items = [{'label': x, 'is_folder': True,
              'url': plugin.url_for('show_films', filter='language',
                                     argument=unicode(mubi_session._LANGUAGES[x]),
                                     page='1')}
              for x in sorted(mubi_session._LANGUAGES)]
    return plugin.add_items(items)


if __name__ == '__main__':
    plugin.run()
