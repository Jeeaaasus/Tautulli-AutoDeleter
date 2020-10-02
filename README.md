# **Tautulli-AutoDeleter**

### TL;DR
Tautulli script to automatically remove watched tv.

I was annoyed that all scripts made for this purpose was made kinda inconvenient, that you have to edit the script file with rating keys and strings of usernames.

My version is much more convenient to use, after setup, it's configured by only editing shows in Plex, no text editing after setup.

It works by using the Collections system Plex has and matching those against Tautulli users, this works with multiple users on the same show.

This also has other benefits, one being able to simply search Plex for a username and see all shows that get automatically removed, neatly grouped per user.

One unfortunate drawback with this, is that Plex forgets about Collections when the show is removed. Which is why AutoDeleter doesn't remove S01E01 episodes.


# REQUIREMENTS
Python 3+

Tautulli and Plex MUST have the exact same paths to media files.

Collections MUST be named exactly the same as Tautulli 'friendly username' (NOT case-insensitive).

The setting 'Allow Consecutive Notifications' in Tautulli needed to be on for me, otherwise there was very inconsistent behavior.


# SETUP
Add your API key to the script.

If you have locations where you don't want files to be deleted, you can enter those also.

In Tautulli, Add a Script Notification Agent.

Under Triggers, enable Playback Stop.

Under Conditions, I suggest doing:

'Library Name' is 'names-of-your-tv-libraries' and 'Progress Percent' is greater than '84'.

Under Arguments, add these Script Arguments in Playback Stop, exactly in this order:

{title} {rating_key} {grandparent_rating_key} {user} {collections} {file} {progress_percent} {episode_num} {season_num}


# USAGE
There are only 2 ways you configure AutoDelete. Plex Collections and Tautulli Friendly Names.

Add whichever tv show you want AutoDeleted to a Plex Collection, with the exact name of the friendly username as the user who watches the show.

E.g.

Your Plex user name is Johnny.

Your Tautulli Friendly Name is John.

You want Game of Thrones to be removed after you have watched it.

In Plex, edit Game of Thrones, under Tags in the field Collections, add one called John.

AutoDeleter will now remove Game of Thrones episodes after you have watched them.
 
