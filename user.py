#!/usr/bin/env python3
# -*- coding: utf_8 -*-

from utils import get_dict_from
from mypylib.mypylib import Dict


class User:
	def __init__(self, local, user_id):
		self.local = local
		self.id = str(user_id)
		self.db = self.get_db()
		self.buffer = self.get_buffer()
	#end define

	def get_db(self):
		users = get_users_dict_from(self.local.db)
		user_db = users.get(self.id)
		if user_db is None:
			user_db = Dict()
			users[self.id] = user_db
		return user_db
	#end define

	def get_data(self, name, type=Dict):
		user_db = self.get_db()
		data = user_db.get(name)
		if data is None:
			data = type()
			user_db[name] = data
		return data
	#end define

	def get_buffer(self):
		users = get_users_dict_from(self.local.buffer)
		user_buffer = users.get(self.id)
		if user_buffer is None:
			user_buffer = Dict()
			users[self.id] = user_buffer
		return user_buffer
	#end define

	def get_data_from_buffer(self, name, type=Dict):
		user_buffer = self.get_buffer()
		data = user_buffer.get(name)
		if data is None:
			data = type()
			user_buffer[name] = data
		return data
	#end define

	def get_adnl_list(self):
		return self.get_data("adnl_list", list)
	#end define

	def get_alarm_list(self):
		return self.get_data("alarm_list", list)
	#end define

	def get_labels(self):
		return self.get_data("labels")
	#end define

	def get_warnings_list(self):
		return self.get_data("warnings_list", list)
	#end define

	def get_triggered_warnings_list(self):
		return self.get_data_from_buffer("triggered_warnings_list")
	#end define

	def get_messages_list(self):
		return self.get_data_from_buffer("messages_list", list)
	#end define

	def add_message(self, text):
		messages_list = self.get_messages_list()
		messages_list.append(text)
	#end define

	def send_messages(self, send_message_func):
		messages_list = self.get_messages_list()
		for i in range(len(messages_list)):
			text = messages_list.pop(0)
			send_message_func(self, text)
	#end define
#end class


def get_users(local):
	users = list()
	for user_id in get_users_dict_from(local.db):
		users.append(User(local, user_id))
	return users
#end define

def get_users_dict_from(db_or_buffer):
	return get_dict_from(db_or_buffer, "users")
#end define


