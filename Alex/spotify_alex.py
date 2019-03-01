import spotipy
import pprint
import types
import schedule
import time
import json
from spotipy import util
from user import User


# Keep this user data in a diffrent location, currently here for testing
alex_info = {'client_id': 'a0a2e7215e7240a687305ee86b6147f6',
             'client_secret': '126c1d67b439435181535bdb652a0cd7',
             'redirect_uri': 'http://localhost:8888/callback/',
             'username': 'alexthomastilley',
             'scope': 'user-read-recently-played playlist-modify-public'
             }


alex = User(**alex_info)
# alex.build_friend_recent_playlist('tanner', 'Fewchaboi Hits')


def main_updater():
    alex.setup()

    alex.create_playlist('Fewchaboi Hits')
    alex.update_playlist_with_tracks(
        'Fewchaboi Hits', from_friend='tanner', amount=3, max_length=15)
    alex.update_playlist_with_tracks('Fewchaboi Hits', amount=3, max_length=15)

    alex.update_playlist_with_tracks('Recent Tracks', max_length=15)


schedule.every(1).minutes.do(main_updater)

while True:
    schedule.run_pending()


#
# def main():
#     alex.setup()
#     track_data = alex.get_recently_played_tracks_data()
#     track_ids = alex.get_track_ids_from_data(track_data)
#     # alex.share_data(track_ids, 'song_data', 'alex')
#     # self.share_data(track_ids, 'song_data', 'alex')
#     alex.show_recently_played_tracks(5)
#     alex.update_recently_played_tracks_playlist()
