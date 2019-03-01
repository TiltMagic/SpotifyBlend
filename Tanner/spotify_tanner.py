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
tanner.create_playlist("Alex's Recents")
tanner.create_playlist("Fewchaboi's Recents")


def main_updater():
    tanner.setup()
    tanner.share_recent_track_ids('tanner')

    tanner.update_playlist_with_recent_tracks(
        "Alex's Recents", from_friend='alex', amount=3, max_length=15)

    tanner.update_playlist_with_recent_tracks("Fewchaboi's Recents", max_length=15)


schedule.every(1).minutes.do(main_updater)

while True:
    schedule.run_pending()
