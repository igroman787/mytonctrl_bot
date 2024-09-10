#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import os
from mypylib.mypylib import get_timestamp


class TelemetryAlert:
	def __init__(self, local, toncenter, *args, **kwargs):
		self.local = local
		self.toncenter = toncenter
		self.create_time = get_timestamp()
		self.timeoute = 604800 # 7 day
	#end define

	def check(self, user):
		for adnl in user.get_adnl_list():
			node = self.toncenter.get_telemetry(user, adnl)
			if node is None:
				continue
			self.try_function(self.check_out_of_sync, user, node)
			self.try_function(self.check_cpu, user, node)
			self.try_function(self.check_memory, user, node)
			self.try_function(self.check_network, user, node)
			self.try_function(self.check_disk, user, node)
			self.try_function(self.check_uptime, user, node)
	#end define

	def try_function(self, func, *args, **kwargs):
		result = None
		try:
			result = func(*args, **kwargs)
		except Exception as err:
			self.local.add_log(f"{func.__name__} error: {err}", "error")
		return result
	#end define

	def check_out_of_sync(self, user, node):
		adnl = node.adnl_address
		out_of_sync = node.data.validatorStatus.out_of_sync
		if out_of_sync > 40:
			self.warn("Sync", user, adnl, out_of_sync, "seconds")
		elif out_of_sync < 20:
			self.warn("Sync", user, adnl, out_of_sync, "seconds", direct=False)
	#end define

	def check_cpu(self, user, node):
		adnl = node.adnl_address
		cpu_load = node.data.cpuLoad[2]
		cpu_number = node.data.cpuNumber
		if cpu_load > cpu_number - 2:
			self.warn("CPU", user, adnl, cpu_load, cpu_number)
		elif cpu_load < cpu_number - 1:
			self.warn("CPU", user, adnl, cpu_load, cpu_number, direct=False)
	#end define

	def check_memory(self, user, node):
		adnl = node.adnl_address
		memory_usage = node.data.memory.usage
		memory_total = node.data.memory.total
		if memory_usage > memory_total - 20:
			self.warn("Memory", user, adnl, memory_usage, memory_total)
		elif memory_usage < memory_total - 10:
			self.warn("Memory", user, adnl, memory_usage, memory_total, direct=False)
	#end define

	def check_network(self, user, node):
		adnl = node.adnl_address
		network_load = node.data.netLoad[2]
		if network_load > 500:
			self.warn("Network", user, adnl, network_load, "Mbit/s")
		elif network_load < 450:
			self.warn("Network", user, adnl, network_load, "Mbit/s", direct=False)
	#end define

	def check_disk(self, user, node):
		adnl = node.adnl_address
		disk_name = os.path.basename(node.data.validatorDiskName)
		if disk_name not in node.data.disksLoad:
			#print(f"{disk_name} not in {list(node.data.disksLoad.keys())}")
			disk_name = list(node.data.disksLoad.keys())[0]
		disk_load = node.data.disksLoad[disk_name][2]
		disk_load_percent = node.data.disksLoadPercent[disk_name][2]
		if disk_load_percent > 80:
			self.warn("Disk", user, adnl, disk_load, "MB/s")
		elif disk_load_percent < 90:
			self.warn("Disk", user, adnl, disk_load, "MB/s", direct=False)
	#end define

	def check_uptime(self, user, node):
		pass
	#end define

	def warn(self, name, user, adnl, *args, direct=True):
		alert_name = f"{type(self).__name__}_{name}_{adnl}"
		triggered_alerts_list = user.get_triggered_alerts_list()
		if (alert_name in triggered_alerts_list) is direct:
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
			triggered_alerts_list[alert_name] = self
		else:
			del triggered_alerts_list[alert_name]
	#end define
#end class
