import spotipy
import pprint
import types
import schedule
import time
import json
from spotipy import util
from user import User

# Keep this user data in a diffrent location, currently here for testing

tanner_info = {'client_id': '9351c95c17f942e78772701d88773cb0',
               'client_secret': '61cd3b240a224232967cf4ec32d27f27',
               'redirect_uri': 'http://localhost:8888/callback/',
               'username': 'boylet3',
               'scope': 'user-read-recently-played playlist-modify-public'
               }

tanner = User(**tanner_info)
tanner.build_friend_recent_playlist('alex', 'Alex Recents')


def main_updater():
    tanner.setup()

    track_data = tanner.get_recently_played_tracks_data()
    track_ids = tanner.get_track_ids_from_data(track_data)
    tanner.share_data(track_ids, 'track_data', 'tanner')

    tanner.update_friend_playlist_with_tracks('alex', 'Alex Recents')


schedule.every(3).minutes.do(main_updater)

while True:
    schedule.run_pending()

# def main():
#     tanner.setup()
#     track_data = tanner.get_recently_played_tracks_data()
#     track_ids = tanner.get_track_ids_from_data(track_data)[:3]
#     # tanner.share_data(track_ids, 'song_data', 'tanner')
#     # self.share_data(track_ids, 'song_data', 'tanner')
#     self.show_recently_played_tracks(5)
#     self.update_recently_played_tracks_playlist()
