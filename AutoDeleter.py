'''
### AutoDeleter ###
https://github.com/Jeeaaasus/Tautulli-AutoDeleter
v1.4.1
Added exception catching to abandoned_delete_files function.
Small improvements to code workflow.
v1.4.0
New: AutoDeleter will tell Sonarr to rescan library files after deleting a media file.
v1.3.2
Small improvements to code clarity.
v1.3.1
Fixed: a rare race condition by adding a small delay to make sure Tautulli has time to log the viewing before checking watch history on the media.
Small improvements to code clarity.
v1.3.0
New: deletes all media files instead of only the file that was played.
v1.2.0
Fixed: friendly name can be different than username.
Small improvements to the 'get_history' logic.
v1.1.0
Optimized the deletion logic.
Added logging for when an episode was not deleted to make it clear as to why.
Cleaned up some code.
v1.0.0
Initial release.

### TL;DR ###
Tautulli script to automatically remove watched tv.
I was annoyed that all scripts made for this purpose was made kinda inconvenient, that you have to edit the script file with rating keys and strings of usernames.
My version is much more convenient to use, after setup, it's configured by only editing shows in Plex.
It works by using the Collections system Plex has and matching those against Tautulli users, this works with multiple users on the same show.
No text editing after setup.
This also has other benefits, one being able to simply search Plex for a username and see all shows that get automatically removed, neatly grouped per user.
One unfortunate drawback with this, is that Plex forgets about Collections when the show is removed. Which is why AutoDeleter doesn't remove S01E01 episodes.

### REQUIREMENTS ###
Python 3+
Tautulli and Plex must have the EXACT same paths to media files.
Collections must be named EXACTLY the same as Tautulli 'friendly username'. (NOT case-insensitive)
'Allow Playback Stop Notifications Exceeding Watched Percent' neededs to be enabled. (notify_consecutive = 1)

### SETUP ###
Add your API key further down.
If you have locations where you don't want files to be deleted, you can enter those also further down.
In Tautulli, Add a Script Notification Agent.
Under Triggers, enable Playback Stop.
Under Conditions, I suggest doing:
'Library Name' is 'names-of-your-tv-libraries' and 'Progress Percent' is greater than '84'.
Under Arguments, add these Script Arguments in 'Playback Stop' exactly in this order:
{title} {rating_key} {grandparent_rating_key} {user} {collections} {file} {progress_percent} {episode_num} {season_num}

### USAGE ###
After setup you shouldn't need to edit this file anymore.
There are only 2 ways you configure AutoDelete. Plex Collections and Tautulli Friendly Names.
Add whichever tv show you want AutoDeleted to a Plex Collection, with the exact name of the friendly username as the user who watches the show.
E.g.
Your Plex user name is Johnny.
Your Tautulli Friendly Name is John.
You want Game of Thrones to be removed after you have watched it.
In Plex, edit Game of Thrones, under Tags in the field Collections, add one called John.
Done, AutoDeleter will now remove Game of Thrones episodes after you have watched them.
'''
import requests
import json
from sys import argv
from os import path, remove
from time import sleep, time
from glob import glob

# Initialize variables
if __name__ == '__main__':
    # ### USER CONFIGURED VARIABLES ### #
    # Your Tautulli URL
    tautulli_url = 'http://localhost:8181/'
    # Your Tautulli API key
    tautulli_apikey = 'YOUR-TAUTULLI-API-KEY-HERE'
    # Full path to folder(s) where you don't want files deleted (e.g. recycle bins)
    # Leave unedited if you don't want to use this feature
    excluded_paths = ('/example/fake/path/to/recycle/', '/example/optional/second/path/')
    # AutoDeleter will tell Sonarr to rescan library files after deleting a media file.
    # Leave unedited if you don't want to use this feature
    # Your Sonarr URL
    sonarr_url = 'http://localhost:8989/'
    # Your Sonarr API key
    sonarr_apikey = 'YOUR-SONARR-API-KEY-HERE'

    # ### SYSTEM VARIABLES ### #
    api_path = '/api/v2'
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
    '''
    Function returns all 'friendly usernames' from tautulli in the form of a list.
    '''
    payload = {
        'apikey': tautulli_apikey,
        'cmd': 'get_user_names',
    }

    try:
        r = requests.get(tautulli_url.rstrip('/') + api_path, params=payload)
        response = r.json()

        response_data = response['response']['data']
        return [field['friendly_name'] for field in response_data]

    except Exception as error:
        print(f'Tautulli API request failed: {error}.')


