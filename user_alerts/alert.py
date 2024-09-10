#!/usr/bin/env python3
# -*- coding: utf_8 -*-

from abc import ABC, abstractmethod

class Alert():
	def __init__(self, local, *args, **kwargs):
		self.local = local
	#end define

	@abstractmethod
	def check(self):
		...
	#end define
#end class
