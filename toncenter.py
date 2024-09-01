#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import json
from utils import try_get_url, with_buffer
from mypylib.mypylib import Dict, get_timestamp


class Toncenter:
	def __init__(self, local):
		self.local = local
	#end define

	def get_validators_list(self):
		result = list()
		toncenter_data = self.get_telemetry()
		validators = self.get_validators()
		for item in validators:
			adnl_addr = item.get("adnl_addr")
			if adnl_addr:
				result.append(adnl_addr)
		print(f"get_validators_list {len(result)}")
		return result
	#end define

	def get_telemetry(self):
		return with_buffer(self.local, self.do_get_telemetry_list)
	#end define

	def get_validation_cycles_list(self):
		return with_buffer(self.local, self.do_get_validation_cycles_list)
	#end define

	def get_validation_cycle(self):
		data = self.get_validation_cycles_list()
		return data[0]
	#end define

	def get_validators(self):
		data = self.get_validation_cycle()
		return data.cycle_info.validators
	#end define

	def get_complaints_list(self):
		return with_buffer(self.local, self.do_get_complaints_list)
	#end define

	def do_get_telemetry_list(self):
		timestamp = get_timestamp()
		url = f"https://telemetry.toncenter.com/getTelemetryData?timestamp_from={timestamp-100}&api_key={self.local.buffer.api_key}"
		text = try_get_url(url)
		data = json.loads(text)
		return parse_dicts_in_list(data)
	#end define

	def do_get_validation_cycles_list(self):
		url = "https://elections.toncenter.com/getValidationCycles"
		text = try_get_url(url)
		data = json.loads(text)
		return parse_dicts_in_list(data)
	#end define

	def do_get_complaints_list(self):
		url = "https://elections.toncenter.com/getComplaints"
		text = try_get_url(url)
		data = json.loads(text)
		return parse_dicts_in_list(data)
	#end define
#end class


def parse_dicts_in_list(lst):
	result = list()
	for item in lst:
		result.append(Dict(item))
	return result
#end define