def get_history(username, rating_key):
    '''
    Function returns 'True' if the provided 'friendly username' (username) has watched the provided media (rating_key).
    '''
    try:
        for user in (requests.get(tautulli_url.rstrip('/') + api_path, params={'apikey': tautulli_apikey, 'cmd': 'get_user_names'})).json()['response']['data']:
            if user['friendly_name'] == username:
                user_id = user['user_id']

    except Exception as error:
        print(f'Tautulli API request failed: {error}.')

    if user_id is None:
        print(f'Tautulli API request failed: The user "{username}" does not exist.')

    payload = {
        'apikey': tautulli_apikey,
        'cmd': 'get_history',
        'user_id': user_id,
        'rating_key': rating_key,
        'length': 100,
    }

    try:
        r = requests.get(tautulli_url.rstrip('/') + api_path, params=payload)
        response = r.json()

        response_data = response['response']['data']['data']
        if any([field['watched_status'] for field in response_data if field['watched_status'] == 1]):
            return True
        else:
            return False

    except Exception as error:
        print(f'Tautulli API request failed: {error}.')


def get_media_paths(rating_key):
    '''
    Function returns all the file paths of the provided media (rating_key).
    '''
    payload = {
        'apikey': tautulli_apikey,
        'cmd': 'get_metadata',
        'rating_key': rating_key,
    }

    try:
        r = requests.get(tautulli_url.rstrip('/') + api_path, params=payload)
        response = r.json()

        response_data = response['response']['data']['media_info']
        list = []
        for field in response_data:
            list.append(field['parts'][0]['file'])
        return list

    except Exception as error:
        print(f'Tautulli API request failed: {error}.')


def sonarr_command(command):
    '''
    Function posts a request to Sonarr to execute a command.
    '''
    try:
        requests.post(sonarr_url.rstrip('/') + '/api/command', headers={'X-Api-Key': sonarr_apikey}, data=json.dumps({'name': command}))

    except Exception as error:
        print(f'Sonarr API request failed: {error}.')


def delete_file(media_path):
    '''
    Function deletes the media.
    '''
    # Only if, the media file exists.
    if path.isfile(media_path):
        # If the media file 'media_path' still exists.
        if path.isfile(media_path):
            # Delete the media file.
            remove(media_path)
            # If Sonarr is configured.
            if sonarr_apikey != 'YOUR-SONARR-API-KEY-HERE':
                # Tell Sonarr to rescan library files.
                sonarr_command('RescanSeries')
            print(f'One media file deleted.')
        # If the media file does not exists anymore.
        else:
            print(f'Error: file doesn\'t exist.')
        # Only if, the file 'delete_job_name' exists still.
        if path.isfile(delete_job_name):
            # Delete the file 'delete_job_name'.
            remove(delete_job_name)


def create_delete_file(media_path):
    '''
    Function creates a delete job file for the media.
    '''
    # Only if, the media file exists.
    if path.isfile(media_path):
        # Create a variable 'delete_job_name', using 'episode_ratingkey' to give it a unique name, making it easy to reference later.
        global delete_job_name
        delete_job_name = f'./AutoDeleter_{episode_ratingkey}.txt'
        # If the file name already exists, find one that does not exist.
        while True:
            if not path.isfile(delete_job_name):
                break
            n = + 1
            delete_job_name = f'./AutoDeleter_{episode_ratingkey}_{n}.txt'
        # Create a file with the name 'delete_job_name', in the same location as this script, write the path of the media file 'media_path' that is going to be deleted to this file and close the file.
        delete_job = open(delete_job_name, 'w'); delete_job.write(f'{media_path}'); delete_job.close()


