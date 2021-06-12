# -*- coding: utf-8 -*-


from bs4 import BeautifulSoup
from requests import Session
from urllib3 import disable_warnings
from time import time
from urllib.parse import urlparse
from re import match, IGNORECASE, findall


class SeriesObject:
    def __init__(self, id: int, title: str, preview_url: str, _session: Session, trailer_url=None):
        self.id = id
        self.title = title
        self.preview_url = preview_url
        self.trailer_url = trailer_url
        self._session = _session


class RezkaObject:
    def __init__(self, title, preview_url, trailer_url, urls):
        self.title = title
        self.preview_url = preview_url
        self.trailer_url = trailer_url
        self.urls = urls

    @property
    def url(self):
        if isinstance(self.urls, list):
            return self.urls
        return self.urls[0]


def parse_urls(object_type: str, title: str, preview_url: str, content: str):
    result = []

    for text in content.split(','):
        m = match(r"(?P<quality>\[\d+p\s?(ultra)?\s?\]).+(?P<url>https.+)", text, flags=IGNORECASE)

        if not m:
            continue

        result.append({'object_type': object_type, 'title': title, 'preview_url': preview_url, 'quality': m.group('quality').replace('[', '').replace(']', '').replace('p', ''), 'video_url': m.group('url')})

    return result


def parse_urls_trailer(content: str):
    return BeautifulSoup(content, 'html.parser').iframe['src']


disable_warnings()

session = Session()
session.verify = False

session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0'


# session.get('https://rezka.ag/')


def get_data(view_url: str):
    skip = False

    page = BeautifulSoup(session.get(view_url).text, 'html.parser')

    id = urlparse('https://rezka.ag/series/comedy/29558-polovoe-vospitanie-2019.html').path.split('/')[-1].split('-')[0]
    title = page.find('div', class_='b-post__title').text
    preview_url = page.find('div', class_='b-sidecover').a.img['src']

    if 'series' in view_url:
        object_type = 'Сериал'
    elif 'films' in view_url:
        object_type = 'Фильм'
    else:
        object_type = ''

    # session.get(view_url)

    #with open('file.html', 'w', encoding='utf-8') as f:
        #f.write(session.get(view_url).text)

    if 'series' in view_url:
        req_data = {'id': id, 'season': 1, 'episode': 1, 'action': 'get_stream'}
        translator_data = page.find('li', class_='b-translator__item active')

        if translator_data:
            req_data['translator_id'] = translator_data['data-translator_id']

        _view_direct_not_parsed = session.post(f"https://rezka.ag/ajax/get_cdn_series/?t={int(time()*1000)}", data=req_data).json()

        if not 'url' in _view_direct_not_parsed:
            skip = True
        else:
            _view_direct_parsed = parse_urls(object_type, title, preview_url, _view_direct_not_parsed['url'].replace('\\', ''))

    elif 'films' in view_url:
        try:
            _view_direct_parsed = parse_urls(object_type, title, preview_url, findall(r'\"streams\":\"(.+?)\"', page.find_all('script')[-5].contents[0].replace('\\', ''))[0])
        except:
            skip = True

    else:
        skip = True

    if skip != True:
        _view_trailer_not_parsed = session.post('https://rezka.ag/engine/ajax/gettrailervideo.php', data={'id': id}).json()

        if not 'code' in _view_trailer_not_parsed:
            trailer_url = None
        else:
            trailer_url = BeautifulSoup(_view_trailer_not_parsed['code'], 'html.parser').iframe['src']

        return {
            'id': id,
            'object_type': object_type,
            'title': title,
            'view_url': view_url,
            'trailer_url': trailer_url,
            'preview_url': preview_url,
            'results': _view_direct_parsed
        }


def search(query: str):
    results = []

    req = session.get('https://rezka.ag/search/', params={'do': 'search', 'subaction': 'search', 'q': query})

    bs = BeautifulSoup(req.text, 'html.parser')

    for item in bs.find_all('div', class_='b-content__inline_item'):
        results.append(get_data(item['data-url']))
        '''
        skip = False

        # b-content__inline_item-cover:
        item_cover = item.find('div', class_='b-content__inline_item-cover')

        id = item['data-id']
        title = item_cover.a.img['alt']
        preview_url = item_cover.a.img['src']
        view_url = item['data-url']

        object_type = item_cover.find('span', class_='cat').text

        # session.get(view_url)

        #with open('file.html', 'w', encoding='utf-8') as f:
            #f.write(session.get(view_url).text)

        page = BeautifulSoup(session.get(view_url).text, 'html.parser')

        if 'series' in view_url:
            req_data = {'id': id, 'season': 1, 'episode': 1, 'action': 'get_stream'}
            translator_data = page.find('li', class_='b-translator__item active')

            if translator_data:
                req_data['translator_id'] = translator_data['data-translator_id']

            #translator_id = 111

            _view_direct_not_parsed = session.post(f"https://rezka.ag/ajax/get_cdn_series/?t={int(time()*1000)}", data=req_data).json()

            if not 'url' in _view_direct_not_parsed:
                skip = True
            else:
                _view_direct_parsed = parse_urls_cdn_series(_view_direct_not_parsed['url'].replace('\\', ''))

        elif 'films' in view_url:
            try:
                _view_direct_parsed = parse_urls_cdn_series(findall(r'\"streams\":\"(.+?)\"', page.find_all('script')[-5].contents[0].replace('\\', ''))[0])
            except:
                skip = True

        if skip != True:
            _view_trailer_not_parsed = session.post('https://rezka.ag/engine/ajax/gettrailervideo.php', data={'id': id}).json()

            if not 'code' in _view_trailer_not_parsed:
                trailer_url = None

            trailer_url = parse_urls_trailer(_view_trailer_not_parsed['code'])

            results.append({
                'id': id,
                'object_type': object_type,
                'title': title,
                'view_url': view_url,
                'trailer_url': trailer_url,
                'preview_url': preview_url,
                'results': _view_direct_parsed
            })
        '''

    return results


if __name__ == '__main__':
    #from pprint import pprint
    #from json import dump
    data = search('Большой хак')

    print()

    for item in data:
        print(f"ID: {item['id']}\n{item['object_type']}{item['title']}\nОбычный просмотр: {item['view_url']}\n")

        for result in item['results']:
            print(f"Качество: {result['quality']}p\nПросмотр: {result['video_url']}")

        print()

    #dump(search('Большой хак'), open('test.json', 'w'), indent=4, ensure_ascii=False)
    #pprint()
