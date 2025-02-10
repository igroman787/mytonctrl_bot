#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import sys
import time
import json
import urllib.request
from mypylib.mypylib import (
	MyPyClass,
	Dict,
	get_timestamp,
	get_git_hash
)

# Telegram components
#pip3 install python-telegram-bot==13.7
from telegram import Bot, ParseMode
from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown
from telegram.ext import (
	Updater,
	CommandHandler,
	MessageHandler,
	Filters,
)

from utils import (
	read_file,
	get_config,
	get_dict_from,
	find_text_in_list,
	get_item_from_list
)
from user import (
	User,
	get_users,
	get_active_users,
	inform_admins
)
from user_alerts import (
	ComplaintsAlert,
	TelemetryAlert,
	ComplaintsInformation,
	ElectionsInformation
)
from toncenter import Toncenter


# Global vars
local = MyPyClass(__file__)
toncenter = Toncenter(local)


def init():
	init_alerts()
	init_buffer()

	# Load translate table
	# local.InitTranslator(local.buffer.get("myDir") + "translate.json")

	# Set local config
	local.db.config.isLocaldbSaving = True
	local.db.config.logLevel = "debug"
	local.run()

	# Start threads
	local.start_cycle(message_sender, sec=0.1)
	local.start_cycle(scan_alerts, sec=60)
#end define

def init_alerts():
	complaints_alerts = ComplaintsAlert(local, toncenter)
	telemetry_alerts = TelemetryAlert(local, toncenter)
	complaints_information = ComplaintsInformation(local, toncenter)
	elections_information = ElectionsInformation(local, toncenter)
	local.buffer.possible_alerts = [complaints_alerts, telemetry_alerts, complaints_information, elections_information]
	local.buffer.possible_alerts_list = list()
	for item in local.buffer.possible_alerts:
		local.buffer.possible_alerts_list.append(type(item).__name__)
	local.buffer.possible_alerts_text = ", ".join(local.buffer.possible_alerts_list)
#end define

def init_buffer():
	config_path = local.buffer.my_dir + "settings.json"
	data = get_config(config_path)
	local.buffer.telegram_bot_token = data.telegram_bot_token
	local.buffer.api_key = data.api_key
	local.db.delay = data.delay if type(data.delay) == int else 60
	local.buffer.admins = data.admins if type(data.admins) == list else list()
	local.buffer.version = get_git_hash(local.buffer.my_dir, short=True)
#end define

def message_sender():
	users = get_users(local)
	for user in users:
		user.send_messages(send_message)
#end define

def send_message(user, text):
	# print(f"send_message user: {user.id}, text: {text}")
	if len(text) == 0:
		text = "No result"
	if type(text) == str:
		do_send_message(user, text)
	elif type(text) == list:
		for item in text:
			do_send_message(user, item)
#end define

def do_send_message(user, text):
	# print(f"do_send_message.text: `{text}`")
	# context.bot.sendMessage(user.id=user.id, text=text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True, disable_notification=True)
	try:
		local.buffer.updater.bot.sendMessage(chat_id=user.id, text=text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True, disable_notification=True)
	except BadRequest as ex:
		if ex.message == "Chat not found":
			user.delete()
		else:
			raise BadRequest(ex)
#end define

def init_bot():
	# bot = Bot(token=telegram_bot_token)
	# print(f"local.buffer: {local.buffer}")
	telegram_bot_token = local.buffer.telegram_bot_token
	updater = Updater(token=telegram_bot_token, use_context=True)
	dispatcher = updater.dispatcher
	local.buffer["updater"] = updater

	# Create handlers
	echo_handler = MessageHandler(Filters.text & (~Filters.command), echo_cmd)
	
	start_handler = CommandHandler("start", start_cmd)
	help_handler = CommandHandler("help", help_cmd)
	status_handler = CommandHandler("status", status_cmd)
	add_adnl_handler = CommandHandler("add_adnl", add_adnl_cmd)
	add_fullnode_adnl_handler = CommandHandler("add_fullnode_adnl", add_fullnode_adnl_cmd)
	remove_adnl_handler = CommandHandler("remove_adnl", remove_adnl_cmd)
	adnl_list_handler = CommandHandler("adnl_list", adnl_list_cmd)
	add_alert_handler = CommandHandler("add_alert", add_alert_cmd)
	remove_alert_handler = CommandHandler("remove_alert", remove_alert_cmd)
	alert_list_handler = CommandHandler("alert_list", alert_list_cmd)

	me_handler = CommandHandler("me", me_cmd)
	bot_handler = CommandHandler("bot", bot_cmd)
	add_notification_handler = CommandHandler("add_notification", add_notification_cmd)
	print_notification_handler = CommandHandler("print_notification", print_notification_cmd)
	start_notification_handler = CommandHandler("start_notification", start_notification_cmd)
	stop_notification_handler = CommandHandler("stop_notification", stop_notification_cmd)
	

	unknown_handler = MessageHandler(Filters.command, unknown_cmd)

	# Add handlers
	
	dispatcher.add_handler(echo_handler)
	dispatcher.add_handler(start_handler)
	dispatcher.add_handler(help_handler)
	dispatcher.add_handler(status_handler)
	dispatcher.add_handler(add_adnl_handler)
	dispatcher.add_handler(add_fullnode_adnl_handler)
	dispatcher.add_handler(remove_adnl_handler)
	dispatcher.add_handler(adnl_list_handler)
	dispatcher.add_handler(add_alert_handler)
	dispatcher.add_handler(remove_alert_handler)
	dispatcher.add_handler(alert_list_handler)

	dispatcher.add_handler(me_handler)
	dispatcher.add_handler(bot_handler)
	dispatcher.add_handler(add_notification_handler)
	dispatcher.add_handler(print_notification_handler)
	dispatcher.add_handler(start_notification_handler)
	dispatcher.add_handler(stop_notification_handler)
	

	dispatcher.add_handler(unknown_handler)

	return updater
