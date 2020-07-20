# ### AutoDeleter ### #
# https://github.com/Jeeaaasus/Tautulli-AutoDeleter
# v1.0
# Initial commit
#
# ### TL;DR ### #
# Tautulli script to automatically remove watched tv.
# I was annoyed that all scripts made for this purpose was made kinda inconvenient, that you have to edit the script file with rating keys and strings of usernames.
# My version is much more convenient to use, after setup, it's configured by only editing shows in Plex.
# It works by using the Collections system Plex has and matching those against Tautulli users, this works with multiple users on the same show.
# No text editing after setup.
# This also has other benefits, one being able to simply search Plex for a username and see all shows that get automatically removed, neatly grouped per user.
# One unfortunate drawback with this, is that Plex forgets about Collections when the show is removed. Which is why AutoDeleter doesn't remove S01E01 episodes.
#
# ### REQUIREMENTS ### #
# Python 3+
# Tautulli and Plex MUST have the exact same paths to media files.
# Collections MUST be named exactly the same as Tautulli 'friendly username' (NOT case-insensitive)
# The setting 'Allow Consecutive Notifications' in Tautulli needed to be on for me, otherwise there was very inconsistent behavior.
#
# ### SETUP ### #
# Add your API key further down.
# If you have locations where you don't want files to be deleted, you can enter those also further down.
# In Tautulli, Add a Script Notification Agent.
# Under Triggers, enable Playback Stop.
# Under Arguments, add these Script Arguments in Playback Stop exactly in this order.
# {title} {rating_key} {grandparent_rating_key} {user} {collections} {file} {progress_percent} {episode_num} {season_num}
#
# ### USAGE ### #
# After setup you shouldn't need to edit this file anymore.
# There are only 2 ways you configure AutoDelete. Plex Collections and Tautulli Friendly Names
# Add whichever tv show you want AutoDeleted to a Plex Collection, with the exact name of the friendly username as the user who watches the show.
# E.g.
# Your Plex user name is Johnny
# Your Tautulli Friendly Name is John
# You want Game of Thrones to be removed after you have watched it.
# In Plex, edit Game of Thrones, under Tags in the field Collections, add one called John.
# Done, AutoDeleter will now remove Game of Thrones episodes after you have watched them.
#
import requests
from sys import argv
from os import path, remove
from time import sleep, time
from glob import glob

# ### USER CONFIGURED VARIABLES ### #
# Your Tautulli URL
tautulli_url = 'http://localhost:8181/'
# Your Tautulli API key
tautulli_apikey = 'YOUR-API-KEY-HERE'
# Full path to folder(s) where you don't want files deleted (e.g. recycle bins)
excluded_paths = ('/fake/path/to/recycle/', '/optional/second/path/')

media_title = argv[1]
episode_ratingkey = argv[2]
grandparent_ratingkey = argv[3]
friendly_username = argv[4]
collections = argv[5].split(', ')
file_location = argv[6]
watched_percent = int(argv[7])
media_episode = int(argv[8])
media_season = int(argv[9])


def get_user_names():
    # this function returns all 'friendly usernames' from tautulli in the form of a list.
    payload = {
        'apikey': tautulli_apikey,
        'cmd': 'get_user_names',
    }

    try:
        r = requests.get(tautulli_url.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        response_data = response['response']['data']
        return [field['friendly_name'] for field in response_data]

    except Exception as error:
        print(f'Tautulli API request failed: {error}.')


def get_history(username, rating_key):
    # This function returns 'True' if the provided 'friendly username' (username) has watched the provided media (rating_key).
    payload = {
        'apikey': tautulli_apikey,
        'cmd': 'get_history',
        'user': username,
        'rating_key': rating_key,
        'start': 0,
        'length': 50
    }

    try:
        r = requests.get(tautulli_url.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        response_data = response['response']['data']['data']
        if [field['watched_status'] for field in response_data if field['watched_status'] == 1]:
            return True

    except Exception as error:
        print(f'Tautulli API request failed: {error}.')


def delete_file():
    # This function deletes the media.
    # Only if, the media file exists & it's not the first episode of the first season & it's not located in any of the paths defined in 'excluded_paths'.
    if path.isfile(file_location) and not (media_episode == 1 and media_season == 1) and not file_location.startswith(excluded_paths):
        # Create a variable 'delete_job_name', using 'episode_ratingkey' to give it a unique name, making it easy to reference later.
        delete_job_name = f'./AutoDeleter_{episode_ratingkey}.txt'
        # Create a file with the name 'delete_job_name', in the same location as this script, write the path of the media file 'file_location' that is going to be deleted to this file and close the file.
        delete_job = open(delete_job_name, 'w'); delete_job.write(f'{file_location}'); delete_job.close()
        # Wait 10 minutes.
        sleep((60 * 10))
        # If the media file 'file_location' still exists.
        if path.isfile(file_location):
            # Delete the media file.
            remove(file_location)
            print(f'Deleted.')
        # If the media file does not exists anymore.
        else:
            print(f'Error: file doesn\'t exist.')
        # Only if, the file 'delete_job_name' exists still.
        if path.isfile(delete_job_name):
            # Delete the file 'delete_job_name'.
            remove(delete_job_name)


def abandoned_delete_files():
    # This function looks for any leftover 'delete_job_name' files created by 'delete_file()' and finishes the removal process.
    # Once per each 'delete_job_name' file.
    for delete_job_name in (glob('./AutoDeleter_*.txt')):
        # Only if, the 'delete_job_name' file was created more than 20 minutes.
        if (time() - path.getctime(delete_job_name)) / 60 > 20:
            # Open the leftover 'delete_job_name' file, save the contents to 'delete_job_target' and close the file.
            delete_job = open(delete_job_name, 'r'); delete_job_target = delete_job.read(); delete_job.close()
            print(f'Found forgotten delete job: \'{delete_job_target}\'\n')
            # If the media file 'delete_job_target' exists.
            if path.isfile(delete_job_target):
                # Delete the media file 'delete_job_target'.
                remove(delete_job_target)
                print(f'Leftover media file deleted.')
            # If the media file does not exists anymore.
            else:
                print(f'Error: Leftover media file doesn\'t exist.')
            # Delete the leftover 'delete_job_name' file.
            remove(delete_job_name)


# Print all arguments from Tautulli.
print(f'AutoDeleter log:\ntitle: {media_title} - S{media_season:02}E{media_episode:02}\nepisode rating key: \'{episode_ratingkey}\'\nseries rating key: \'{grandparent_ratingkey}\'\ncollections: {collections}\nfile path: \'{file_location}\'\nviewer: \'{friendly_username}\'\nwatched: {watched_percent}%\n')


abandoned_delete_files()
# Create a list of users 'watchers' by taking the list of Plex users from 'get_user_names()' and cross-matching it with the {collections} on the media item.
watchers = list(set(collections).intersection(get_user_names()))
# Only if, the user viewing the media item is in the list 'watchers'.
if watchers.__contains__(friendly_username):
    print(f'watchers: {watchers}')
    # If all 'watchers' have watched this media item.
    if all(get_history(user, episode_ratingkey) for user in watchers):
        print(f'All watchers have seen this episode.')
        delete_file()
    # If not all 'watchers' have watched this media item.
    else:
        print(f'Not all watchers have seen this episode.')

exit()
