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
		self.max_list_len = 20
	#end define

	def get_db(self):
		users = get_users_dict_from(self.local.db)
		user_db = users.get(self.id)
		if user_db is None:
			user_db = Dict()
			users[self.id] = user_db
		return user_db
	#end define

	def get_data_from_db(self, name, type=Dict):
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
		return self.get_data_from_db("adnl_list", list)
	#end define

	def get_fullnode_adnl_list(self):
		return self.get_data_from_db("fullnode_adnl_list", list)
	#end define

	def get_labels(self):
		return self.get_data_from_db("labels")
	#end define

	def get_disable_alerts_list(self):
		return self.get_data_from_db("disable_alerts_list", list)
	#end define

	def get_triggered_alerts_list(self):
		return self.get_data_from_db("triggered_alerts_list")
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

	def add_adnl(self, adnl):
		adnl_list = self.get_adnl_list()
		error = self.check_entry_in_list(adnl, adnl_list)
		if error:
			return error
		adnl_list.append(adnl)
		text = f"Ok, ADNL added: _{adnl}_"
		return text
	#end define

	def add_fullnode_adnl(self, fullnode_adnl):
		fullnode_adnl_list = self.get_fullnode_adnl_list()
		error = self.check_entry_in_list(fullnode_adnl, fullnode_adnl_list)
		if error:
			return error
		fullnode_adnl_list.append(fullnode_adnl)
		text = f"Ok, fullnode ADNL added: _{fullnode_adnl}_"
		return text
	#end define

	def add_label(self, adnl, label):
		user_labels = self.get_labels()
		error = self.check_entry_in_list(label, user_labels)
		if error:
			return error
		if label is None:
			return
		if len(label) > 10:
			return
		user_labels[adnl] = label
	#end define

	def enable_alert(self, alert_name):
		if alert_name not in self.local.buffer.possible_alerts_list:
			return "Error, alert not found"
		disable_alerts_list = self.get_disable_alerts_list()
		if alert_name not in disable_alerts_list:
			return f"Error, alert already enabled: _{alert_name}_"
		alert_index = disable_alerts_list.index(alert_name)
		del disable_alerts_list[alert_index]
		text = f"Ok, alert enabled: _{alert_name}_"
		return text
	#end define

	def disable_alert(self, alert_name):
		if alert_name not in self.local.buffer.possible_alerts_list:
			return "Error, alert not found"
		disable_alerts_list = self.get_disable_alerts_list()
		error = self.check_entry_in_list(alert_name, disable_alerts_list)
		if error:
			return error
		disable_alerts_list.append(alert_name)
		text = f"Ok, alert disabled: _{alert_name}_"
		return text
	#end define

	def get_alerts_list(self):
		user_alerts_list = list()
		disable_alerts_list = self.get_disable_alerts_list()
		for alert in self.local.buffer.possible_alerts:
			alert_name = type(alert).__name__
			if alert_name in disable_alerts_list:
				continue
			user_alerts_list.append(alert)
		return user_alerts_list
	#end define

	def check_entry_in_list(self, item, lst):
		if item in lst:
			text = "Element is already on the list."
			return text
		if len(lst) > self.max_list_len:
			text = "The maximum number of elements has been reached."
			return text
	#end define

	def is_admin(self):
		admins = [str(admin) for admin in self.local.buffer.admins]
		if self.id in admins:
			return True
		return False
	#end define

	def delete(self):
		del self.local.db.users[self.id]
	#end define
#end class


def get_users(local):
	users = list()
	for user_id in get_users_dict_from(local.db):
		users.append(User(local, user_id))
	return users
#end define

def get_active_users(local):
	users = dict()
	for user_id, user in local.db.users.items():
		if ((user.adnl_list and len(user.adnl_list) > 0) or
			(user.alerts_list and len(user.alerts_list) > 0)):
			users[user_id] = User(local, user_id)
	return users
#end define

def get_users_dict_from(db_or_buffer):
	return get_dict_from(db_or_buffer, "users")
#end define

def inform_admins(local, text):
	for user_id in local.buffer.admins:
		User(local, user_id).add_message(text)
#end define
