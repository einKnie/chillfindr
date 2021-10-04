#!/usr/bin/env python

## @package log
#  Simple logging, specialized for debug logging

import sys, pprint

## @class log.log
#  Provide simple logging functionality
class log:

	## Constructor
	#  @param name module name, will be prepended to all logged strings
	#  @param debug boolean, enable debug logging
	def __init__(self, name='test', debug=False):
		self.debug = debug
		self.name = name

	## Log a given message to stdout
	def log(self, *args, **kwargs):
		print("%s:" %(self.name), end=' ')
		print(*args, **kwargs)

	## Log a given message to stderr
	def err(self, *args, **kwargs):
		print("%s:" %(self.name), end=' ')
		print(*args, file=sys.stderr, **kwargs)

	## Log a given message if debug enabled
	def dbg(self, *args, **kwargs):
		if self.debug:
			print("%s:" %(self.name), end=' ')
			print(*args, **kwargs)

	## Log a given message to stderr if debug enabled
	def dbgerr(self, *args, **kwargs):
		if self.debug:
			print("%s:" %(self.name), file=sys.stderr, end=' ')
			print(*args, file=sys.stderr,**kwargs)

	## Pretty print a json object if debug enabled
	def dbg_json(self, *args, **kwargs):
		if self.debug:
			print("%s:" %(self.name), end=' ')
			pprint.pprint(*args, **kwargs)