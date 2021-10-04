#!/usr/bin/env python

## @package chillfindr
#  Provide simple interaction the spotify api
#
#  Mainly parameter parsing and final presentation of the result

import os, sys, getopt
from apiHandler.test.test_reqs import TestRequirements

"""
MAIN
"""

ws_name = ""
helptext = """
Usage:
 > chillfindr.py --now|--playlist [--query=<search term> -h]

 # operations
 -n | --now           ... show currently playing track
 -p | --playlist      ... get playlist suggestions

 # modifiers
 -q <s> | --query=<s> ... set playlist search term [optional]

 # misc
 -h                   ... show this help

 Note: Choose exactly one operation.

"""

if __name__ == '__main__':

	tr = TestRequirements()
	tr.test_requirements()

	from apiHandler import apiHandler

	print(sys.argv)

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hnpq:', ['now', 'playlist', 'query=', 'help'])
	except getopt.GetoptError:
		print(helptext)
		exit(1)

	current = False
	playlist = False
	term = None

	for opt,arg in opts:
		if opt in ('-h', '--help'):
			print(helptext)
			exit(0)
		elif opt in ('-n', '--now'):
			current = True
		elif opt in ('-p', '--playlist'):
			playlist = True
		elif opt in ('-q', '--query'):
			term = arg

	if current == playlist:
		print("select exactly one operation at a time")
		print(helptext)
		exit(1)

	fetcher = apiHandler.ApiHandler(term)
	if not fetcher.select_user():
		print("no usable user config found, sorry.")
		exit(1)
	
	if current:
		print("currently listening to: %s" %(fetcher.get_current_playing()))
	elif playlist:
		link = fetcher.get_playlist()
		if link is None:
			print("no playlist selected")
			exit(0)
		print(link)
		syscall = "i3-msg 'workspace %s; exec firefox --new-window %s;'" %(ws_name, link)
		os.system(syscall)

	exit(0)