#end define

def echo_cmd(update, context):
	#input = update.message.text
	#input = context.args
	user = User(local, update.effective_user.id)
	output = "Technical support for validators: @mytonctrl_help_bot"
	send_message(user, escape_markdown(output))
#end define

def unknown_cmd(update, context):
	user = User(local, update.effective_user.id)
	output = "Sorry, I didn't understand that command."
	send_message(user, escape_markdown(output))
#end define

def start_cmd(update, context):
	user = User(local, update.effective_user.id)
	output = "This bot allows you to monitor the state of the validator." + '\n'
	output += "For more information use command /help"
	send_message(user, output)
#end define

def help_cmd(update, context):
	user = User(local, update.effective_user.id)
	file_path = local.buffer.my_dir + "help.txt"
	output = read_file(file_path)
	send_message(user, output)
#end define

def me_cmd(update, context):
	user = User(local, update.effective_user.id)
	output = f"User: `{user.id}`" + '\n'
	if user.is_admin() == True:
		text = "Available commands: /add_notification, /print_notification, /start_notification, /stop_notification"
		output += escape_markdown(text)
	send_message(user, output)
#end define

def bot_cmd(update, context):
	user = User(local, update.effective_user.id)
	if user.is_admin() == False:
		unknown_cmd(update, context)
		return
	#end if

	active_users = get_active_users(local)
	db_size = round(sys.getsizeof(local.db)/10**6, 2)
	buffer_size = round(sys.getsizeof(local.buffer)/10**6, 2)
	output = f"version: `{local.buffer.version}`" + '\n'
	output += f"users: `{len(active_users)}/{len(local.db.users)}`" + '\n'
	output += f"db size: `{db_size} Mb`" + '\n'
	output += f"buffer size: `{buffer_size} Mb`" + '\n'
	send_message(user, output)
#end define

def add_notification_cmd(update, context):
	user = User(local, update.effective_user.id)
	if user.is_admin() == False:
		unknown_cmd(update, context)
		return
	#end if

	text = update.message.text_markdown
	if '\n' in text:
		notification = text[text.find('\n') + 1:]
	elif ' ' in text:
		notification = text[text.find(' ') + 1:]
	else:
		notification = None
	#end if

	if notification and len(notification) > 0:
		local.db.notification = notification
		output = "Notification added"
	else:
		output = "Empty notification"
	send_message(user, output)
#end define

def print_notification_cmd(update, context):
	user = User(local, update.effective_user.id)
	if user.is_admin() == False:
		unknown_cmd(update, context)
		return
	#end if

	if local.db.notification == None or len(local.db.notification) == 0:
		output = "Empty notification"
		send_message(user, output)
		return
	#end if

	send_message(user, local.db.notification)
#end define

def start_notification_cmd(update, context):
	username = escape_markdown('@' + update.effective_user.username)
	user = User(local, update.effective_user.id)
	if user.is_admin() == False:
		unknown_cmd(update, context)
		return
	#end if

	if local.db.notification == None or len(local.db.notification) == 0:
		output = "Empty notification"
		send_message(user, output)
		return
	#end if

	if local.buffer.notification_sending == True:
		output = "Already started"
		send_message(user, output)
		return
	#end if

	local.start_thread(do_notification_sending)
	local.buffer.notification_sending = True
	output = f"Start notification sending by {username} in {local.db.delay} seconds"
	inform_admins(local, output)
#end define

