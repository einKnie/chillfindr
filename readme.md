# chillfindr

Get spotify playlist suggestions based on given keywords.

_[still in early development]_

## intro

This app suggest several playlists based on one or more keywords provided by the user. On playlist selection, a new firefox window is opened on a special workspace(\*) with the spotify web player.

_\* this is a i3wm-specific setup. To change the executed command, see [here](https://github.com/einKnie/chillfindr/blob/9f42de141f8006538e9c0371f482dabbdd96ba34/chillfindr.py#L82)_


Suggestions as well as query input are implemented using [zenity](https://linux.die.net/man/1/zenity) dialogs.

### Examples

Get suggestions for 'lofi' playlists:
```
chillfindr.py --playlist -q="lofi"
```

Enter query via a dialog box. This works well for keyboard shortcuts:
```
chillfindr.py --playlist
```

Print the currently playing song:
```
chillfindr.py --now
```


### Configuration

#### Prerequisites

This app requires a couple of python modules to be installed:

- [requests](https://pypi.org/project/requests/)
- [zenity](https://pypi.org/project/Zenity/)

#### Account Management

Credentials are stored in a hidden file `.cred` inside the apiHandler/auth/ directory. When no `.cred` file is found, a default file is created.
At least _client\_id_ and _client\_secret_ must be provided by the user.

The one-time setup is a bit tricky, since this is for testing only.
_client\_id_ and _client\_secret_ are obtained by registering the app on your spotify developer account [here](https://developer.spotify.com/dashboard/applications).
This will provide you with a _client\_id_ and _client\_secret_. 
Additionally, you will have to set a _redirect\_uri_ *http://localhost:2112/* in the app's settings there. The remaining process of obtaining the necessary permissions and access tokens is automated. Simply follow the instructions after starting the chillfindr.

**note: This process will be improved.** 