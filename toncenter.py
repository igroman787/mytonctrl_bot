#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import json
import base64
from utils import try_get_url, with_buffer
from mypylib.mypylib import Dict, get_timestamp


class Toncenter:
	def __init__(self, local):
		self.local = local
	#end define

	def get_validator_efficiency(self, adnl, election_id):
		efficiency_list = self.get_efficiency_list(election_id=election_id)
		for validator in efficiency_list:
			if validator.adnl_addr == adnl:
				efficiency = round(validator.efficiency, 2)
				return efficiency
	#end define

	def get_validator(self, adnl, past=False):
		validators = self.get_validators(past=past)
		for validator in validators:
			if validator.adnl_addr == adnl:
				return validator
	#end define

	def get_validators_list(self):
		result = list()
		validators = self.get_validators()
		for item in validators:
			adnl_addr = item.get("adnl_addr")
			if adnl_addr:
				result.append(adnl_addr)
		return result
	#end define

	def get_nodes_list(self):
		result = list()
		telemetry_list = self.get_telemetry_list()
		for node in telemetry_list:
			if node.adnl_address in result:
				continue
			result.append(node.adnl_address)
		#with open("get_nodes_list.txt", 'wt') as file:
		#	file.write(json.dumps(result, indent=4))
		return result
	#end define

	def get_telemetry(self, user, adnl):
		node = self.do_get_telemetry(adnl)
		if node is None:
			return
		fullnode_adnl = base64.b64decode(node.data.fullnode_adnl).hex().upper()
		if fullnode_adnl in user.get_fullnode_adnl_list():
			return node
	#end define

	def do_get_telemetry(self, adnl):
		telemetry_list = self.get_telemetry_list()
		for node in telemetry_list:
			if node.adnl_address != adnl:
				continue
			return node
	#end define

	def is_send_telemetry(self, adnl):
		node = self.do_get_telemetry(adnl)
		if node:
			return True
		return False
	#end define

	def get_telemetry_list(self):
		return with_buffer(self.local, self.do_get_telemetry_list)
	#end define

	def get_validation_cycles_list(self):
		return with_buffer(self.local, self.do_get_validation_cycles_list)
	#end define

	def get_validation_cycle(self, past=False):
		data = self.get_validation_cycles_list()
		if past:
			return data[1]
		else:
			return data[0]
	#end define

	def get_validators(self, past=False):
		data = self.get_validation_cycle(past=past)
		return data.cycle_info.validators
	#end define

	def get_election_data(self):
		data = self.get_elections_list()
		return data[0]
	#end define

	def get_elections_list(self):
		return with_buffer(self.local, self.do_get_elections_list)
	#end define

	def get_complaints_list(self, election_id):
		return with_buffer(self.local, self.do_get_complaints_list, election_id)
	#end define

	def get_efficiency_list(self, election_id):
		return with_buffer(self.local, self.do_get_efficiency_list, election_id)
	#end define

	def do_get_telemetry_list(self):
		timestamp = get_timestamp()
		url = f"https://telemetry.toncenter.com/getTelemetryData?timestamp_from={timestamp-100}&api_key={self.local.buffer.api_key}"
		#print("do_get_telemetry_list url:", url)
		text = try_get_url(url)
		data = json.loads(text)
		#with open("do_get_telemetry_list.txt", 'wt') as file:
		#	file.write(json.dumps(data, indent=4))
		#with open("do_get_telemetry_list_parse.txt", 'wt') as file:
		#	file.write(json.dumps(parse_dicts_in_list(data), indent=4))
		return parse_dicts_in_list(data)
	#end define

	def do_get_validation_cycles_list(self):
		url = "https://elections.toncenter.com/getValidationCycles?limit=2"
		text = try_get_url(url)
		data = json.loads(text)
		return parse_dicts_in_list(data)
	#end define

	def do_get_elections_list(self):
		url = "https://elections.toncenter.com/getElections"
		text = try_get_url(url)
		data = json.loads(text)
		return parse_dicts_in_list(data)
	#end define

	def do_get_complaints_list(self, election_id):
		url = f"https://elections.toncenter.com/getComplaints?election_id={election_id}&limit=100"
		text = try_get_url(url)
		data = json.loads(text)
		return parse_dicts_in_list(data)
	#end define

	def do_get_efficiency_list(self, election_id):
		url = f"https://toncenter.com/api/qos/cycleScoreboard?cycle_id={election_id}&limit=1000"
		text = try_get_url(url)
		data = json.loads(text)
		return Dict(data).scoreboard
	#end define
#end class


def parse_dicts_in_list(lst):
	result = list()
	for item in lst:
		result.append(Dict(item))
	return result
#end define
