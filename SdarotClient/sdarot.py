import requests
import time
import urllib
from lxml import html
import re
import json


SDAROT_HOST = 'zira.online'


class NoShowsFoundException(Exception): pass


class AmbiguousSearchTermException(Exception): pass


class SdarotShow(object):
    SDAROT_URL = 'http://{}'.format(SDAROT_HOST)
    AJAX_WATCH_URL  = '{}/ajax/watch'.format(SDAROT_URL)
    AJAX_INDEX_URL  = '{}/ajax/index'.format(SDAROT_URL)
    WATCH_URL  = '{}/watch'.format(SDAROT_URL)
    SHOW_URL  = '{}/watch/'.format(SDAROT_URL)
    SERVER_URL = 'http://{}/watch/{}/{}.mp4'
    JS_NAME_VAR = 'Sname'
    SLEEP_DURATION = 30

    def __init__(self, show_id, show_name=None):
        self.show_id = str(show_id)
        if not show_name:
            show_name = self._resolve_show_name(self.show_id)

        self.name = show_name

    @property
    def seasons(self):
        r = requests.get(SdarotShow.SHOW_URL + self.show_id)
        tree = html.fromstring(r.content)
        seasons = tree.xpath('//ul[@id="season"]/li[@data-season]/@data-season')
        return [SdarotSeason(self, s) for s in seasons]

    def __repr__(self):
        return 'SdarotShow({}, {})'.format(self.show_id, repr(self.name))

    @classmethod
    def _resolve_show_name(cls, show_id):
        # So ugly
        r = requests.get(cls.SHOW_URL + show_id)
        var = 'var {}'.format(cls.JS_NAME_VAR)
        name_var = [l for l in r.text.splitlines() if (var in l)]
        assert len(name_var) == 1
        name_var = name_var[0]
        name_var = re.search("var .*=(.*);", name_var)
        assert name_var is not None
        name_var = json.loads(name_var.group(1).strip())
        return name_var[0]

    @classmethod
    def search(cls, name, allow_ambiguous=False):
        url = "{}?{}".format(cls.AJAX_INDEX_URL, urllib.parse.urlencode({
            'search': name    
        }))
        r = requests.get(url)
        shows = [cls(s['id'], s['name']) for s in r.json()]

        if not shows:
            raise NoShowsFoundException('No results for term "{}".'.format(name))

        if allow_ambiguous:
            return shows

        if len(shows) > 1:
            raise AmbiguousSearchTermException('{} results for term "{}".'.format(len(shows), name))

        return shows[0] 


class SdarotSeason(object):
    def __init__(self, show, season_id):
        self._show = show
        self.season_id = season_id

    @property
    def episodes(self):
        url = "{}?{}".format(self._show.AJAX_WATCH_URL, urllib.parse.urlencode({
            'episodeList': self._show.show_id,
            'season': self.season_id
        }))
        r = requests.get(url)
        tree = html.fromstring(r.content)
        episodes = tree.xpath('//li[@data-episode]/@data-episode')
        return [SdarotEpisode(self, e) for e in episodes]

    def __repr__(self):
        return 'SdarotSeason({}, {})'.format(self._show, self.season_id)


class SdarotEpisode(object):
    def __init__(self, season, episode_id):
        self._season = season
        self._show = self._season._show
        self.episode_id = episode_id

    def generate_url(self):
        s = requests.Session()
        s.headers.update({
            'Referer': self._show.WATCH_URL,
        })

        r = s.post(self._show.AJAX_WATCH_URL, data={
            'preWatch': 'true',
            'SID': self._show.show_id,
            'season': self._season.season_id,
            'ep': self.episode_id,
        })
        token = r.text

        time.sleep(self._show.SLEEP_DURATION)

        r = s.post(self._show.AJAX_WATCH_URL, data={
            'watch': 'true',
            'token': token,
            'serie': self._show.show_id,
            'season': self._season.season_id,
            'episode': self.episode_id,
            'auth': 'false',
        })
        episode_data = r.json()

        video_id, token = episode_data['watch'].popitem()
        data = {
            'time': episode_data['time'],
            'token': token
        }

        url = self._show.SERVER_URL.format(episode_data['url'],
            video_id,
            episode_data['VID'],
            episode_data['time'])
        data = urllib.parse.urlencode(data)
        return "{}?{}".format(url, data)

    def __repr__(self):
        return 'SdarotEpisode({}, {})'.format(self._season, self.episode_id)