def abandoned_delete_files():
    '''
    Function looks for any leftover 'delete_job_name' files created by the 'delete_file()' function and finishes the removal process.
    '''
    # Once per each 'delete_job_name' file.
    for delete_job_name in (glob('./AutoDeleter_*.txt')):
        try:
            # Only if, the 'delete_job_name' file was created more than 20 minutes ago.
            if (time() - path.getctime(delete_job_name)) / 60 > 20:
                # Open the leftover 'delete_job_name' file, save the contents to 'delete_job_target' and close the file.
                delete_job = open(delete_job_name, 'r'); delete_job_target = delete_job.read(); delete_job.close()
                print(f'Found forgotten delete job: \'{delete_job_target}\'\n')
                # If the media file 'delete_job_target' exists.
                if path.isfile(delete_job_target):
                    # Delete the media file 'delete_job_target'.
                    remove(delete_job_target)
                    # If Sonarr is configured.
                    if sonarr_apikey != 'YOUR-SONARR-API-KEY-HERE':
                        # Tell Sonarr to rescan library files.
                        sonarr_command('RescanSeries')
                    print(f'Leftover media file deleted.')
                # If the media file does not exists anymore.
                else:
                    print(f'Error: Leftover media file doesn\'t exist.')
                # Delete the leftover 'delete_job_name' file.
                remove(delete_job_name)
        except Exception as error:
            print(f'Something went wrong when processing an abandoned delete file. Exception: {error}')


# Start
if __name__ == '__main__':
    # Print all arguments given to AutoDeleter from Tautulli.
    print(
        f'AutoDeleter log:\n'
        f'title: {media_title} - S{media_season:02}E{media_episode:02}\n'
        f'episode rating key: \'{episode_ratingkey}\'\n'
        f'series rating key: \'{grandparent_ratingkey}\'\n'
        f'collections: {collections}\n'
        f'file path: \'{file_location}\'\n'
        f'viewer: \'{friendly_username}\'\n'
        f'watched: {watched_percent}%\n'
    )

    # Only if, the user watching is in the list of Collections on the episode & it's not the first episode of the first season.
    if friendly_username in collections and not (media_episode == 1 and media_season == 1):
        # Create a list of users 'watchers' by taking the list of Plex users from 'get_user_names()' and cross-matching it with the {collections} on the episode.
        watchers = list(set(collections).intersection(get_user_names()))
        print(f'watchers: {watchers}')
        # Small delay to make sure Tautulli has time to log the viewing.
        sleep(10)
        # If all 'watchers' have watched this episode.
        if all(get_history(user, episode_ratingkey) for user in watchers):
            print(f'All watchers have seen this episode.')
            # For every media file.
            for media_path in get_media_paths(episode_ratingkey):
                # If the media file is not located in any of the paths defined in 'excluded_paths'
                if not media_path.startswith(excluded_paths):
                    # Create delete job file
                    create_delete_file(media_path)
                    # Wait 10 minutes.
                    sleep((60 * 10))
                    # Delete media file
                    delete_file(media_path)
                else:
                    print(f'One media file not deleted because it is located within an excluded path.')
        # If not all 'watchers' have watched this episode.
        else:
            print(f'Deleted nothing.')
            print(f'Not all watchers have seen this episode.')
    else:
        # Print relevant information why the episode is not being deleted.
        print(f'Deleted nothing.')
        if friendly_username not in collections:
            print(f'The user watching is not in the list of Collections on this episode.')
        if media_episode == 1 and media_season == 1:
            print(f'This is the first episode of the first season.')

    # Delete leftover delete job files
    abandoned_delete_files()

    exit()

