# -*- coding: utf-8 -*-


from requests import Session
from bs4 import BeautifulSoup
from urllib3 import disable_warnings
from urllib.parse import urlparse
from time import time
from re import match, IGNORECASE


disable_warnings()


base_url = 'http://rezkery.com/'


def get_session() -> Session:
    session = Session()
    session.verify = False
    session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0'
    return session


def parse_urls(_urls: str):
    result = []

    for text in _urls.split(','):
        m = match(r"(?P<quality>\[\d+p\s?(ultra)?\s?\]).+(?P<url>https.+)", text, flags=IGNORECASE)

        if not m:
            continue

        result.append([m.group('quality').replace('[', '').replace(']', ''), m.group('url')])
    # 193
    return result


class Episode:
    def __init__(self, title, season_id, episode_id, data):
        self.title = title
        self.season_id = season_id
        self.episode_id = episode_id
        self.data = data

    @property
    def terrible_quality(self) -> str:
        return self.data[0][1]

    @property
    def best_quality(self) -> str:
        return self.data[-1][1]

    @property
    def all_qualities(self) -> str:
        return [episode[0] for episode in self.data]

    @property
    def all_urls(self) -> str:
        return [item[1] for item in self.data]

    def __getitem__(self, index) -> list:
        return self.data[index]

    def __repr__(self) -> str:
        return '<Episode of ' + self.title + ', max_quality=' + self.data[-1][0] + '>'


class SeriesPage:
    def __init__(self, id: int, title: str, about: str, preview_url: str, _page: BeautifulSoup, _session: Session, trailer_url=None):
        self.id = id
        self.title = title
        self.about = about
        self.preview_url = preview_url
        self.trailer_url = trailer_url
        self._page = _page
        self._session = _session
        self.__episodes = None

    @property
    def translators(self) -> list:
        return self._get_translators()

    def _get_translators(self):
        translator_data = self._page.find_all('li', class_='b-translator__item')

        if not translator_data:
            return [56]
        else:
            return [[data['data-translator_id'], data['title']] for data in translator_data]

    @property
    def _episodes(self):
        if not self.__episodes:
            self._init_data()

        return self.__episodes

    def _init_data(self, translator_id=None):
        episodes = []

        if not translator_id:
            translator_id = self.translators[0][0]

        req_data = {'id': str(self.id), 'translator_id': '56', 'season': '1', 'episode': '1', 'action': 'get_stream'}

        if translator_id:
            req_data['translator_id'] = translator_id

        for episode_data in self._page.find('ul', class_='b-simple_episodes__list clearfix'):
            season = episode_data['data-season_id']
            episode_id = episode_data['data-episode_id']

            req_data['season'] = season
            req_data['episode'] = episode_id

            _data = self._session.post('{}ajax/get_cdn_series/'.format(base_url), data=req_data, params={'t': int(time()*1000)}).json()
            data = parse_urls(_data['url'].replace('\\', ''))
            episodes.append(Episode(self.title, season, episode_id, data))

        self.__episodes = episodes

    def __getitem__(self, index) -> list:
        return self.__episodes[index]

    def __repr__(self) -> str:
        return '<Series id={} title="{}">'.format(self.id, self.title)


class FilmsPage:
    def __init__(self, id: int, title: str, about: str, preview_url: str, _page: BeautifulSoup, _session: Session, trailer_url=None):
        self.id = id
        self.title = title
        self.about = about
        self.preview_url = preview_url
        self.trailer_url = trailer_url
        self._page = _page
        self._session = _session
        self.__data = None

    @property
    def terrible_quality(self) -> str:
        return self._data[0][1]

    @property
    def best_quality(self) -> str:
        return self._data[-1][1]

    @property
    def all_qualities(self) -> str:
        return [item[0] for item in self._data]

    @property
    def all_urls(self) -> str:
        return [item[1] for item in self._data]

    @property
    def translators(self) -> list:
        return self._get_translators()

    def _get_translators(self):
        translator_data = self._page.find_all('li', class_='b-translator__item')

        if not translator_data:
            return [56]
        else:
            return [[data['data-translator_id'], data['title']] for data in translator_data]

    @property
    def _data(self):
        if not self.__data:
            self._init_data()

        return self.__data

    def _init_data(self, translator_id=None):
        if not translator_id:
            translator_id = self.translators[0][0]

        req_data = {'id': str(self.id), 'translator_id': '56', 'is_camrip': '0', 'is_ads': '0', 'is_director': '0', 'action': 'get_movie'}

        if translator_id:
            req_data['translator_id'] = translator_id

        print(self._page.find_all('script', text='stream.voidboost.in'))

        _data = self._session.post('{}ajax/get_cdn_series/'.format(base_url), data=req_data, params={'t': int(time()*1000)}).json()

        print(_data)

        data = parse_urls(_data['url'].replace('\\', ''))
        self.__data = data

    def __getitem__(self, index) -> list:
        return self._data[index]

    def __repr__(self) -> str:
        return '<Film id={} title="{}">'.format(self.id, self.title)


def get_object_data(url: str) -> SeriesPage:
    session = get_session()
    page = BeautifulSoup(session.get(url).text, 'html.parser')

    _url_parse = urlparse(url)

    id = int(_url_parse.path.split('/')[-1].split('-')[0])
    title = page.find('div', class_='b-post__title').h1.text
    about = page.find('div', class_='b-post__description_text')
    about = about.text if about else None
    preview_url = page.find('div', class_='b-sidecover').a.img['src']
    _trailer = session.post('{}engine/ajax/gettrailervideo.php'.format(base_url), data={'id': id}).json()

    if _trailer.get('code'):
        trailer_url = BeautifulSoup(_trailer['code'], 'html.parser').iframe['src']
    else:
        trailer_url = None

    if _url_parse.path.startswith('/series'):
        return SeriesPage(id, title, about, preview_url, page, session, trailer_url=trailer_url)
    elif _url_parse.path.startswith('/films'):
        return FilmsPage(id, title, about, preview_url, page, session, trailer_url=trailer_url)


def search(query: str):
    session = get_session()

    results = []

    req = session.get('{}search/'.format(base_url), params={'do': 'search', 'subaction': 'search', 'q': query})

    bs = BeautifulSoup(req.text, 'html.parser')

    if bs.find('div', class_='b-searchresults__st'):
        return []

    for item in bs.find_all('div', class_='b-content__inline_item'):
        results.append(get_object_data(item['data-url']))

    return results
