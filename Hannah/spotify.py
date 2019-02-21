import spotipy
import pprint
import types
import schedule
import time
from spotipy import util

# Keep this user data in a diffrent location, currently here for testing

hannah_info = {'client_id': '1bbd76d2d96a49dbaabcac56f0437c89',
               'client_secret': 'bbdbddf73cb1453d841b6943ea447bd1',
               'redirect_uri': 'http://localhost:8888/callback/',
               'username': 'Hannah Hansen',
               'scope': 'user-read-recently-played playlist-modify-public'
               }

# work around to use 'current_user_recently_played' since spotipy doesnt support anymore?
# currently don't understand code- check google bookmark
# see similar comment below


def current_user_recently_played(self, limit=50):
    return self._get('me/player/recently-played', limit=limit)


class User:
    def __init__(self, **kwargs):
        self.client_id = kwargs['client_id']
        self.client_secret = kwargs['client_secret']
        self.redirect_uri = kwargs['redirect_uri']
        self.username = kwargs['username']
        self.scope = kwargs['scope']
        self.setup()

    def get_token(self):
        token = util.prompt_for_user_token(self.username,
                                           self.scope,
                                           self.client_id,
                                           self.client_secret,
                                           self.redirect_uri,
                                           )

        return token

    def setup(self):

        token = self.get_token()

        spotify = spotipy.Spotify(auth=token)
        # work around to use 'current_user_recently_played' since spotipy doesnt support anymore?
        # see similar comment above
        spotify.current_user_recently_played = types.MethodType(
            current_user_recently_played, spotify)

        # building class attributes
        self.spotify = spotify

    def get_recently_played_tracks_data(self, limit=50, just_titles=False):
        # Sets up recently_played attribute with json track data OR returns recent track titles
        # we want all recent track data retrieved so limit is not passed to 'current_user_recently_played'
        recent_tracks_data = self.spotify.current_user_recently_played()

        if just_titles:
            recent_tracks_titles = []
            for item in recent_tracks_data['items']:
                recent_tracks_titles.append(item['track']['album']['artists'][0]['name'])

            return recent_tracks_titles[:limit]
        else:
            return recent_tracks_data

    def show_recently_played_tracks(self, limit=50):
        # Prints out recently played track from recently played attribute
        print('\n')
        print("--- {}'s {} Recently Played Tracks ---\n".format(self.username, limit))

        recent_track_titles = self.get_recently_played_tracks_data(limit=limit, just_titles=True)
        for title in recent_track_titles:
            print(title)

    def get_track_ids_from_data(self, track_data):
        # Returns track ids given Spotify API json track_data
        track_ids = [item['track']['id'] for item in track_data['items']]
        return track_ids

    def get_track_ids_from_playlist_with_name(self, playlist_name):
        # Returns track ids from a given playlist name
        playlist_id = self.get_playlist_id(playlist_name)
        track_data = self.spotify.user_playlist_tracks(self.username, playlist_id)
        track_ids = self.get_track_ids_from_data(track_data)

        return track_ids

    def get_playlist_data(self, limit=50, just_titles=False):
        # Sets up value for class playlist attribute OR returns playlist titles
        playlists = self.spotify.user_playlists(self.username)

        if just_titles:
            playlist_titles = []
            for item in playlists['items']:
                playlist_titles.append(item['name'])

            return playlist_titles[:limit]
        else:
            return playlists

    def show_playlists(self, limit=50):
        # Prints playlist titles from playlist attribute
        print('\n')
        print("--- {}'s Playlists (Max. 50) ---\n".format(self.username))

        playlist_titles = self.get_playlist_data(limit=limit, just_titles=True)
        for title in playlist_titles:
            print(title)

    def create_playlist(self, name):
        # Creates a new playlist for the user
        if name not in self.get_playlist_data(just_titles=True):
            self.spotify.user_playlist_create(self.username, name)
            return True

    def get_playlist_id(self, name):
        # change to 'with_name'
        # For not this returns the first playlist witht the matching name
        playlist_data = self.get_playlist_data()
        for item in playlist_data['items']:
            if item['name'] == name:
                return item['id']

    def create_recently_listened_to_playlist(self):
        # Add parameter for track limit
        if self.create_playlist('Recent Tracks'):
            track_data = self.get_recently_played_tracks_data()
            track_ids = self.get_track_ids_from_data(track_data)
            playlist_id = self.get_playlist_id('Recent Tracks')
            self.spotify.user_playlist_add_tracks(self.username, playlist_id, track_ids)

    def get_recently_listened_to_track_ids(self, amount=50, dedupe=True):
        # dedupe takes True or False- returns duplicates if False
        recently_played_data = self.get_recently_played_tracks_data()
        unfiltered_new_track_ids = self.get_track_ids_from_data(recently_played_data)
        filtered_track_ids = list(dict.fromkeys(unfiltered_new_track_ids))

        if dedupe:
            return filtered_track_ids[:amount]
        else:
            return unfiltered_track_ids[:amount]

    def get_id_position_objects_from_playlist_with_name(self, name):
        # return list of id/positions objects used for Spotipy's-
        # user_playlist_remove_specific_occurrences_of_tracks method
        playlist_ids = self.get_track_ids_from_playlist_with_name(name)
        id_objects = [{"uri": id, "positions": [position]}
                      for position, id in enumerate(playlist_ids, 0)]

        return id_objects

    def get_playlist_length_with_name(self, name):
        playlist_len = len(self.get_track_ids_from_playlist_with_name(name))
        return playlist_len

    def remove_tracks_from_playlist_with_name(self, name, location_list):
        # Removes tracks in all locations provided by the location_list
        playlist_id = self.get_playlist_id(name)
        playlist_objects = self.get_id_position_objects_from_playlist_with_name(name)
        tracks_to_remove = []
        for location in location_list:
            tracks_to_remove.append(playlist_objects[location - 1])
        print('\n')
        print("tracks removed:\n{}".format(tracks_to_remove))
        print(len(tracks_to_remove))

        self.spotify.user_playlist_remove_specific_occurrences_of_tracks(
            self.username, playlist_id, tracks_to_remove)

    def add_tracks_to_playlist_with_name(self, playlist_name, new_track_ids, position=0, dedupe=True):
        # dedupe prevents duplicate tracks from being added

        if playlist_name in self.get_playlist_data(just_titles=True):
            playlist_id = self.get_playlist_id(playlist_name)

        if dedupe:
            current_track_ids = self.get_track_ids_from_playlist_with_name(playlist_name)

            filtered_track_ids = []
            for track_id in new_track_ids:
                if track_id not in current_track_ids:
                    filtered_track_ids.append(track_id)

            # Only try to add tracks if there are filtered tracks to add
            if filtered_track_ids:

                self.spotify.user_playlist_add_tracks(
                    self.username, playlist_id, filtered_track_ids, position)

                return True
        else:
            self.spotify.user_playlist_add_tracks(
                self.username, playlist_id, new_track_ids, position)
            return True

    def update_recently_played_tracks_playlist(self, limit_total=True, max_length=50):

        recent_track_ids = self.get_recently_listened_to_track_ids(amount=15)
        playlist_ids = self.get_track_ids_from_playlist_with_name('Recent Tracks')

        filtered_tracks = []
        for id in recent_track_ids:
            if id not in playlist_ids:
                filtered_tracks.append(id)

        print('\n')
        print('filtered tracks')
        print(filtered_tracks)
        print(len(filtered_tracks))

        playlist_len = len(playlist_ids)
        len_list = list(range(1, playlist_len + 1))

        available_playlist_space = max_length - playlist_len
        print('\n')
        print('len_list:')
        print(len_list)

        if len(filtered_tracks) == max_length:
            playlist_id = self.get_playlist_id_with_name('Recent Tracks')
            self.user_playlist_replace_tracks(self.username, playlist_id, recent_track_ids)

        if available_playlist_space < len(filtered_tracks):
            # remove_range = len(filtered_tracks) - available_playlist_space
            remove_range = len(filtered_tracks)
            self.remove_tracks_from_playlist_with_name('Recent Tracks',
                                                       len_list[-remove_range:]
                                                       )

        self.add_tracks_to_playlist_with_name('Recent Tracks', filtered_tracks)

    def main(self):
        self.setup()
        self.show_recently_played_tracks(5)
        self.create_recently_listened_to_playlist()
        # self.update_recently_played_tracks_playlist()


hannah = User(**hannah_info)
hannah.main()


# schedule.every(2).minutes.do(hannah.main)
#
# while True:
#     schedule.run_pending()
