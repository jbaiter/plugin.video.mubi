# -*- coding: utf-8 -*-

import json
import re
from math import ceil
from urllib import urlencode
from urlparse import urljoin

import requests
from BeautifulSoup import BeautifulSoup as BS

class Mubi(object):
    _URL_MUBI = "http://mubi.com"
    _URL_MUBI_SECURE = "https://mubi.com"
    _URL_LOGIN = urljoin(_URL_MUBI_SECURE, "login")
    _URL_SESSION = urljoin(_URL_MUBI_SECURE, "session")
    _URL_SEARCH = urljoin(_URL_MUBI, "services/films/search.json?term=%s")
    _URL_PROGRAMS = urljoin(_URL_MUBI, "cinemas")
    _URL_SINGLE_PROGRAM = urljoin(_URL_MUBI, "programs")
    _URL_VIDEO = urljoin(_URL_MUBI, "films/%s/secure_url")
    _URL_PRESCREEN = urljoin(_URL_MUBI, "films/%s/prescreen")
    _URL_LIST = urljoin(_URL_MUBI, "watch")
    _URL_PERSON = urljoin(_URL_MUBI, "cast_members/%s")
    _URL_LOGOUT = urljoin(_URL_MUBI, "logout")
    _URL_FILMSTILL = "http://s3.amazonaws.com/auteurs_production/images/film/%s/w448/%s.jpg"
    _URL_SHORTDETAILS = urljoin(_URL_MUBI, "/services/films/tooltip?id=%s&country_code=US&locale=en_US")
    _URL_FULLDETAILS = urljoin(_URL_MUBI, "films/%s")
    _URL_WATCHLIST = urljoin(_URL_MUBI, "/users/%s/watchlist.json")

    _SORT_KEYS = ['popularity', 'recently_added', 'rating', 'year', 'running_time']

    _COUNTRIES = {  "Anonymous Proxy": 1,
                    "Satellite Provider": 2,
                    "Andorra": 3,
                    "United Arab Emirates": 4,
                    "Antigua and Barbuda": 6,
                    "Anguilla": 7,
                    "Albania": 8,
                    "Armenia": 9,
                    "Netherlands Antilles": 10,
                    "Angola": 11,
                    "Asia/Pacific Region": 12,
                    "Antarctica": 13,
                    "Argentina": 14,
                    "American Samoa": 15,
                    "Austria": 16,
                    "Australia": 17,
                    "Aruba": 18,
                    "Aland Islands": 19,
                    "Azerbaijan": 20,
                    "Bosnia and Herzegovina": 21,
                    "Barbados": 22,
                    "Bangladesh": 23,
                    "Belgium": 24,
                    "Burkina Faso": 25,
                    "Bulgaria": 26,
                    "Bahrain": 27,
                    "Burundi": 28,
                    "Benin": 29,
                    "Bermuda": 30,
                    "Brunei Darussalam": 31,
                    "Bolivia": 32,
                    "Brazil": 33,
                    "Bahamas": 34,
                    "Bhutan": 35,
                    "Bouvet Island": 36,
                    "Botswana": 37,
                    "Belarus": 38,
                    "Belize": 39,
                    "Canada": 40,
                    "Cocos (Keeling) Islands": 41,
                    "Congo, The Democratic Republic of the": 42,
                    "Central African Republic": 43,
                    "Congo": 44,
                    "Switzerland": 45,
                    "Cote d'Ivoire": 46,
                    "Cook Islands": 47,
                    "Chile": 48,
                    "Cameroon": 49,
                    "China": 50,
                    "Colombia": 51,
                    "Costa Rica": 52,
                    "Cuba": 53,
                    "Cape Verde": 54,
                    "Christmas Island": 55,
                    "Cyprus": 56,
                    "Czech Republic": 57,
                    "Germany": 58,
                    "Djibouti": 59,
                    "Denmark": 60,
                    "Dominica": 61,
                    "Dominican Republic": 62,
                    "Algeria": 63,
                    "Ecuador": 64,
                    "Estonia": 65,
                    "Egypt": 66,
                    "Western Sahara": 67,
                    "Eritrea": 68,
                    "Spain": 69,
                    "Ethiopia": 70,
                    "Europe": 71,
                    "Finland": 72,
                    "Fiji": 73,
                    "Falkland Islands (Malvinas)": 74,
                    "Micronesia, Federated States of": 75,
                    "Faroe Islands": 76,
                    "France": 77,
                    "Gabon": 78,
                    "United Kingdom": 79,
                    "Grenada": 80,
                    "Georgia": 81,
                    "French Guiana": 82,
                    "Guernsey": 83,
                    "Ghana": 84,
                    "Gibraltar": 85,
                    "Greenland": 86,
                    "Gambia": 87,
                    "Guinea": 88,
                    "Guadeloupe": 89,
                    "Equatorial Guinea": 90,
                    "Greece": 91,
                    "South Georgia and the South Sandwich Islands": 92,
                    "Guatemala": 93,
                    "Guam": 94,
                    "Guinea-Bissau": 95,
                    "Guyana": 96,
                    "Hong Kong": 97,
                    "Heard Island and McDonald Islands": 98,
                    "Honduras": 99,
                    "Croatia": 100,
                    "Haiti": 101,
                    "Hungary": 102,
                    "Indonesia": 103,
                    "Ireland": 104,
                    "Israel": 105,
                    "Isle of Man": 106,
                    "India": 107,
                    "British Indian Ocean Territory": 108,
                    "Iraq": 109,
                    "Iran": 110,
                    "Iceland": 111,
                    "Italy": 112,
                    "Jersey": 113,
                    "Jamaica": 114,
                    "Jordan": 115,
                    "Japan": 116,
                    "Kenya": 117,
                    "Kyrgyzstan": 118,
                    "Cambodia": 119,
                    "Kiribati": 120,
                    "Comoros": 121,
                    "Saint Kitts and Nevis": 122,
                    "North Korea": 123,
                    "South Korea": 124,
                    "Kuwait": 125,
                    "Cayman Islands": 126,
                    "Kazakhstan": 127,
                    "Lao People's Democratic Republic": 128,
                    "Lebanon": 129,
                    "Saint Lucia": 130,
                    "Liechtenstein": 131,
                    "Sri Lanka": 132,
                    "Liberia": 133,
                    "Lesotho": 134,
                    "Lithuania": 135,
                    "Luxembourg": 136,
                    "Latvia": 137,
                    "Libyan Arab Jamahiriya": 138,
                    "Morocco": 139,
                    "Monaco": 140,
                    "Moldova, Republic of": 141,
                    "Montenegro": 142,
                    "Madagascar": 143,
                    "Marshall Islands": 144,
                    "Macedonia": 145,
                    "Mali": 146,
                    "Myanmar": 147,
                    "Mongolia": 148,
                    "Macao": 149,
                    "Northern Mariana Islands": 150,
                    "Martinique": 151,
                    "Mauritania": 152,
                    "Montserrat": 153,
                    "Malta": 154,
                    "Mauritius": 155,
                    "Maldives": 156,
                    "Malawi": 157,
                    "Mexico": 158,
                    "Malaysia": 159,
                    "Mozambique": 160,
                    "Namibia": 161,
                    "New Caledonia": 162,
                    "Niger": 163,
                    "Norfolk Island": 164,
                    "Nigeria": 165,
                    "Nicaragua": 166,
                    "Netherlands": 167,
                    "Norway": 168,
                    "Nepal": 169,
                    "Nauru": 170,
                    "Niue": 171,
                    "New Zealand": 172,
                    "Oman": 173,
                    "Panama": 174,
                    "Peru": 175,
                    "French Polynesia": 176,
                    "Papua New Guinea": 177,
                    "Philippines": 178,
                    "Pakistan": 179,
                    "Poland": 180,
                    "Saint Pierre and Miquelon": 181,
                    "Pitcairn": 182,
                    "Puerto Rico": 183,
                    "Palestinian Territory": 184,
                    "Portugal": 185,
                    "Palau": 186,
                    "Paraguay": 187,
                    "Qatar": 188,
                    "Reunion": 189,
                    "Romania": 190,
                    "Serbia": 191,
                    "Russia": 192,
                    "Rwanda": 193,
                    "Saudi Arabia": 194,
                    "Solomon Islands": 195,
                    "Seychelles": 196,
                    "Sudan": 197,
                    "Sweden": 198,
                    "Singapore": 199,
                    "Saint Helena": 200,
                    "Slovenia": 201,
                    "Svalbard and Jan Mayen": 202,
                    "Slovakia": 203,
                    "Sierra Leone": 204,
                    "San Marino": 205,
                    "Senegal": 206,
                    "Somalia": 207,
                    "Suriname": 208,
                    "Sao Tome and Principe": 209,
                    "El Salvador": 210,
                    "Syrian Arab Republic": 211,
                    "Swaziland": 212,
                    "Turks and Caicos Islands": 213,
                    "Chad": 214,
                    "French Southern Territories": 215,
                    "Togo": 216,
                    "Thailand": 217,
                    "Tajikistan": 218,
                    "Tokelau": 219,
                    "Timor-Leste": 220,
                    "Turkmenistan": 221,
                    "Tunisia": 222,
                    "Tonga": 223,
                    "Turkey": 224,
                    "Trinidad and Tobago": 225,
                    "Tuvalu": 226,
                    "Taiwan": 227,
                    "Tanzania, United Republic of": 228,
                    "Ukraine": 229,
                    "Uganda": 230,
                    "United States Minor Outlying Islands": 231,
                    "United States": 232,
                    "Uruguay": 233,
                    "Uzbekistan": 234,
                    "Holy See (Vatican City State)": 235,
                    "Saint Vincent and the Grenadines": 236,
                    "Venezuela": 237,
                    "Virgin Islands, British": 238,
                    "Virgin Islands, U.S.": 239,
                    "Vietnam": 240,
                    "Vanuatu": 241,
                    "Wallis and Futuna": 242,
                    "Samoa": 243,
                    "Yemen": 244,
                    "Mayotte": 245,
                    "South Africa": 246,
                    "Zambia": 247,
                    "Zimbabwe": 248,
                    "Soviet Union": 249,
                    "Yugoslavia": 250,
                    "West Germany": 251,
                    "Scotland": 252,
                    "Czechoslovakia": 253,
                    "East Germany": 254,
                    "Republic of Kosovo": 255 }
    _LANGUAGES = {  "Aboriginal": 1,
                    "Afrikaans": 2,
                    "Albanian": 3,
                    "Algonquin": 4,
                    "Amharic": 5,
                    "Arabic": 6,
                    "Armenian": 7,
                    "Bambara": 8,
                    "Bengali": 9,
                    "Bosnian": 10,
                    "Burmese": 11,
                    "Cantonese": 12,
                    "Catalan": 13,
                    "Croatian": 14,
                    "Czech": 15,
                    "Danish": 17,
                    "Dutch": 18,
                    "Dzongkha": 19,
                    "English": 20,
                    "Farsi": 21,
                    "Filipino": 22,
                    "Finnish": 23,
                    "Flemish": 24,
                    "French": 25,
                    "Galician": 26,
                    "Georgian": 27,
                    "German": 28,
                    "Greek": 29,
                    "Haitian": 30,
                    "Hebrew": 31,
                    "Hindi": 32,
                    "Hungarian": 33,
                    "Icelandic": 34,
                    "Irish": 35,
                    "Italian": 36,
                    "Japanese": 37,
                    "K'iche'": 38,
                    "Kazakh": 39,
                    "Korean": 40,
                    "Kurdish": 41,
                    "Kyrgyz": 42,
                    "Latin": 43,
                    "Malayalam": 44,
                    "Mandarin": 45,
                    "Mende": 46,
                    "Mongolian": 47,
                    "Nepali": 48,
                    "Norwegian": 49,
                    "Pashtu": 50,
                    "Persian": 51,
                    "Polish": 52,
                    "Portuguese": 53,
                    "Punjabi": 54,
                    "Romanian": 55,
                    "Russian": 56,
                    "Serbian": 57,
                    "Serbo-Croatian": 58,
                    "Silent": 59,
                    "Slovak": 60,
                    "Slovenian": 61,
                    "Somali": 62,
                    "South Korean": 63,
                    "Spanish": 64,
                    "Swahili": 65,
                    "Swedish": 66,
                    "Tagalog": 67,
                    "Taiwanese": 68,
                    "Tajik": 69,
                    "Thai": 70,
                    "Tibetan": 71,
                    "Turkish": 72,
                    "Vietnamese": 73,
                    "Welsh": 74,
                    "Wolof": 75,
                    "Yiddish": 76,
                    "Malinka": 77,
                    "Inuktitut": 78,
                    "Maori": 79,
                    "Guarani": 80,
                    "Nyanja": 81,
                    "Ukrainian": 82,
                    "Esperanto": 83,
                    "Ewe": 84,
                    "Hassaniya": 85,
                    "Estonian": 86,
                    "Indonesian": 87,
                    "Dari": 88,
                    "Tamil": 89,
                    "Zulu": 90,
                    "Xhosa": 91,
                    "Berber": 92,
                    "Bulgarian": 93,
                    "Urdu": 94,
                    "Martu": 95,
                    "Khmer": 96,
                    "Afghan": 97,
                    "Karen": 98,
                    "Maltese": 99,
                    "Aymara": 100,
                    "Inuit": 101,
                    "Kikuyu": 102,
                    "Lithuanian": 103,
                    "Latvian": 104,
                    "Ndebele": 105,
                    "Shona": 106,
                    "American Sign Language": 107,
                    "Faliasch": 108,
                    "Greenlandic": 109,
                    "Khanty": 110,
                    "Korowai": 111,
                    "Kunwinjku": 112,
                    "Ladakhi": 113,
                    "Moso": 114,
                    "Ojihimba": 115,
                    "Saami": 116,
                    "Sardinian": 117,
                    "Tamashek": 118,
                    "Macedonian": 119,
                    "Kinyarwanda": 120,
                    "Romany": 121,
                    "Shanghainese": 122,
                    "Telugu": 123,
                    "Basque": 124,
                    "Maya": 125,
                    "None": 126,
                    "Lingala": 127,
                    "Dioula": 128,
                    "Moré": 129,
                    "Peul": 130,
                    "Malagasy": 131,
                    "Gujarati": 132,
                    "Kalmyk-Oirat": 133,
                    "Malay": 134,
                    "Bemba": 135,
                    "Hokkien": 136,
                    "Yoruba": 137,
                    "Sinhala": 138,
                    "Swiss German": 139,
                    "Chechen": 140,
                    "Kabuverdianu": 141,
                    "Hunan": 142,
                    "Marathi": 143,
                    "French Sign Language": 144,
                    "Visayan": 145,
                    "Navajo": 146,
                    "Hopi": 147,
                    "Quechua": 148,
                    "Mapudungun": 149,
                    "Dogri": 150,
                    "Kangri": 151,
                    "Hawaiian": 152,
                    "Uzbek": 153,
                    "Oriya": 154,
                    "Azeri": 155,
                    "Mazatec": 156,
                    "Tzotzil": 157,
                    "Tachelhit": 158,
                    "Cree": 159,
                    "Tok Pisin": 160,
                    "Faroese": 161,
                    "Igbo": 162,
                    "Kabyle": 163,
                    "Lao": 164,
                    "Abkhazian": 165,
                    "Dong": 166,
                    "Kannada": 167,
                    "Sioux": 168,
                    "Tigrigna": 169,
                    "Pular": 170,
                    "Susu": 171,
                    "Tonga": 172,
                    "Creole": 173,
                    "Nenets": 174,
                    "Samoan": 175,
                    "British Sign Language": 176,
                    "Rusyn": 177,
                    "Palawanon": 178,
                    "Dinka": 179,
                    "Baeggu": 180,
                    "Sindhi": 181,
                    "Hmong": 182,
                    "Hausa": 183,
                    "Sotho": 184,
                    "Mohawk": 185,
                    "Luo": 186,
                    "Min Nan": 187,
                    "Morisyen": 188,
                    "Maldivian": 189,
                    "Sotho": 190,
                    "Arabic Sign Language": 191,
                    "Sicilian": 192,
                    "Turkmen": 193,
                    "Djerma": 194,
                    "Serer": 195,
                    "Kashmiri": 196,
                    "Limbu": 197,
                    "Tarahumara": 198,
                    "Assamese": 199,
                    "Acholi": 200,
                    "Sichuanese": 201,
                    "Luganda": 202 }
    _CATEGORIES = { "Children & Family": 19,
                    "Comedy": 29,
                    "Horror": 36,
                    "Documentary": 48,
                    "Action": 54,
                    "Science Fiction": 64,
                    "TV / Video": 73,
                    "Drama": 91,
                    "Gay and Lesbian": 101,
                    "Musical": 105,
                    "Thriller": 107,
                    "Animation": 109,
                    "Faith and Spirituality": 111,
                    "Adventure": 466,
                    "Road Movie": 619,
                    "Romance": 620,
                    "Erotica": 942,
                    "Western": 951,
                    "Fantasy": 991,
                    "Experimental Film": 1005,
                    "Exploitation": 1030 }
    _USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_5_8) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.151 Safari/535.19"

    def __init__(self):
        self._session = requests.session()
        self._session.headers = {'User-Agent': self._USER_AGENT}
        
    def __del__(self):
        self._session.get(self._URL_LOGOUT)

    def _parse_watchable_titles(self, page):
        items = [x for x in BS(page).findAll("div", {"class": re.compile("item.*")})
                 if (x.findChild("h2")
                 and x.findChild("div", {"class": re.compile("watch_link.*")}))]
        return [(x.find("h2").text, x.get("data-item-id"),
                 x.find("div", {"class": "cropped_image"}
                        ).find("img").get("src").replace("w192", "w448"))
                for x in items]

    def _search(self, term):
        return json.loads(self._session.get(self._URL_SEARCH % term).content)

    def _get_shortdetails(self, mubi_id):
        return json.loads(self._session.get(self._URL_SHORTDETAILS % unicode(mubi_id)
            ).content)

    def _get_filmstill(self, name):
        return self._URL_FILMSTILL % (name, name)

    def _resolve_id(self, mubi_id):
        return self._session.head(self._URL_FULLDETAILS % mubi_id
                ).headers['location'].split("/")[-1]

    def login(self, username, password):
        self._username = username
        self._password = password
        login_page = self._session.get(self._URL_LOGIN).content
        auth_token = BS(login_page).find("input", {"name": "authenticity_token"}).get("value")
        session_payload = { 'utf8': '✓',
                            'authenticity_token': auth_token,
                            'email': username,
                            'password': password,
                            'x': 0,
                            'y': 0 }
        landing_page = self._session.post(self._URL_SESSION,
                                          data=session_payload)
        self._userid = BS(landing_page.content).find(
                "a", {"class": "user_avatar"}).get("href").split("/")[-1]

    def is_film_available(self, name):
        if not self._session.head(self._URL_VIDEO % name):
            prescreen_page = self._session.get(self._URL_PRESCREEN % name)
            if not prescreen_page:
                raise Exception("Ooops, something went wrong while scraping :-(")
            else:
                availability = BS(prescreen_page.content).find(
                        "div", {"class": "film_viewable_status "}).text
                return not "Not Available to watch" in availability
        else:
            return True

    def get_play_url(self, name):
        if not self.is_film_available(name):
            raise Exception("This film is not available in your country.")
        return self._session.get(self._URL_VIDEO % name).content

    
    def search_film(self, term):
        results = self._search(term)
        filtered = [x for x in results if x['category'] == "Films"]
        final = [(x['label'], x['id'],
                  self._get_filmstill(x['url'].split("/")[-1]))
                 for x in filtered if self.is_film_available(x['id'])]
        return final

    def search_person(self, term):
        results = self._search(term)
        final = [(x['label'], x['id'])
                 for x in results if x['category'] == "People"]
        return final
    
    def get_person_films(self, person_id):
        person_page = self._session.get(self._URL_PERSON % person_id)
        return self._parse_watchable_titles(person_page.content)

    def get_all_films(self, page=1, sort_key='popularity', genre=None, country=None, language=None):
        if sort_key not in self._SORT_KEYS:
            raise Exception("Invalid sort key, must be one of %s" % self._SORT_KEYS.__repr__())
        params = { 'page': page,
                   'sort': sort_key }
        if genre:
            params["category_id"] = genre
        elif country:
            params["historic_country_id"] = country
        elif language:
            params["language_id"] = language
        list_url = urljoin(self._URL_LIST, "?" + urlencode(params))
        list_page = self._session.get(list_url)
        num_pages = ceil(int(BS(list_page.content)
                         .find("strong", {"id": "result_count"}).text
                         .split()[0])/20.0)
        return (num_pages, self._parse_watchable_titles(list_page.content))

    def get_all_programs(self):
        programs_page = self._session.get(self._URL_PROGRAMS)
        programs = BS(programs_page.content).findAll(
                    "div", {"class": re.compile("use6.*")})
        return [(x.find("h2").text, x.find("a").get("href").split("/")[-1],
                 x.find("img").get("src")) for x in programs]

    def get_program_films(self, cinema):
        program_page = self._session.get("/".join([self._URL_SINGLE_PROGRAM, cinema]))
        items = BS(program_page.content).findAll("div",{"class": re.compile("item.*")})
        films = []
        for item in items:
            film = dict()
            film['id'] = item.get("data-item-id")
            film['title'] = item.find("h2", {"class": "film_title "}).text
            film['director'] = item.find("h2", {"class": "film_director"}
                                         ).find("a").text
            film['country_year'] = item.find("h3", {"class": "film_country_year"}).text
            film['thumb'] = item.find("img").get("src").replace("w320", "w448")
            films.append(film)
        return [("%s: %s (%s)" % (x['director'], x['title'], x['country_year']), x['id'],
                 x['thumb'])
                for x in films]

    def get_watchlist(self, userid=None):
        if not userid:
            userid = self._userid
        items = [self._get_shortdetails(x)
                for x in json.loads(
                    self._session.get(self._URL_WATCHLIST % userid).content)]
        return [("%s (%s %s)" % (x['title'], x['primary_country'], x['year']),
                 unicode(x['id']), self._get_filmstill(self._resolve_id(x['id'])))
                 for x in items]
