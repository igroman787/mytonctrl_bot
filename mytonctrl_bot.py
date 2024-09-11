#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import time
import json
import threading
import urllib.request
from mypylib.mypylib import MyPyClass, Dict, get_timestamp

# Telegram components
#pip3 install python-telegram-bot==13.7
from telegram import Bot, ParseMode
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

from utils import (
	read_file,
	get_config,
	get_dict_from,
	find_text_in_list,
	get_item_from_list
)
from user import User, get_users
from user_alerts import (
	ComplaintsAlert,
	TelemetryAlert,
	ComplaintsInformation
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

	local.start_cycle(message_sender, sec=1)
	local.start_cycle(scan_alerts, sec=60)
#end define

def init_alerts():
	complaints_alerts = ComplaintsAlert(local, toncenter)
	telemetry_alerts = TelemetryAlert(local, toncenter)
	complaints_information = ComplaintsInformation(local, toncenter)
	local.buffer.possible_alerts = [complaints_alerts, telemetry_alerts, complaints_information]
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
#end define

def message_sender():
	users = get_users(local)
	for user in users:
		user.send_messages(send_message)
#end define

def send_message(user, text, markdown=True):
	# print(f"send_message user: {user.id}, text: {text}")
	if len(text) == 0:
		text = "No result"
	if type(text) == str:
		send_message_work(user, text, markdown)
	elif type(text) == list:
		for item in text:
			send_message_work(user, item, markdown)
#end define

def send_message_work(user, text, markdown=True):
	# print("send_message_work.text:", json.dumps(text))
	# context.bot.sendMessage(user.id=user.id, text=text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True, disable_notification=True)
	parse_mode = None
	if markdown == True:
		parse_mode = ParseMode.MARKDOWN
	local.buffer.updater.bot.sendMessage(chat_id=user.id, text=text, parse_mode=parse_mode, disable_web_page_preview=True, disable_notification=True)
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
	#remove_alert_handler = CommandHandler("remove_alert", remove_alert_cmd)
	#alert_list_handler = CommandHandler("alert_list", alert_list_cmd)
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
	#dispatcher.add_handler(remove_alert_handler)
	#dispatcher.add_handler(alert_list_handler)
	dispatcher.add_handler(unknown_handler)

	return updater
#end define

def echo_cmd(update, context):
	#input = update.message.text
	#input = context.args
	user = User(local, update.effective_user.id)
	output = "Technical support for validators: @mytonctrl_help_bot"
	send_message(user, output, markdown=False)
#end define

def unknown_cmd(update, context):
	user = User(local, update.effective_user.id)
	output = "Sorry, I didn't understand that command."
	send_message(user, output)
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

def do_add_adnl_cmd(user, input_adnl, input_label):
	validators_list = toncenter.get_validators_list()
	adnl = find_text_in_list(validators_list, input_adnl)
	if adnl is None:
		output = f"ADNL not found: _{input_adnl}_"
	else:
		output = user.add_adnl(adnl)
		user.add_label(input_label)
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

def remove_adnl_cmd(update, context):
	user = User(local, update.effective_user.id)

	input_args = context.args
	input_item = get_item_from_list(input_args)

	user_adnl_list = user.get_adnl_list()
	user_labels = user.get_labels()
	adnl = find_text_in_list(user_adnl_list, input_item)
	if input_item is None:
		output = "error"
	elif adnl is None:
		output = "error2"
	else:
		user_adnl_list.remove(adnl)
		if adnl in user_labels:
			user_labels.pop(adnl)
		output = "ok"
	send_message(user, output)
#end define

def adnl_list_cmd(update, context):
	user = User(local, update.effective_user.id)

	user_adnl_list = user.get_adnl_list()
	user_labels = user.get_labels()
	output = ""
	for adnl in user_adnl_list:
		label = user_labels.get(adnl, "")
		output += f"`{adnl} {label}`"
	# output = json.dumps(user_adnl_list, indent=2)
	# output = f"`{output}`"
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
	buff = ListFraction(data, 16)
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
	# print("Status2Text.item:", json.dumps(item))
	label = item.get("label")
	adnl_addr = item.get("adnl_addr")
	adnl_ending = item.get("adnl_ending")
	isValidator = item.get("isValidator")
	isSendTelemetry = item.get("isSendTelemetry")
	telemetry_availability = item.get("telemetry_availability")
	isWorking = item.get("isWorking", "unknown")
	cpuLoad = item.get("cpuLoad")
	netLoad = item.get("netLoad")
	outOfSync = item.get("outOfSync")
	status_icon = item.get("status_icon")
	if label:
		output += f"Label:            {label}" + '\n'
	output += f"ADNL:            ...{adnl_ending} `{status_icon}`" + '\n'
	output += f"Validator:       {isValidator}" + '\n'
	if isValidator:
		output += f"Send telemetry:  {isSendTelemetry}" + '\n'
		output += f"Working:         {isWorking}" + '\n'
	if telemetry_availability:
		output += f"Out of sync:     {outOfSync}" + '\n'
		output += f"Cpu load:        {cpuLoad}" + '\n'
		output += f"Net load:        {netLoad}" + '\n'
	if telemetry_availability == False and isSendTelemetry == True:
		output += "Warning: Telemetry is only available to validator owners. "
		output += "Confirm node ownership with command /add_fullnode_adnl" + '\n'
	output += '\n'
	output = f"`{output}`"
	return output
#end define

def get_validator_status(user, adnl_addr):
	data = Dict()
	data.isValidator = False
	data.isSendTelemetry = False
	data.telemetry_availability = False

	# get data
	validators = toncenter.get_validators()
	user_fullnode_adnl_list = user.get_fullnode_adnl_list()

	# Get validator info
	for validator in validators:
		itemAdnlAddr = validator.get("adnl_addr")
		if adnl_addr == itemAdnlAddr:
			# print("get_validator_status.validator:", json.dumps(validator))
			data.isValidator = True
			data.adnl_addr = adnl_addr
			data.adnl_ending = adnl_addr[58:65]
			data.pubkey = validator.get("pubkey")
			data.weight = validator.get("weight")
	#end for

	# Get node info
	node = toncenter.get_telemetry(user, adnl_addr)
	data.isSendTelemetry = toncenter.is_send_telemetry(adnl_addr)
	if node:
		data.telemetry_availability = True
		data.cpuLoad = node.data.cpuLoad
		data.netLoad = node.data.netLoad
		buffStatus = node.data.validatorStatus
		if buffStatus:
			data.isWorking = buffStatus.get("isWorking")
			data.unixtime = buffStatus.get("unixtime")
			data.masterchainblocktime = buffStatus.get("masterchainblocktime")
			data.outOfSync = buffStatus.get("outOfSync")
		#end if
	#end if

	# Set status
	isWorking = data.get("isWorking")
	outOfSync = data.get("outOfSync")
	isValidator = data.get("isValidator")

	status = None
	# Если нода отправляет телеметрию
	if outOfSync is not None:
		# Если рассинхронизация > 300, или эффективность < 10, или нода не работает
		if outOfSync > 300 or isWorking is False:
			status = False
		else:
			status = True
	#end if

	# Set status icon
	if status is True:
		status_icon = "✅"
	elif status is False:
		status_icon = "❌"
	else:
		status_icon = ""
	data["status_icon"] = status_icon
	data["status"] = status

	return data
#end define

def ListFraction(inputList, maxLen):
	buff = list()
	result = list()
	for item in inputList:
		if len(buff) == maxLen:
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
	user_alerts_list = user.get_alerts_list()
	for alert in local.buffer.possible_alerts:
		if type(alert).__name__ in user_alerts_list:
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













