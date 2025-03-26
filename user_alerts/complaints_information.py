#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import time
from mypylib.mypylib import get_timestamp
from utils import (
	collect_template,
	amount_formatting
)


class ComplaintsInformation:
	def __init__(self, local, toncenter, *args, **kwargs):
		self.local = local
		self.toncenter = toncenter
		self.create_time = get_timestamp()
		self.timeoute = 604800 # 7 day
	#end define

	def check(self, user):
		past_validation_cycle = self.toncenter.get_validation_cycle(past=True)
		election_id = past_validation_cycle.cycle_id
		utime_until = past_validation_cycle.cycle_info.utime_until
		if get_timestamp() < utime_until + 900:
			return
		#end if

		complaints_list = self.toncenter.get_complaints_list(election_id)
		complaints = list()
		for complaint in complaints_list:
			if complaint.is_passed != True:
				continue
			complaints.append(complaint)
		complaints.reverse()
		self.inform(user, election_id, utime_until, complaints)
	#end define

	def inform(self, user, election_id, utime_until, complaints):
		alert_name = f"{type(self).__name__}-{election_id}"
		triggered_alerts_list = user.get_triggered_alerts_list()
		if alert_name in triggered_alerts_list:
			return
		#end if

		complaints_text = str()
		for complaint in complaints:
			penalty = complaint.suggested_fine // 10**9
			penalty_text = amount_formatting(penalty)
			validator = self.toncenter.get_validator(complaint.adnl_addr, past=True)
			efficiency = self.toncenter.get_validator_efficiency(complaint.adnl_addr, election_id)
			complaints_text += collect_template(self.local, "complaint", index=validator.index, adnl=complaint.adnl_addr, efficiency=efficiency, penalty=penalty_text)
			complaints_text += '\n'
		if not len(complaints):
			complaints_text += 'No poor performing validators in the round'
		start_time = timestamp2utcdatetime(election_id)
		end_time = timestamp2utcdatetime(utime_until)
		inform_text = collect_template(self.local, "complaints_information", election_id=election_id, start_time=start_time, end_time=end_time, complaints=complaints_text)

		user.add_message(inform_text)
		triggered_alerts_list[alert_name] = get_timestamp()
	#end define
#end class

def timestamp2utcdatetime(timestamp, format="%d.%m.%Y %H:%M:%S"):
	datetime = time.gmtime(timestamp)
	result = time.strftime(format, datetime) + ' UTC'
	return result
#end define
