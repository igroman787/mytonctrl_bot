#!/usr/bin/env python3
# -*- coding: utf_8 -*-

from mypylib.mypylib import get_timestamp


class ComplaintsAlert:
	def __init__(self, local, toncenter, *args, **kwargs):
		self.local = local
		self.toncenter = toncenter
		self.create_time = get_timestamp()
		self.timeoute = 604800 # 7 day
	#end define

	def check(self, user):
		past_validation_cycle = self.toncenter.get_validation_cycle(past=True)
		complaints_list = self.toncenter.get_complaints_list(past_validation_cycle.cycle_id)
		for complaint in complaints_list:
			if complaint.is_passed != True:
				continue
			if complaint.adnl_addr in user.get_adnl_list():
				self.warn(user, complaint)
	#end define

	def warn(self, user, complaint):
		alert_name = f"{type(self).__name__}-{complaint.election_id}"
		triggered_alerts_list = user.get_triggered_alerts_list()
		if alert_name in triggered_alerts_list:
			return
		adnl_ending = complaint.adnl_addr[58:65]
		alert_text = "The validator has been fined:" + '\n'
		alert_text += "```" + '\n'
		alert_text += f"ADNL: ...{adnl_ending}" + '\n'
		alert_text += f"election: {complaint.election_id}" + '\n'
		alert_text += f"fine: {complaint.suggested_fine//10**9} TON" + '\n'
		alert_text += "```"
		user.add_message(alert_text)
		triggered_alerts_list[alert_name] = self
	#end define
#end class
