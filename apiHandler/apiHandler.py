import requests, sys, os, random, getopt

## @package apiHandler
#  Provide simple interaction the spotify api

# own
from apiHandler.auth import authorize as auth
from apiHandler.util import log, ui

## Enable debug logging
debug = False

## @class APIErrorCodes
#  Helper for spotify API return codes
class APIErrorCodes:
	ok = 200
	no_content = 204
	bad_request = 400
	expired_access = 401
	permission_missing = 401
	premium_required = 403
	not_found = 404
	too_many = 429

## @class ApiHandler
#  Handle interaction with the spotify API
#
#  Provides a number of public methods for spotify interaction
class ApiHandler:

	## Constructor
	#  @param keyword search term for playlists (optional)
	#
	#  The constructor loads stored credentials, selects a valid user
	#  and requests a keyword is not provided via call parameter. 
	def __init__(self, keyword=None):
		self._log = log.log(self.__class__.__name__, debug)
		self._log.dbg("hello from playlist fetcher")

		self._auth = auth.Auth()
		self._ui = ui.Ui()
		self._user = ""
		self.keyword = keyword


	## Select a valid user for API calls
	#  @return True if user selected, else False
	#
	#  If only one valid user is found, use this one,
	#  otherwise let user choose which id to use.
	def select_user(self):
		user = ""
		ulen = len(self._auth.valid_users())

		if ulen < 1:
			self._log.err("no user credentials found. cannot access spotify api")
			return False
		elif ulen == 1:
			self._log.dbg("one usable user found")
			user = self._auth.valid_users()[0]
		elif ulen > 1:
			self._log.dbg("asking user for user selection")
			q = "Found %d authenticated users:\n%s\n\nEnter username to select:" %(ulen, self._auth.valid_users())
			i = 0; i_max = 3
			while user not in self._auth.valid_users():
				i += 1
				if i > i_max:
					self._log.err("aborting")
					return False
				user = self._ui.get_input(q)
		
		self._user = user
		return True

	
	## Return a playlist url
	#  @return string containing browser-callable playlist url
	#
	# This function does everything, indended ad outfacing api
	def get_playlist(self):

		if self.keyword is None:
			if not self._get_keyword(): 
				self._log.err("no keyword provided")
				return None

		lists = self._fetch_lists()
		if lists is None:
			self._log.err("Couldn't find any playlists with search term: %s" %(self.keyword))
			return None
		else:
			self._log.dbg("Found %d playlists with keyword %s" %(len(lists), self.keyword))

		playlist_url = self._select_playlist(lists)
		return playlist_url


	## Get currently playing song
	#  @return string 'artist - title' or empty string if not currently playing
	def get_current_playing(self):
		active, song = self._get_current()

		if active:
			self._log.log("User is currently playing: %s" %(song))
			return song
		else:
			self._log.log("no music currently playing")
			return ''


	## Toggle playback
	#  In theory, this should toggle the user's playback. Untested, since I dont have a premium spotify account
	def _toggle_playback(self):
		url = "https://api.spotify.com/v1/me/player/play"
		headers = {'Authorization': f"Bearer {self._auth.access_token(str(self._user))}"}

		## @todo: need to put the actual data here.
		#  https://developer.spotify.com/console/put-play/

		response = requests.put(url, headers=headers)
		res = self._check_response(response)
		self._log.dbg_json(res)

		if res.get('error'):
			self._log.log("Recieved an error")
			if res.get('error') == APIErrorCodes.premium_required:
				self._log.log("This action required a premium spotify account, sorry.")
			return None

		return None

	def _get_active_device(self):
		res = None
		url = "https://api.spotify.com/v1/me/player/devices"
		headers = {'Authorization': f"Bearer {self._auth.access_token(str(self._user))}"}

		response = requests.get(url, headers=headers)
		res = self._check_response(response)
		self._log.dbg_json(res)

		if res.get('error'):
			self._log.log("Recieved an error")
			return res

		for device in res.get('devices'):
			if device.is_active:
				res = device.id
				break

		return res
	
	
	## Retrieve currently playing track
	#  @return tuple containing playback status and 'artist - song name' as string
	def _get_current(self):
		ret = (None, None)
		url = "https://api.spotify.com/v1/me/player/currently-playing?additional_types=episode"
		headers = {'Authorization': f"Bearer {self._auth.access_token(str(self._user))}"}

		response = requests.get(url, headers=headers)
		res = self._check_response(response)
		self._log.dbg_json(res)

		if res.get('error'):
			self._log.log("Recieved an error")
			if res.get('error') == APIErrorCodes.no_content:
				self._log.log("no currently playing")
			if res.get('error') == APIErrorCodes.permission_missing:
				if self._auth.authorize(self._user):
					return self.get_current_playing()
				else:
					self._log.err("Could not refresh access token for user %s" %(self._user))
			return ret

		active = res.get('is_playing')
		self._log.dbg("song is %s playing" %("actively" if active else "not"))
		item = res.get('item', None)

		self._log.dbg("listening to:")
		self._log.dbg_json(item)

		if item is not None:
			creator=''
			if item.get('show'):
				creator = item.get('show').get('name')
			elif item.get('artists'):
				creator = item.get('artists')[0].get('name')

			itemstr = "%s - %s" %(creator, item.get('name'))
			self._log.log(itemstr)
			ret = (active, itemstr)
		return ret

	## Check a response from spotify API
	#  @param response as recieved from API call
	#  @return the response object if API call was successful, else an object containing error code
	def _check_response(self, response):
		# preliminary error checking
		res = {'error' : response.status_code}
		self._log.dbg(response)

		if response.status_code == APIErrorCodes.ok:
			res = response.json()
		else:
			self._log.dbg('Failed to receive token: error %d' %(response.status_code))
			if response.status_code == APIErrorCodes.no_content:
				self._log.dbgerr("no content")
			elif response.status_code == APIErrorCodes.not_found:
				self._log.dbgerr("not found")
			elif response.status_code == APIErrorCodes.bad_request:
				self._log.dbgerr("bad request")
			elif response.status_code == APIErrorCodes.permission_missing:
				self._log.dbgerr("permissions missing")

		return res


	## Request keyword from user
	#  @return True if keyword gotten, else False
	def _get_keyword(self):
		keyword = self._ui.get_input("Search term:")
		if keyword is None:
			return False
		
		self.keyword = keyword
		return True


	## Get playlists matching keyword from spotify
	#  @return list of playlists, or None if no playlists found
	def _fetch_lists(self):
		if self.keyword == '':
			self.get_keyword()
		
		url = "https://api.spotify.com/v1/search?q=%s&type=playlist" %(self.keyword)
		headers = {'Authorization': f"Bearer {self._auth.access_token(str(self._user))}"}

		response = requests.get(url, headers=headers)
		res = self._check_response(response)
		self._log.dbg_json(res)

		if res.get('error'):
			self._log.log("Recieved an error")
			if res.get('error') == APIErrorCodes.permission_missing:
				if self._auth.authorize(self._user):
					return self._fetch_lists()
				else:
					self._log.err("Could not refresh access token for user %s" %(self._user))
			return None

		# look for the playlists
		if not res.get('playlists'):
			print("something went wrong")
			return None
		elif not res.get('playlists').get('items') or (len(res.get('playlists').get('items')) == 0) :
			print("no results found")
			return None

		return res.get('playlists').get('items')


	## Suggest random playlists to iser and let them choose
	#  @param playlists list of playlists as returned by fetch_listst
	#  @return playlist url or None if aborted by user
	def _select_playlist(self, playlists):
		# suggestion and selection
		accepted = False
		i = 0
		l = len(playlists)

		while not accepted:
			
			if (i > 0 ) and ((i % 10) == 0):
				if self._ui.question("You did not accept 10 times now, want to abort altogether?"):
					break
			
			i += 1
			idx = int(random.random() * l)
			pl = playlists[idx]
			name = self._fix_pango_markup(pl['name'])
			desc = self._fix_pango_markup("~ "+pl['description']+" ~" if (pl['description'] != "") else "")
			suggestion = "I suggest you listen to <b>%s</b> with %d tracks.\n%s\n\nOkay?" %(name, pl['tracks']['total'], desc)

			if self._ui.question(suggestion):
				accepted = True

		if accepted:
			self._log.dbg("got playlist index %d: %s" %(idx, name))
			self._log.dbg(pl['external_urls']['spotify'])
			return pl['external_urls']['spotify']
		else:
			self._log.err("user aborted")
			return None

	## Replace illegal chars with their escaped counterpart
	def _fix_pango_markup(self, text):
		return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("''", "&#39;")

