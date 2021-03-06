import spotipy
import pprint
import types
import schedule
import time
import json
from spotipy import util


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
        self.database_location = '../user_database.json'

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

    def create_recently_listened_to_playlist(self, playlist_name='Recent Tracks', from_friend=None):
        if from_friend:
            track_ids = self.get_user_track_data(from_friend)
            if self.create_playlist(playlist_name):
                self.add_tracks_to_playlist_with_name(playlist_name, track_ids, dedupe=True)
        else:
            if self.create_playlist(playlist_name):
                track_data = self.get_recently_played_tracks_data()
                track_ids = self.get_track_ids_from_data(track_data)
                playlist_id = self.get_playlist_id(playlist_name)
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
        print("{} tracks removed\n".format(len(tracks_to_remove)))

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

    def update_playlist_with_recent_tracks(self, playlist_name, from_friend=None, amount=15, max_length=50):
        if playlist_name in self.get_playlist_data(just_titles=True):
            if from_friend:
                recent_track_ids = self.get_user_track_data(from_friend)[:amount]
            else:
                recent_track_ids = self.get_recently_listened_to_track_ids(amount=amount)

            current_ids = self.get_track_ids_from_playlist_with_name(playlist_name)

            filtered_tracks = []
            for id in recent_track_ids:
                if id not in current_ids:
                    filtered_tracks.append(id)

            playlist_len = len(current_ids)
            len_list = list(range(1, playlist_len + 1))

            available_playlist_space = max_length - playlist_len

            print("Playlist Name: {}".format(playlist_name))
            print("Filtered_tracks: {}\n".format(filtered_tracks))
            print("Available playlist space: {}".format(available_playlist_space))
            print("Playlist length: {}".format(playlist_len))

            if len(filtered_tracks) == max_length or playlist_len > max_length:
                playlist_id = self.get_playlist_id(playlist_name)
                self.spotify.user_playlist_replace_tracks(
                    self.username, playlist_id, recent_track_ids)

            if available_playlist_space < len(filtered_tracks):
                remove_range = len(filtered_tracks)
                self.remove_tracks_from_playlist_with_name(playlist_name,
                                                           len_list[-remove_range:]
                                                           )

            self.add_tracks_to_playlist_with_name(playlist_name, filtered_tracks)
            print("Tracks added: {}".format(filtered_tracks))
            print("{} tracks added".format(len(filtered_tracks)))
            print("**************************************")
        else:
            print("Playlist {} not found".format(playlist_name))
    ############################- Data Sharing -#############################################

    def get_data_from_database(self):
        with open(self.database_location, 'r') as database:
            data = json.load(database)

        return data

    def share_data(self, new_data, type, user):
        data = self.get_data_from_database()
        if type in data[user].keys():
            data[user][type] = new_data
            with open(self.database_location, 'w') as database:
                new_data = json.dumps(data, indent=8)
                database.write(new_data)

    def share_recent_track_ids(self, user):
        track_ids = self.get_recently_listened_to_track_ids()
        self.share_data(track_ids, 'track_data', user)

    def get_user_data(self, user, type):
        data = self.get_data_from_database()
        if type in data[user].keys():
            return data[user][type]

    def get_user_track_data(self, user):
        # This currently returns track id's check database.json
        track_data = self.get_user_data(user, 'track_data')
        return track_data

    def get_user_playlist_data(self, user):
        playlist_data = self.get_user_data(user, 'playlist_data')
        return playlist_data