def do_notification_sending():
	time.sleep(local.db.delay)
	if local.db.notification == None or len(local.db.notification) == 0:
		return
	#end if

	active_users = get_active_users(local)
	for user_id, user in active_users.items():
		user.add_message(local.db.notification)
	local.db.notification = None
	local.buffer.notification_sending = None
#end define

def stop_notification_cmd(update, context):
	username = escape_markdown('@' + update.effective_user.username)
	user = User(local, update.effective_user.id)
	if user.is_admin() == False:
		unknown_cmd(update, context)
		return
	#end if

	local.db.notification = None
	output = f"Stop notification sending by {username}"
	inform_admins(local, output)
#end define

def add_adnl_cmd(update, context):
	user = User(local, update.effective_user.id)

	try:
		adnl = context.args[0]
		label = get_item_from_list(context.args, 1)
	except:
		error = "Bad args. Usage: `add_adnl <adnl> [<label>]`"
		send_message(user, error)
		return
	do_add_adnl_cmd(user, adnl, label)
#end define

def do_add_adnl_cmd(user, adnl, label):
	#validators_list = toncenter.get_validators_list()
	nodes_list = toncenter.get_nodes_list()
	if adnl in nodes_list:
		output = user.add_adnl(adnl)
		user.add_label(adnl, label)
	else:
		output = f"_{adnl}_ not found"
	send_message(user, output)
#end define

def remove_adnl_cmd(update, context):
	user = User(local, update.effective_user.id)
	user_adnl_list = user.get_adnl_list()
	#user_adnl_list_text = ", ".join(user_adnl_list)

	try:
		adnl = context.args[0]
	except:
		error = "Bad args. Usage: `remove_adnl <adnl>`" + '\n'
		#error += f"User adnl list: _{user_adnl_list_text}_"
		send_message(user, error)
		return
	#end try

	if adnl in user_adnl_list:
		user_adnl_list.remove(adnl)
		output = f"_{adnl}_ is delated"
	else:
		output = f"_{adnl}_ not found" + 'n'
		#output += f"User adnl list: _{user_adnl_list_text}_"
	send_message(user, output)
#end define

def adnl_list_cmd(update, context):
	user = User(local, update.effective_user.id)

	user_adnl_list = user.get_adnl_list()
	user_labels = user.get_labels()
	output = ""
	for adnl in user_adnl_list:
		label = user_labels.get(adnl, "")
		output += f"`{adnl} {label}`" + '\n'
	# output = json.dumps(user_adnl_list, indent=2)
	# output = f"`{output}`"
	send_message(user, output)
#end define

def add_fullnode_adnl_cmd(update, context):
	user = User(local, update.effective_user.id)

	try:
		fullnode_adnl = context.args[0]
	except:
		error = "Bad args. Usage: `add_fullnode_adnl <fullnode_adnl>`"
		send_message(user, error)
		return
	output = user.add_fullnode_adnl(fullnode_adnl)
	send_message(user, output)
#end define

def add_alert_cmd(update, context):
	user = User(local, update.effective_user.id)

	try:
		alert_type = context.args[0]
	except:
		error = "Bad args. Usage: `add_alert <alert_type>`" + '\n'
		error += f"Possible alerts: _{local.buffer.possible_alerts_text}_"
		send_message(user, error)
		return
	output = user.add_alert(alert_type)
	send_message(user, output)
#end define

def remove_alert_cmd(update, context):
	user = User(local, update.effective_user.id)
	user_alert_list = user.get_alerts_list()
	#user_alert_text = ", ".join(user_alert_list)

	try:
		alert_type = context.args[0]
	except:
		error = "Bad args. Usage: `remove_alert <alert_type>`" + '\n'
		#error += f"User alerts: _{user_alert_text}_"
		send_message(user, error)
		return
	#end try

	if alert_type in user_alert_list:
		user_alert_list.remove(alert_type)
		output = f"_{alert_type}_ is delated"
	else:
		output = f"_{alert_type}_ not found" + 'n'
		#output += f"User alerts: _{user_alert_text}_"
	send_message(user, output)
#end define

def alert_list_cmd(update, context):
	user = User(local, update.effective_user.id)
	user_alert_list = user.get_alerts_list()
	user_alert_text = ", ".join(user_alert_list)
	output = f"User alerts: _{user_alert_text}_" + '\n'
	output += f"Possible alerts: _{local.buffer.possible_alerts_text}_"
	send_message(user, output)
#end define

def status_cmd(update, context):
	user = User(local, update.effective_user.id)
	data = get_my_status(user)
	output = Status2TextWithFraction(data)
	send_message(user, output)
#end define

