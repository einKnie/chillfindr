#!/usr/bin/env python

##  @package ui
#   Provide simple user interaction

import zenity
import os
# own
from apiHandler.util import log

## Enable debug logging
debug = False

## @class Ui
#  Helper class for graphical user interaction
class Ui:

	## Constructor
	def __init__(self):
		self._log = log.log(self.__class__.__name__, debug)
		self._log.dbg("hello from ui")

	## Get input from user
	#  @param prompt Input prompt
	#  @return user input or None if user aborted
	def get_input(self, prompt):
		self._log.dbg(prompt)
		ret,entry = zenity.show(zenity.entry, 'width=300', text=prompt)
		return entry if ret else None

	## Ask a yes/no question
	#  @param prompt question string
	#  @return True/False
	def question(self, prompt):
		self._log.dbg(prompt)
		ans,_ = zenity.show(zenity.question, 'width=300', text=prompt)
		return ans

