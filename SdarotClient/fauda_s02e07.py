from sdarot_downloader import *
from sdarot import *

SHOW='fauda'
SEASON='01'

#show = SdarotSeason.search(SHOW, allow_ambiguous=True)[0]
show = SdarotShow(7)
season = SdarotSeason(show, SEASON)
episode = SdarotEpisode(season, 1)
episodes = season.episodes
for e in episodes:
    # OR: just call e.generate_url() and put the url in Chrome or VLC.
    # generate_url() takes 30 seconds because the server make sure you waited.
    print("Downloading {}".format(e))
    s = SdarotEpisodeDownloader(e)
    fn = "{}.s{}.e{}.mp4".format(SHOW, SEASON, e.episode_id)
    print(fn)
    s.start(fn)