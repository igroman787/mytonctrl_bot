#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import os
from mypylib.mypylib import get_timestamp


class TelemetryWarning:
	def __init__(self, local, toncenter, *args, **kwargs):
		self.local = local
		self.toncenter = toncenter
		self.create_time = get_timestamp()
		self.timeoute = 604800 # 7 day
	#end define

	def check(self, user):
		for adnl in user.get_adnl_list():
			node = self.toncenter.get_telemetry(adnl)
			if node is None:
				continue
			self.check_out_of_sync(user, node)
			self.check_cpu(user, node)
			self.check_memory(user, node)
			self.check_network(user, node)
			self.check_disk(user, node)
			self.check_uptime(user, node)
	#end define

	def check_out_of_sync(self, user, node):
		adnl = node.adnl_address
		out_of_sync = node.data.validatorStatus.out_of_sync
		if out_of_sync > 20:
			self.warn("Sync", user, adnl, out_of_sync, "seconds")
		else:
			self.warn("Sync", user, adnl, out_of_sync, "seconds", direct=False)
	#end define

	def check_cpu(self, user, node):
		adnl = node.adnl_address
		cpu_load = node.data.cpuLoad[0]
		cpu_number = node.data.cpuNumber
		if cpu_load > cpu_number - 1:
			self.warn("CPU", user, adnl, cpu_load, cpu_number)
		else:
			self.warn("CPU", user, adnl, cpu_load, cpu_number, direct=False)
	#end define

	def check_memory(self, user, node):
		adnl = node.adnl_address
		memory_usage = node.data.memory.usage
		memory_total = node.data.memory.total
		if memory_usage > memory_total - 10:
			self.warn("Memory", user, adnl, memory_usage, memory_total)
		else:
			self.warn("Memory", user, adnl, memory_usage, memory_total, direct=False)
	#end define

	def check_network(self, user, node):
		adnl = node.adnl_address
		network_load = node.data.netLoad[0]
		if network_load > 500:
			self.warn("Network", user, adnl, network_load, "Mbit/s")
		else:
			self.warn("Network", user, adnl, network_load, "Mbit/s", direct=False)
	#end define

	def check_disk(self, user, node):
		adnl = node.adnl_address
		disk_name = os.path.basename(node.data.validatorDiskName)
		disk_load_percent = node.data.disksLoadPercent[disk_name][0]
		disk_load = node.data.disksLoad[disk_name][0]
		if disk_load_percent > 90:
			self.warn("Disk", user, adnl, disk_load, "MB/s")
		else:
			self.warn("Disk", user, adnl, disk_load, "MB/s", direct=False)
	#end define

	def check_uptime(self, user, node):
		pass
	#end define

	def warn(self, name, user, adnl, *args, direct=True):
		warning_name = f"{type(self).__name__}_{name}"
		triggered_warnings_list = user.get_triggered_warnings_list()
		if (warning_name in triggered_warnings_list) is direct:
			return
		adnl_ending = adnl[58:65]
		status = "overloaded" if direct else "ok"
		text = f"Validator {name} is {status}:" + '\n'
		text += "```" + '\n'
		text += f"ADNL: ...{adnl_ending}" + '\n'
		text += f"{name}: {args[0]} /{args[1]}" + '\n'
		text += "```"
		user.add_message(text)
		if direct is True:
			triggered_warnings_list[warning_name] = self
		else:
			del triggered_warnings_list[warning_name]
	#end define
#end class
