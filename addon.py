#!/usr/bin/env python

from xbmcswift import xbmc, xbmcgui, Plugin
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
    items = [{'label': plugin.get_string(31001), 'is_folder': True,
              'url': plugin.url_for('select_filter')},
             {'label': plugin.get_string(31002), 'is_folder': True,
              'url': plugin.url_for('show_cinemas')},
             {'label': plugin.get_string(31003), 'is_folder': True,
              'url': plugin.url_for('show_films', filter='watchlist',
                                    argument='0', page='1')},
             {'label': plugin.get_string(31004), 'is_folder': True,
              'url': plugin.url_for('show_search_targets')}]
    return plugin.add_items(items)


@plugin.route('/films')
def select_filter():
    options = [{'label': plugin.get_string(31005), 'is_folder': True,
                'url': plugin.url_for('show_films', filter='all',
                                      argument='0', page='1')},
               {'label': plugin.get_string(31006), 'is_folder': True,
                'url': plugin.url_for('show_genres')},
               {'label': plugin.get_string(31007), 'is_folder': True,
                'url': plugin.url_for('show_countries')},
               {'label': plugin.get_string(31008), 'is_folder': True,
                'url': plugin.url_for('show_languages')}]
    return plugin.add_items(options)


@plugin.route('/cinemas')
def show_cinemas():
    cinemas = mubi_session.get_all_programs()
    items = [{'label': x.title, 'is_folder': True, 'thumbnail': x.picture,
              'url': plugin.url_for('show_cinema_films', cinema=x.identifier)}
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
    targets = [{'label': plugin.get_string(31009), 'is_folder': True,
                'url': plugin.url_for('show_search', target='film')},
               {'label': plugin.get_string(31010), 'is_folder': True,
                'url': plugin.url_for('show_search', target='person')}]
    return plugin.add_items(targets)


@plugin.route('/search/<target>')
def show_search(target=None):
    if target == 'film':
        label = plugin.get_string(31013)
    else:
        label = plugin.get_string(31014)
    keyboard = xbmc.Keyboard('', label)
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText()
        url = plugin.url_for('show_search_results', target=target,
                             term=search_string)
        plugin.redirect(url)


@plugin.route('/search/<target>/<term>')
def show_search_results(target, term):
    if target == 'film':
        results = mubi_session.search_film(term)
        items = [{'label': x[0], 'is_folder': False, 'is_playable': True,
                  'url': plugin.url_for('play_film', identifier=unicode(x[1])),
                  'thumbnail': x[2]} for x in results]
        return plugin.add_items(items)
    elif target == 'person':
        results = mubi_session.search_person(term)
        items = [{'label': x[0], 'is_folder': True,
                  'url': plugin.url_for('show_person_films',
                                        person=unicode(x[1])),
                  'thumbnail': x[2]}
                  for x in results]
        return plugin.add_items(items)


@plugin.route('/persons/<person>')
def show_person_films(person):
    films = mubi_session.get_person_films(person)
    items = [{'label': x[0], 'is_folder': False, 'is_playable': True,
              'url': plugin.url_for('play_film', identifier=x[1]),
              'thumbnail': x[2]} for x in films]
    return plugin.add_items(items)


@plugin.route('/films/<filter>/<argument>/<page>')
def show_films(filter, argument, page):
    page = int(page)
    if filter == 'all':
        num_pages, films = mubi_session.get_all_films(page=page)
    elif filter == 'watchlist':
        films = mubi_session.get_watchlist()
        num_pages = 1
    elif filter == 'genre':
        num_pages, films = mubi_session.get_all_films(genre=argument,
                                                      page=page)
    elif filter == 'country':
        num_pages, films = mubi_session.get_all_films(country=argument,
                                                      page=page)
    elif filter == 'language':
        num_pages, films = mubi_session.get_all_films(language=argument,
                                                      page=page)
    items = [{'label': x[0], 'is_folder': False, 'is_playable': True,
              'url': plugin.url_for('play_film', identifier=x[1]),
              'thumbnail': x[2]}
              for x in films]
    if len(items) == 0:
        xbmcgui.Dialog().ok(plugin.get_string(30000), plugin.get_string(31015))
        plugin.redirect(plugin.url_for('select_filter'))
    if page > 1:
        items.append({'label': plugin.get_string(31011), 'is_folder': True,
                      'url': plugin.url_for('show_films', filter=filter,
                                            argument=argument,
                                            page=unicode(page - 1))})
    if (num_pages - page) > 0:
        items.append({'label': plugin.get_string(31012), 'is_folder': True,
                      'url': plugin.url_for('show_films', filter=filter,
                                            argument=argument,
                                            page=unicode(page + 1))})
    return plugin.add_items(items)


@plugin.route('/play/<identifier>')
def play_film(identifier):
    return plugin.set_resolved_url(mubi_session.get_play_url(identifier))


@plugin.route('/list/genres')
def show_genres():
    items = [{'label': x, 'is_folder': True,
              'url': plugin.url_for('show_films', filter='genre',
                                     argument=unicode(mubi_session.genres[x]),
                                     page='1')}
              for x in sorted(mubi_session._CATEGORIES)]
    return plugin.add_items(items)


@plugin.route('/list/countries')
def show_countries():
    items = [{'label': x, 'is_folder': True,
              'url': plugin.url_for('show_films', filter='country',
                                     argument=unicode(mubi_session
                                                      .countries[x]),
                                     page='1')}
              for x in sorted(mubi_session.countries)]
    return plugin.add_items(items)


@plugin.route('/list/languages')
def show_languages():
    items = [{'label': x, 'is_folder': True,
              'url': plugin.url_for('show_films', filter='language',
                                     argument=unicode(mubi_session
                                                      .languages[x]),
                                     page='1')}
              for x in sorted(mubi_session._LANGUAGES)]
    return plugin.add_items(items)


if __name__ == '__main__':
    plugin.run()
