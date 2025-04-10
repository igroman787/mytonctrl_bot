#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import os
from mypylib.mypylib import get_timestamp
from utils import get_adnl_text, collect_template


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
			self.try_function(self.check_sync, user, node)
			self.try_function(self.check_cpu, user, node)
			self.try_function(self.check_ram, user, node)
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

	def check_sync(self, user, node):
		adnl = node.adnl_address
		out_of_sync = node.data.validatorStatus.out_of_sync
		#if out_of_sync > 40:
		#	self.warn("Sync", user, adnl, out_of_sync, "seconds")
		#elif out_of_sync < 20:
		#	self.warn("Sync", user, adnl, out_of_sync, "seconds", overloaded=False)
		self.check_with_threshold(user, alert_name="Sync", adnl=adnl, value_for_comparison=out_of_sync, 
			upper_threshold=40, lower_threshold=20, value=out_of_sync)
	#end define

	def check_cpu(self, user, node):
		adnl = node.adnl_address
		cpu_load = node.data.cpuLoad[2]
		cpu_number = node.data.cpuNumber
		#if cpu_load > cpu_number - 2:
		#	self.warn("CPU", user, adnl, cpu_load, cpu_number)
		#elif cpu_load < cpu_number - 1:
		#	self.warn("CPU", user, adnl, cpu_load, cpu_number, overloaded=False)
		value_percent = round(cpu_load/cpu_number*100, 2)
		self.check_with_threshold(user, alert_name="CPU", adnl=adnl, value_for_comparison=value_percent, 
			upper_threshold=90, lower_threshold=85, value=cpu_load, value_percent=value_percent, max_value=cpu_number)
	#end define

	def check_ram(self, user, node):
		adnl = node.adnl_address
		memory_usage = node.data.memory.usage
		memory_total = node.data.memory.total
		#if memory_usage > memory_total - 20:
		#	self.warn("RAM", user, adnl, memory_usage, memory_total)
		#elif memory_usage < memory_total - 10:
		#	self.warn("RAM", user, adnl, memory_usage, memory_total, overloaded=False)
		value_percent = round(memory_usage/memory_total*100, 2)
		self.check_with_threshold(user, alert_name="RAM", adnl=adnl, value_for_comparison=value_percent, 
			upper_threshold=90, lower_threshold=85, value=memory_usage, value_percent=value_percent, max_value=memory_total)
	#end define

	def check_network(self, user, node):
		adnl = node.adnl_address
		network_load = node.data.netLoad[2]
		#if network_load > 500:
		#	self.warn("Network", user, adnl, network_load, "Mbit/s")
		#elif network_load < 450:
		#	self.warn("Network", user, adnl, network_load, "Mbit/s", overloaded=False)
		self.check_with_threshold(user, alert_name="Network", adnl=adnl, value_for_comparison=network_load, 
			upper_threshold=500, lower_threshold=450, value=network_load)
	#end define

	def check_disk(self, user, node):
		adnl = node.adnl_address
		disk_name = os.path.basename(node.data.validatorDiskName)
		if disk_name not in node.data.disksLoad:
			#print(f"{disk_name} not in {list(node.data.disksLoad.keys())}")
			disk_name = list(node.data.disksLoad.keys())[0]
		disk_load = node.data.disksLoad[disk_name][2]
		disk_load_percent = node.data.disksLoadPercent[disk_name][2]
		#if disk_load_percent > 90:
		#	self.warn("Disk", user, adnl, disk_load, "MB/s")
		#elif disk_load_percent < 80:
		#	self.warn("Disk", user, adnl, disk_load, "MB/s", overloaded=False)
		self.check_with_threshold(user, alert_name="Disk", adnl=adnl, value_for_comparison=disk_load_percent, 
			upper_threshold=90, lower_threshold=80, value=disk_load, value_percent=disk_load_percent)
	#end define

	def check_uptime(self, user, node):
		pass
	#end define

	def check_with_threshold(self, user, alert_name, upper_threshold, lower_threshold, value_for_comparison, **kwargs):
		if value_for_comparison > upper_threshold:
			self.warn(user, alert_name, overloaded=True, threshold=upper_threshold, **kwargs)
		elif value_for_comparison < lower_threshold:
			self.warn(user, alert_name, overloaded=False, threshold=lower_threshold, **kwargs)
	#end define

	def warn(self, user, alert_name, overloaded, **kwargs):
		adnl = kwargs.get("adnl")
		alert_id = f"{type(self).__name__}-{alert_name}-{adnl}"
		triggered_alerts_list = user.get_triggered_alerts_list()
		if (alert_id in triggered_alerts_list) == overloaded:
			return
		#end if

		adnl_short = get_adnl_text(user, adnl)
		overloaded_str = "_overloaded" if overloaded else "_ok"
		template_name = alert_name.lower() + overloaded_str
		alert_text = collect_template(self.local, template_name, adnl_short=adnl_short, **kwargs)
		user.add_message(alert_text)
		if overloaded is True:
			triggered_alerts_list[alert_id] = get_timestamp()
		else:
			del triggered_alerts_list[alert_id]
	#end define
#end class
