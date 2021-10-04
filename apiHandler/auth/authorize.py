#!/usr/bin/env python

## @package authorize
#  Handle Spotify API authorisation
#
#  The module contains two classes, but only 
#  \a Auth is designed for outside use.


import requests, json, os
from apiHandler.util import log, ui

## Enable debug logging
debug = True

## @class Creds
#  Handle credential storage
#
#  The \a Creds class is a helper class of \a Auth.  
#  It handles the storage and retrieval of credentials on disk.
#  If no existing credential storage file is found,
#  an empty file is created for the user to fill with their data.
class Creds:

	## Constructor
	#  @param file credential storage file location
	def __init__(self, file):
		self._log = log.log(self.__class__.__name__, debug)
		self._log.dbg("hello from credential")
		self._data = None
		self._credfile = file
		self._init()
		self._print()


	## Parse credentials file
	#  @param file credentials file path (optional)
	#  @return credentials from file in json format
	def _parse(self, file=None):
		file = self._credfile if file is None else file
		dat = {}
		with open(file, 'r') as f:
			dat = json.load(f)
		return dat

	## Store active credentials to file
	def _print(self):
		if os.path.isfile(self._credfile):
			os.rename(self._credfile, "%s.bak" %(self._credfile))
		with open(self._credfile, 'w') as f:
			f.write(json.dumps(self._data, indent=2))

	## Initialize credential storage
	#
	#  Load credentials from file if one exists,
	#  or initlialize empty set of credentials
	def _init(self):
		if self._data is not None:
			return self._data
		
		data = {}
		if os.path.isfile(self._credfile):
			data = self._parse(self._credfile)
		else:
			data['urls'] = {
				'auth_url': 'https://accounts.spotify.com/authorize',
				'token_url': 'https://accounts.spotify.com/api/token'
			}
			data['auth'] = {}
			data['auth']['none'] = {
				'client_id': '',
				'client_secret': '',
				'code': '',
				'auth_token': '',
				'refresh_token': ''
			}

		self._data = data
	

	## Print current state of credential storage
	def show(self):
		self._log.dbg(json.dumps(self._data, indent=2))


	## Return list of users in credential storage
	#  @return list of all user ids
	def users(self):
		return list(self._data['auth'].keys())


	## Get/Set a user's access token
	#  @param user user id
	#  @param data new value (optional)
	#  @return current/new value
	#
	# This method acts as a getter if no \a data is provided.
	def access_token(self, user, data=None):
		if data is not None:
			self._data['auth'][user]['auth_token'] = data
			self._print()
		return self._data['auth'][user]['auth_token']


	## Get/Set a user's refresh token
	#  @param user user id
	#  @param data new value (optional)
	#  @return current/new value
	#
	# This method acts as a getter if no \a data is provided.
	def refresh_token(self, user, data=None):
		if data is not None:
			self._data['auth'][user]['refresh_token'] = data
			self._print()
		return self._data['auth'][user]['refresh_token']


	## Get/Set a user's access code
	#  @param user user id
	#  @param data new value (optional)
	#  @return current/new value
	#
	# This method acts as a getter if no \a data is provided.
	def code(self, user, data=None):
		if data is not None:
			self._data['auth'][user]['code'] = data
			self._print()
		return self._data['auth'][user]['code']


	## Get/Set a user's client id
	#  @param user user id
	#  @param data new value (optional)
	#  @return current/new value
	#
	# This method acts as a getter if no \a data is provided.
	def client_id(self, user, data=None):
		if data is not None:
			self._data['auth'][user]['client_id'] = data
			self._print()
		return self._data['auth'][user]['client_id']


	## Get/Set a user's client secret
	#  @param user user id
	#  @param data new value (optional)
	#  @return current/new value
	#
	# This method acts as a getter if no \a data is provided.
	def client_secret(self, user, data=None):
		if data is not None:
			self._data['auth'][user]['client_secret'] = data
			self._print()
		return self._data['auth'][user]['client_secret']



