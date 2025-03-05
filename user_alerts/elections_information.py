#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import time
from mypylib.mypylib import get_timestamp
from utils import (
	with_buffer,
	get_adnl_text,
	amount_formatting
)


class ElectionsInformation:
	def __init__(self, local, toncenter, *args, **kwargs):
		self.local = local
		self.toncenter = toncenter
		self.create_time = get_timestamp()
		self.timeoute = 604800 # 7 day
	#end define

	def check(self, user):
		election_data = self.toncenter.get_election_data()
		user_adnl_list = user.get_adnl_list()
		user_participants_list = get_sorted_participants_list(self.local, self.toncenter, user_adnl_list)
		#print("user_adnl_list:", user_adnl_list)
		#print("user_participants_list:", user_participants_list)
		if election_data.finished == False:
			self.check_before_start(election_data, user, user_participants_list)
		else:
			self.check_after_start(election_data, user, user_adnl_list, user_participants_list)
	#end define

	def check_before_start(self, election_data, user, user_participants_list):
		for adnl_addr, participant in user_participants_list.items():
			self.inform_before_start(user, election_data.election_id, participant)
	#end define

	def check_after_start(self, election_data, user, user_adnl_list, user_participants_list):
		problem_adnl_list = list()
		for adnl_addr in user_adnl_list:
			if adnl_addr in user_participants_list:
				continue
			problem_adnl_list.append(adnl_addr)
		if len(problem_adnl_list) == 0:
			return
		self.inform_after_start(user, election_data.election_id, problem_adnl_list)
	#end define

	def inform_before_start(self, user, election_id, participant):
		alert_name = f"{type(self).__name__}-{election_id}-{participant.adnl_addr}"
		triggered_alerts_list = user.get_triggered_alerts_list()
		if alert_name in triggered_alerts_list:
			return
		#end if

		adnl_text = get_adnl_text(user, participant.adnl_addr)
		stake = participant.stake // 10**9
		stake_text = amount_formatting(stake)
		text = f"Validator `{adnl_text}` sent stake: `{stake_text}` TON"
		user.add_message(text)
		triggered_alerts_list[alert_name] = get_timestamp()
	#end define

	def inform_after_start(self, user, election_id, problem_adnl_list):
		alert_name = f"{type(self).__name__}-{election_id}"
		triggered_alerts_list = user.get_triggered_alerts_list()
		if alert_name in triggered_alerts_list:
			return
		#end if

		user_labels = user.get_labels()
		text = f"Validators didn't send stake for round `{election_id}`:" + '\n'
		for adnl_addr in problem_adnl_list:
			adnl_text = get_adnl_text(user, adnl_addr)
			text += f"`{adnl_text}`" + '\n'
		user.add_message(text)
		triggered_alerts_list[alert_name] = get_timestamp()
	#end define
#end class

def get_sorted_participants_list(local, toncenter, adnl_list):
	return with_buffer(local, do_get_sorted_participants_list, toncenter, adnl_list)
#end define

def do_get_sorted_participants_list(toncenter, adnl_list):
	result = dict()
	election_data = toncenter.get_election_data()
	for participant in election_data.participants_list:
		if participant.adnl_addr not in adnl_list:
			continue
		result[participant.adnl_addr] = participant
	return result
#end define
