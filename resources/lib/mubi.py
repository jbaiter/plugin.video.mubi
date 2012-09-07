# -*- coding: utf-8 -*-

# Copyright (c) 2012, Johannes Baiter (jbaiter)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import json
import logging
import re
from collections import namedtuple
from math import ceil
from urllib import urlencode
from urlparse import urljoin

import requests
from BeautifulSoup import BeautifulSoup as BS

Film = namedtuple('Film', ['title', 'mubi_id', 'filmstill'])
Person = namedtuple('Person', ['name', 'mubi_id', 'portrait'])
Program = namedtuple('Program', ['title', 'identifier', 'picture'])
VideoMetadata = namedtuple('VideoMetadata',
                           ['year', 'rating', 'cast', 'director', 'plot',
                            'title', 'originaltitle', 'duration', 'writer',
                            'playcount', 'trailer', 'audio_language',
                            'subtitle_language', 'plotoutline'])


class Mubi(object):
    _URL_MUBI = "http://mubi.com"
    _URL_MUBI_SECURE = "https://mubi.com"
    _regexps = {"item":        re.compile("item.*"),
                "watch_link":  re.compile("watch_link.*"),
                "duration":    re.compile("\d+ Min"),
                "program":     re.compile("use6.*"),
                "rating":      re.compile(r"Currently ([1-5]\.\d)/5 Stars."),
                "audio_lang":  re.compile(r"Audio in (.*)"),
                "sub_lang":    re.compile(r"Subtitled in (.*)"),
                "watch_page":  re.compile(r"^.*/watch$")}
    _mubi_urls = {
                  "login":      urljoin(_URL_MUBI_SECURE, "login"),
                  "session":    urljoin(_URL_MUBI_SECURE, "session"),
                  "search":     urljoin(_URL_MUBI,
                                        "services/films/search.json?term=%s"),
                  "programs":   urljoin(_URL_MUBI, "cinemas"),
                  "single_program": urljoin(_URL_MUBI, "programs"),
                  "video":      urljoin(_URL_MUBI, "films/%s/secure_url"),
                  "prescreen":  urljoin(_URL_MUBI, "films/%s/prescreen"),
                  "list":       urljoin(_URL_MUBI, "watch"),
                  "person":     urljoin(_URL_MUBI, "cast_members/%s"),
                  "logout":     urljoin(_URL_MUBI, "logout"),
                  "filmstill":  "http://s3.amazonaws.com/auteurs_production/images/film/%s/w448/%s.jpg",
                  "shortdetails": urljoin(_URL_MUBI,
                                          "/services/films/tooltip?id=%s&country_code=US&locale=en_US"),
                  "fulldetails": urljoin(_URL_MUBI, "films/%s"),
                  "watchlist":  urljoin(_URL_MUBI, "/users/%s/watchlist.json"),
                  "portrait":   "http://s3.amazonaws.com/auteurs_production/images/cast_member/%s/original.jpg"
                 }

    _SORT_KEYS = ['popularity', 'recently_added', 'rating', 'year', 'running_time']
    _USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_5_8) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.151 Safari/535.19"

    def __init__(self):
        self._logger = logging.getLogger('mubi.Mubi')
        self._session = requests.session()
        self._session.headers = {'User-Agent': self._USER_AGENT}
        list_page = BS(self._session.get(self._mubi_urls["list"]).content)
        self.genres = self._parse_genres(list_page)
        self.languages = self._parse_languages(list_page)
        self.countries = self._parse_countries(list_page)

    def __del__(self):
        self._session.get(self._mubi_urls["logout"])

    def _parse_watchable_titles(self, page):
        items = [x for x in BS(page).findAll("div",
                                             {"class": self._regexps["item"]})
                 if (x.findChild("h2")
                 and x.findChild("div",
                                 {"class": self._regexps["watch_link"]}))]
        return [Film(title=x.find("h2").text,
                     mubi_id=x.get("data-item-id"),
                     filmstill=(x.find("div", "cropped_image")
                                .find("img").get("src")
                                .replace("w192", "w448")))
                for x in items]

    def _search(self, term):
        return json.loads(self._session.get(self._mubi_urls["search"] % term)
                          .content)

    def _get_shortdetails(self, mubi_id):
        # Available keys: cast, directors, duration [minutes], excerpt,
        #                 id, primary_country, title, year
        info = json.loads(self._session.get(self._mubi_urls["shortdetails"]
                                            % unicode(mubi_id)
                         ).content)
        return (Film(info['title'], info['id'],
                     self._get_filmstill(self._resolve_id(info['id']))),
                VideoMetadata(year=info['year'], rating=None,
                              cast=info['cast'].split(", "),
                              director=", ".join(info['directors'].values()),
                              plot=None, title=info['title'],
                              originaltitle=None, duration=info['duration'],
                              writer=None, playcount=None, trailer=None,
                              audio_language=None, subtitle_language=None,
                              plotoutline=info['excerpt'])
               )

    def _get_filmstill(self, name):
        return self._mubi_urls["filmstill"] % (name, name)

    def _get_person_image(self, person_id):
        url = self._mubi_urls["portrait"] % unicode(person_id)
        if not self._session.head(url):
            url = url.replace("jpg", "jpeg")
        return url

    def _resolve_id(self, mubi_id):
        return self._session.head(self._mubi_urls["fulldetails"] % mubi_id
                ).headers['location'].split("/")[-1]

    def _parse_genres(self, list_page):
        options = (list_page.find("select", {"id": "category_id"})
                   .findAll("option"))
        return {x.text: x.get("value") for x in options
                if x.get("value") != ""}

    def _parse_languages(self, list_page):
        options = (list_page.find("select", {"id": "language_id"})
                   .findAll("option"))
        return {x.text: x.get("value") for x in options
                if x.get("value") != ""}

    def _parse_countries(self, list_page):
        options = (list_page.find("select", {"id": "historic_country_id"})
                   .findAll("option"))
        return {x.text: x.get("value") for x in options
                if x.get("value") != ""}

    def _parse_metadata(self, mubi_id):
        page = BS(self._session.get(self._mubi_urls["fulldetails"] % mubi_id)
                  .content)
        full_cast = page.findAll("h3", "film_cast")

        year = page.find("h3", "film_year").text
        rating = float(self._regexps["rating"].match(
                 page.find("li", "current_rating").text)
                 .group(1))
        cast = [x.text.replace("CAST", "").split(",")
                for x in full_cast if x.span.text == 'CAST'][0]
        director = [x.text.replace("DIR", "").replace(",", ", ")
                    for x in full_cast if x.span.text == 'DIR'][0]
        plot = "\n".join([x.text for x in
                          page.find("div", "content greenbg clear")
                          .findAll("p")])
        title = page.find("h1", "film_title blue").text
        try: originaltitle = page.find("h2", "film_title notbold blue").text
        except AttributeError: originaltitle = None
        duration = page.find("div", text=self._regexps["duration"])
        writer = [x.text.replace("SCR","").replace(",", ", ")
                  for x in full_cast if x.span.text == 'SCR'][0]
        try: playcount = int(page.find("div", "film_views").span.text
                             .replace(",",""))
        except AttributeError: playcount = None
        try: trailer = (BS(self._session.get(page.find("a", "watch_trailer")
                                             .get("href")).content)
                        .find("div", "flashplayer").get("data-video_url"))
        except AttributeError: trailer = None
        try: audio_language = (self._regexps["audio_lang"].match(
                                    page.find("div", "film_subtitle_language",
                                              text=self._regexps["audio_lang"]))
                               .group(1))
        except TypeError: audio_language = None
        try: subtitle_language = (self._regexps["sub_lang"].match(
                                    page.find("div", "film_subtitle_language",
                                              text=self._regexps["sub_lang"]))
                                  .group(1))
        except TypeError: subtitle_language = None
        return VideoMetadata(year=year, rating=rating, cast=cast,
                             director=director, plot=plot, title=title,
                             originaltitle=originaltitle, duration=duration,
                             writer=writer, playcount=playcount,
                             trailer=trailer, audio_language=audio_language,
                             subtitle_language=subtitle_language,
                             plotoutline=None)

    def login(self, username, password):
        self._username = username
        self._password = password
        login_page = self._session.get(self._mubi_urls["login"]).content
        auth_token = (BS(login_page).find("input",
                                          {"name": "authenticity_token"})
                      .get("value"))
        session_payload = {'utf8': '✓',
                           'authenticity_token': auth_token,
                           'email': username,
                           'password': password,
                           'x': 0,
                           'y': 0}
        self._logger.debug("Logging in as user '%s', auth token is '%s'"
                             % (username, auth_token))
        landing_page = self._session.post(self._mubi_urls["session"],
                                          data=session_payload)
        self._userid = BS(landing_page.content).find(
                "a", "user_avatar").get("href").split("/")[-1]
        self._logger.debug("Login succesful, user ID is '%s'" % self._userid)

    def is_film_available(self, name):
        # Sometimes we have to load a prescreen page before we can retrieve
        # the film's URL
        if not self._session.head(self._mubi_urls["video"] % name):
            prescreen_page = self._session.get(self._mubi_urls["prescreen"]
                                               % name)
            if not prescreen_page:
                raise Exception("Oops, something went wrong while scraping :(")
            elif self._regexps["watch_page"].match(prescreen_page.url):
                return True
            else:
                availability = BS(prescreen_page.content).find(
                                  "div", "film_viewable_status ").text
                return not "Not Available to watch" in availability
        else:
            return True

    def get_play_url(self, name):
        if not self.is_film_available(name):
            raise Exception("This film is not available in your country.")
        return self._session.get(self._mubi_urls["video"] % name).content

    def search_film(self, term):
        results = self._search(term)
        filtered = [x for x in results if x['category'] == "Films"]
        final = [Film(title=x['label'],
                      mubi_id=x['id'],
                      filmstill=self._get_filmstill(x['url'].split("/")[-1]))
                 for x in filtered if self.is_film_available(x['id'])]
        return final

    def search_person(self, term):
        results = self._search(term)
        final = [Person(name=x['label'],
                        mubi_id=x['id'],
                        portrait=self._get_person_image(x['id']))
                 for x in results if x['category'] == "People"]
        return final

    def get_person_films(self, person_id):
        person_page = self._session.get(self._mubi_urls["person"] % person_id)
        return self._parse_watchable_titles(person_page.content)

    def get_all_films(self, page=1, sort_key='popularity', genre=None,
                      country=None, language=None):
        if sort_key not in self._SORT_KEYS:
            raise Exception("Invalid sort key, must be one of %s"
                            % self._SORT_KEYS.__repr__())
        params = {'page': page,
                  'sort': sort_key}
        if genre:
            params["category_id"] = genre
        elif country:
            params["historic_country_id"] = country
        elif language:
            params["language_id"] = language
        list_url = urljoin(self._mubi_urls["list"], "?" + urlencode(params))
        list_page = self._session.get(list_url)
        num_pages = ceil(int(BS(list_page.content)
                         .find("strong", {"id": "result_count"}).text
                         .split()[0]) / 20.0)
        return (num_pages, self._parse_watchable_titles(list_page.content))

    def get_all_programs(self):
        programs_page = self._session.get(self._mubi_urls["programs"])
        programs = (BS(programs_page.content)
                    .findAll("div", {"class": self._regexps["program"]}))
        return [Program(title=x.find("h2").text,
                        identifier=x.find("a").get("href").split("/")[-1],
                        picture=x.find("img").get("src"))
                for x in programs]

    def get_program_films(self, cinema):
        program_page = self._session.get("/"
                .join([self._mubi_urls["single_program"], cinema]))
        items = (BS(program_page.content)
                 .findAll("div", {"class": self._regexps["item"]}))
        films = []
        for item in items:
            film = dict()
            film['id'] = item.get("data-item-id")
            film['title'] = item.find("h2", "film_title ").text
            film['director'] = item.find("h2", "film_director"
                                         ).find("a").text
            film['country_year'] = item.find("h3", "film_country_year").text
            film['thumb'] = item.find("img").get("src").replace("w320", "w448")
            films.append(film)
        return [Film(title="%s: %s (%s)" % (x['director'], x['title'],
                                            x['country_year']),
                     mubi_id=x['id'],
                     filmstill=x['thumb'])
                for x in films]

    def get_watchlist(self, userid=None):
        if not userid:
            userid = self._userid
        return [self._get_shortdetails(x)
                for x in json.loads(self._session
                                    .get(self._mubi_urls["watchlist"] % userid)
                                    .content)]