## @class Auth
#  Handle Spotify API credentials
class Auth:

	## Constructor
	#  @param file credential file path [default: script location]
	#
	#  Any stored credentials are read, updated and sorted into lists.
	def __init__(self, file=None):
		self._log = log.log(self.__class__.__name__, debug)
		self._log.dbg("hello from Auth")

		self._file = "%s/.cred" %(os.path.split(os.path.realpath(__file__))[0]) if file is None else file
		self._log.dbg("using credentials file: %s" %(self._file))

		self._ui = ui.Ui()
		self._creds = Creds(self._file)
		self._users = {}
		self._users['unauthorized'] = []
		self._users['authorized'] = []
		self._users['all'] = []
		if self._check_data() == 0:
			self._log.err("No usable credentials found")
		self._update_users()


	## Get user ids from credential storage
	#  @return number of valid users found
	#
	#  @note This function updates the self._users dataset 
	def _check_data(self):
		self._log.dbg("checking available data")
		valid_users = 0
		for user in self._creds.users():
			if self._creds.client_id(user) == '' or self._creds.client_secret(user) == '':
				self._log.err("user %s: not enough data for authentication" %(user))
				self._log.err("please enter at least client_id and client_secret in the credentials file")
				continue
			valid_users += 1
			self._users['all'].append(user)
		return valid_users


	## Update the users datatset 
	#  @return number of valid users found
	#
	# Sort users into authorized and unauthorized (i.e. unusable) users.  
	# This checks if the stored credentials can make an API requests,
	# if not, authentication is attempted 3 times or until success.  
	# Users are then sorted into valid and invalid accounts.
	#  @note This function updates the self._users dataset 
	def _update_users(self):
		self._log.dbg("updating user status")
		for user in self._users['all']:
				status = self.authorize(user)
				if status:
					self._users['authorized'].append(user)
				else:
					self._users['unauthorized'].append(user)
				desc = "%s: %s" %(user, 'valid' if status else 'invalid')
				self._log.dbg(desc)


	## Check if user is authorized
	#  @param user id
	#  @return True if user credentials are authorized, else False
	def _is_authorized(self, user):
		""" Return True is the user has valid credentials, else False """
		if self._creds.access_token(user) != '':
			# check if token is valid
			url = "https://api.spotify.com/v1/search?q=lofi&type=playlist"
			headers = {'Authorization': f"Bearer {self._creds.access_token(user)}"}

			response = requests.get(url, headers=headers)
			res = response.json()

			if res.get('error'):
				self._log.err("we encountered an error: %s" % (res.get('error').get('message')))
				self._log.dbg("user %s: error %s" %(user, res))
			else:		
				self._log.dbg("user %s has valid access token" %(user))
				return True
		return False

	
	## Login with user credentials to gain a temporary access code
	#  @param user user id
	#  @return True on success, False on failure
	#
	# This method requests a non-refreshable access code from user's a\ client_id and \a client_secret
	def _get_access_token_oneshot(self, user):
		payload = {
			'grant_type': 'client_credentials',
			'client_id' : self._creds.client_id(user),
			'client_secret' : self._creds.client_secret(user)
		}

		res = requests.post('https://accounts.spotify.com/api/token', auth=(self._creds.client_id(user), self._creds.client_secret(user)), data=payload)
		res_data = res.json()

		if res_data.get('error') or res.status_code != 200:
			self._log.dbg('Failed to receive token: %s' %(res_data.get('error', 'No error information received.')))
			return False

		json.dumps(res_data, indent=2)
		self._creds.access_token(user, data=res_data.get('access_token'))
		self._creds.refresh_token(user, data='')
		return True


	## Direct the user to grant access and paste resulting code
	#  @param user the user's id
	#  @return True if authorisation using the new access code was successful, else False
	def _get_access_code(self, user):
		redirect = "http://localhost:2112/"
		scope = "user-modify-playback-state%20user-read-playback-state%20user-read-currently-playing"
		auth_url = "https://accounts.spotify.com/authorize?client_id=%s&amp;response_type=code&amp;redirect_uri=%s&amp;scope=%s" %(self.client_id(user), redirect, scope)
		req = "Please click <a href='%s'>this link</a> to give the required permissions to use this program.  \nWhen you're done, lick ok here and copy the part after data= into the next field:" %(auth_url)
		
		if not self._ui.question(req):
			return False
		
		code = self._ui.get_input("enter the url part after 'data='")
		if code is None:
			return False

		if self._creds.code(user, data=code) != code:
			self._log.err("failed to update access code")
			return False
		
		return self.authorize(user)

	
	## Get API access and refresh tokens using user's stored credentials
	#  @param user id
	#  @return True if API tokens were granted, else False
	#
	#  @note This requires the fields client_id, client_secret, and code to be set in credentials file
	def _get_access_tokens(self, user):
		""" Get access and refresh token from a users id, secret, and access code """
		payload = {
			'grant_type': 'authorization_code',
			'code': self._creds.code(user),
			'redirect_uri': 'http://localhost:2112/',
		}

		res = requests.post('https://accounts.spotify.com/api/token', auth=(self._creds.client_id(user), self._creds.client_secret(user)), data=payload)
		res_data = res.json()

		if res_data.get('error') or res.status_code != 200:
			self._log.dbg('Failed to receive token: %s' %(res_data.get('error', 'No error information received.')))
			return False

		self._creds.access_token(user, data=res_data.get('access_token'))
		self._creds.refresh_token(user, data=res_data.get('refresh_token'))
		return True


	## Refresh user's access token
	#  @param user id
	#  @return True if API token could be refreshed, else False
	#
	#  Get updated API access token using user's stored refresh token.  
	#  @note This requires the fields  client_id, client_secret, and refresh_token to be set in credentials file
	def _refresh_access_tokens(self, user):
		""" Refresh access token of an authorized user """
		payload = {
			'grant_type': 'refresh_token',
			'refresh_token': self._creds.refresh_token(user)
		}

		res = requests.post('https://accounts.spotify.com/api/token', auth=(self._creds.client_id(user), self._creds.client_secret(user)), data=payload)
		res_data = res.json()

		if res_data.get('error') or res.status_code != 200:
			self._log.dbg('Failed to refresh token: %s' %(res_data.get('error', 'No error information received.')))
			return False

		json.dumps(res_data, indent=2)
		self._creds.access_token(user, data=res_data.get('access_token'))
		return True
		
	# PUBLIC

	## Print all known users' ids, authorized or not
	def users(self):
		print(self._users)


	## Return list of authorized users' ids
	#  @return list of usable user ids
	def valid_users(self):
		return self._users['authorized']


	## Get user's client id
	#  @param user id
	#  @return user's client_id
	def client_id(self, user):
		return self._creds.client_id(user)


	## Get user's client secret
	#  @param user id
	#  @return user's client_secret
	def client_secret(self, user):
		return self._creds.client_secret(user)

	## Get user's access token
	#  @param user id
	#  @return user's auth_token
	def access_token(self, user):
		return self._creds.access_token(user)

	## Try to authorize a user from stored credentials
	#  @param user user id
	#  @return True if user is authorized, else False
	#
	#  Try to get valid authentication for a user id
	#  up to three times until giving up.  
	#  @note The minimum requirements for authentication are 
	#  client_id and client_secret.
	def authorize(self, user):
		self._log.dbg("authorizing with available data")
		ret = True
		i = 0; i_max = 3

		while not self._is_authorized(user):
			i += 1
			if i > i_max:
				self._log.dbg("aborting")
				ret = False
				break
			
			self._log.dbg("try %d/%d" %(i, i_max))

			if self._creds.code(user) == '':
				# if we have no code, get it before moving on to access token
				if not self._get_access_code(user):
					self._log.dbg("Failed to get access code, sorry.")
				else:
					self._log.log("access code aquired")

			if self._creds.access_token(user) == '':
				# fetch access && refresh tokens with code
				if not self._get_access_tokens(user):
					self._log.dbg("could not get access token, sorry.")
				else:
					self._log.log("access token aquired")
			elif self._creds.refresh_token(user) == '':
				# when we have an access token, but no refresh token, this is a oneshot configuration
				if not self._get_access_token_oneshot(user):
					self._log.dbg("could not get oneshot token, sorry.")
				else:
					self._log.log("oneshot sccess token aquired")
			else:
				# if we have access token && refresh token, but no authorisation,
				# we need to refresh the access token
				if not self._refresh_access_tokens(user):
					self._log.dbg("could not refresh access token, sorry.")
				else:
					self._log.log("access token refreshed")

		return ret

