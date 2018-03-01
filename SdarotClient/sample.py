from sdarot_downloader import *
from sdarot import *
#show = SdarotSeason.search("friends", allow_ambiguous=True)[0]
show = SdarotShow(6)
season = SdarotSeason(show, 2)
# episode = SdarotEpisode(season, 1)
episodes = season.episodes
for e in episodes:
    # OR: just call e.generate_url() and put the url in Chrome or VLC.
    # generate_url() takes 30 seconds because the server make sure you waited.
    print("Downloading {}".format(e))
    s = SdarotEpisodeDownloader(e)
    fn = "friends.s02.e{}.mp4".format(e.episode_id)
    print(fn)
    s.start(fn)