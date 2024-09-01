#!/usr/bin/env python3
# -*- coding: utf_8 -*-

from mypylib.mypylib import get_timestamp


class ComplaintsWarning:
	def __init__(self, local, toncenter, *args, **kwargs):
		self.local = local
		self.toncenter = toncenter
		self.create_time = get_timestamp()
		self.timeoute = 604800 # 7 day
	#end define

	def check(self, user):
		validation_cycle = self.toncenter.get_validation_cycle()
		complaints_list = self.toncenter.get_complaints_list()
		for complaint in complaints_list:
			if complaint.election_id != validation_cycle.cycle_id:
				continue
			if complaint.is_passed != True:
				continue
			if complaint.adnl_addr in user.get_adnl_list():
				self.warn(user, complaint)
	#end define

	def warn(self, user, complaint):
		warning_name = f"{type(self).__name__}-{complaint.election_id}"
		triggered_warnings_list = user.get_triggered_warnings_list()
		if warning_name in triggered_warnings_list:
			return
		adnl_ending = complaint.adnl_addr[58:65]
		warning_text = "The validator has been fined:" + '\n'
		warning_text += "```" + '\n'
		warning_text += f"ADNL: ...{adnl_ending}" + '\n'
		warning_text += f"election: {complaint.election_id}" + '\n'
		warning_text += f"fine: {complaint.suggested_fine/10**9} TON" + '\n'
		warning_text += "```"
		user.add_message(warning_text)
		triggered_warnings_list[warning_name] = self
	#end define
#end class