def get_my_status(user):
	'''Отобразить статусы своих валидаторов'''
	user_labels = user.get_labels()
	user_adnl_list = user.get_adnl_list()
	result = list()
	for adnl_addr in user_adnl_list:
		data = get_validator_status(user, adnl_addr)
		data["label"] = user_labels.get(adnl_addr)
		result.append(data)
	return result
#end define

def Status2TextWithFraction(data):
	result = list()
	buff = list_fraction(data, 16)
	# print("Status2TextWithFraction.data:", json.dumps(data))
	# print("Status2TextWithFraction.buff:", json.dumps(buff))
	for item in buff:
		text = StatusList2Text(item)
		result.append(text)
	# print("Status2TextWithFraction.result:", json.dumps(result))
	return result
#end define

def StatusList2Text(data):
	output = ""
	for item in data:
		output += Status2Text(item)
	return output
#end define

def Status2Text(item):
	output = ""
	if item.label:
		output += f"Label:            {item.label}" + '\n'
	output += f"ADNL:            {item.adnl_short}... `{item.status_icon}`" + '\n'
	output += f"Validator:       {item.is_validator}" + '\n'
	output += f"Send telemetry:  {item.is_send_telemetry}" + '\n'
	if item.is_validator:
		output += f"Working:         {item.isWorking}" + '\n'
	if item.telemetry_availability:
		output += f"Out of sync:     {item.outOfSync}" + '\n'
		output += f"Cpu load:        {item.cpuLoad}" + '\n'
		output += f"Net load:        {item.netLoad}" + '\n'
	#if item.telemetry_availability == False and item.is_send_telemetry == True:
	#	output += "Warning: Telemetry is only available to validator owners. "
	#	output += "Confirm node ownership with command /add_fullnode_adnl" + '\n'
	output += '\n'
	output = f"`{output}`"
	return output
#end define

def get_validator_status(user, adnl_addr):
	data = Dict()
	data.adnl_addr = adnl_addr
	data.adnl_short = adnl_addr[0:7]
	data.is_validator = False
	data.is_send_telemetry = False
	data.telemetry_availability = False

	# get data
	validators = toncenter.get_validators()
	user_fullnode_adnl_list = user.get_fullnode_adnl_list()

	# Get validator info
	for validator in validators:
		itemAdnlAddr = validator.get("adnl_addr")
		if adnl_addr == itemAdnlAddr:
			# print("get_validator_status.validator:", json.dumps(validator))
			data.is_validator = True
			#data.adnl_addr = adnl_addr
			#data.adnl_ending = adnl_addr[58:65]
			data.pubkey = validator.get("pubkey")
			data.weight = validator.get("weight")
	#end for

	# Get node info
	node = toncenter.get_telemetry(user, adnl_addr)
	data.is_send_telemetry = toncenter.is_send_telemetry(adnl_addr)
	if node:
		data.telemetry_availability = True
		data.cpuLoad = node.data.cpuLoad
		data.netLoad = node.data.netLoad
		buff_status = node.data.validatorStatus
		if buff_status:
			data.isWorking = buff_status.get("isWorking")
			data.unixtime = buff_status.get("unixtime")
			data.masterchainblocktime = buff_status.get("masterchainblocktime")
			data.outOfSync = buff_status.get("outOfSync")
		#end if
	#end if

	# Set status
	isWorking = data.get("isWorking")
	outOfSync = data.get("outOfSync")
	is_validator = data.get("is_validator")

	status = None
	# Если нода отправляет телеметрию
	if outOfSync != None:
		# Если рассинхронизация > 300, или нода не работает
		if outOfSync > 300 or isWorking == False:
			status = False
		else:
			status = True
	#end if

	# Set status icon
	if status == True and is_validator == True:
		status_icon = "✅"
	elif status == True and is_validator == False:
		status_icon = "☑️"
	elif status == False:
		status_icon = "❌"
	else:
		status_icon = ""
	data["status_icon"] = status_icon
	data["status"] = status

	return data
#end define

def list_fraction(input_list, max_len):
	buff = list()
	result = list()
	for item in input_list:
		if len(buff) == max_len:
			result.append(buff)
			buff = list()
		buff.append(item)
	if len(buff) > 0:
		result.append(buff)
	return result
#end define

def scan_alerts():
	users = get_users(local)
	for user in users:
		try_scan_user_alerts(user)
#end define

def try_scan_user_alerts(user):
	try:
		scan_user_alerts(user)
	except Exception as er:
		local.add_log(f"scan_user_alerts {user.id} error: {er}", "error")
#end define

def scan_user_alerts(user):
	user_alert_list = user.get_alerts_list()
	for alert in local.buffer.possible_alerts:
		if type(alert).__name__ in user_alert_list:
			alert.check(user)
#end define




###
### Start of the program
###

if __name__ == "__main__":
	init()
	updater = init_bot()
	updater.start_polling()
#end if













