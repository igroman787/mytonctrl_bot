#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import time
import json
import threading
import urllib.request
from mypylib.mypylib import *

# Telegram components
#pip3 install python-telegram-bot
from telegram import Bot, ParseMode
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters



# Global vars
local = MyPyClass(__file__)


def Init():
	# Load bot settings (telegramBotToken)
	file = open("settings.json", "rt")
	text = file.read()
	file.close()
	buff = json.loads(text)
	local.buffer["telegramBotToken"] = buff.get("telegramBotToken")

	# Load translate table
	# local.InitTranslator(local.buffer.get("myDir") + "translate.json")

	# Set local config
	local.db["config"]["isLocaldbSaving"] = True
	local.db["config"]["logLevel"] = "debug"
	local.Run()

	# Start threads
	local.StartCycle(MessageSender, sec=3)
	local.StartCycle(ScanValidators, sec=60)
#end define

def TryGetUrl(url):
	for i in range(3):
		try:
			data = GetUrl(url)
			return data
		except Exception as err:
			time.sleep(1)
	raise Exception("TryGetUrl error: {err}")
#end define

def GetUrl(url):
	req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	web = urllib.request.urlopen(req)
	data = web.read()
	text = data.decode()
	return text
#end define

def GetToncenterData():
	# Get buffer
	timestamp = GetTimestamp()
	toncenterData = local.buffer.get("toncenterData")
	if toncenterData:
		diffTime = timestamp - toncenterData.get("timestamp")
		if diffTime < 60:
			return toncenterData
	#end if

	# Get gata
	url = "https://toncenter.com/api/newton_test/status/debug"
	text = TryGetUrl(url)
	data = json.loads(text)
	nodes = data.get("nodes_stats")
	validators = data.get("current_validators")

	# Set buffer
	toncenterData = dict()
	toncenterData["timestamp"] = timestamp
	toncenterData["nodes"] = nodes
	toncenterData["validators"] = validators
	local.buffer["toncenterData"] = toncenterData
	return toncenterData
#end define

def GetValidatorStatus(adnlAddr):
	data = dict()
	data["isValidator"] = False
	data["isSendTelemetry"] = False

	# get data
	toncenterData = GetToncenterData()
	validators = toncenterData.get("validators")
	nodes = toncenterData.get("nodes")

	# Get validator info
	for item in validators:
		itemAdnlAddr = item.get("adnlAddr")
		if adnlAddr == itemAdnlAddr:
			# print("GetValidatorStatus.item:", json.dumps(item))
			data["isValidator"] = True
			data["adnlAddr"] = adnlAddr
			data["adnlEnding"] = adnlAddr[58:65]
			data["pubkey"] = item.get("pubkey")
			data["weight"] = item.get("weight")
			data["mr"] = item.get("mr")
			data["wr"] = item.get("wr")
			data["efficiency"] = item.get("efficiency")
		#end for

	# Get node info
	buff = nodes.get(adnlAddr)
	if buff is not None:
		data["isSendTelemetry"] = True
		data["cpuLoad"] = buff.get("cpuLoad")
		data["netLoad"] = buff.get("netLoad")
		data["tps"] = buff.get("tps")
		buffStatus = buff.get("validatorStatus")
		if buffStatus:
			data["isWorking"] = buffStatus.get("isWorking")
			data["unixtime"] = buffStatus.get("unixtime")
			data["masterchainblocktime"] = buffStatus.get("masterchainblocktime")
			data["outOfSync"] = buffStatus.get("outOfSync")
	#end if

	# Set status
	isWorking = data.get("isWorking")
	outOfSync = data.get("outOfSync")
	efficiency = data.get("efficiency")
	isValidator = data.get("isValidator")
	if outOfSync and outOfSync < 300 and efficiency and efficiency > 10:
		status = True
	elif outOfSync is None and efficiency and efficiency > 10:
		status = True
	elif efficiency is None and outOfSync and outOfSync < 300:
		status = True
	elif efficiency is None:
		status = None
	else:
		status = False
	if isValidator is False:
		status = None
	if status is True:
		statusIcon = "✅"
	elif status is False:
		statusIcon = "❌"
	else:
		statusIcon = ""
	data["statusIcon"] = statusIcon
	data["status"] = status
	#end if

	return data
#end define

def SendMessage(chatId, output):
	# print("SendMessage.output:", json.dumps(output))
	if type(output) == str:
		SendMessageWork(chatId, output)
	elif type(output) == list:
		for item in output:
			SendMessageWork(chatId, item)
#end define

def SendMessageWork(chatId, output):
	# print("SendMessageWork.output:", json.dumps(output))
	# context.bot.sendMessage(chat_id=chatId, text=output, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True, disable_notification=True)
	local.buffer["updater"].bot.sendMessage(chat_id=chatId, text=output, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True, disable_notification=True)
#end define

def GetItem(inputArgs, index=0):
	try:
		inputItem = inputArgs[index]
	except:
		inputItem = None
	return inputItem
#end define

def GetUsers():
	users = local.db.get("users")
	if users is None:
		users = dict()
		local.db["users"] = users
	return users
#end define

def GetUserDb(userId):
	userId = str(userId)
	users = GetUsers()
	userDb = users.get(userId)
	if userDb is None:
		userDb = dict()
		users[userId] = userDb
	return userDb
#end define

def GetUserAdnlList(userId):
	userId = str(userId)
	userDb = GetUserDb(userId)
	adnlList = userDb.get("adnlList")
	if adnlList is None:
		adnlList = list()
		userDb["adnlList"] = adnlList
	return adnlList
#end define

def GetUserAlarmList(userId):
	userId = str(userId)
	userDb = GetUserDb(userId)
	alarmList = userDb.get("alarmList")
	if alarmList is None:
		alarmList = list()
		userDb["alarmList"] = alarmList
	return alarmList
#end define

def GetUserLabels(userId):
	userId = str(userId)
	userDb = GetUserDb(userId)
	labels = userDb.get("labels")
	if labels is None:
		labels = dict()
		userDb["labels"] = labels
	return labels
#end define

def FindTextInList(inputList, text):
	result = None
	if text is None:
		return result
	textLen = len(text)
	for item in inputList:
		itemLen = len(item)
		start = itemLen-textLen
		buff = item[start:itemLen]
		if text == buff:
			result = item
	return result
#end define

def GetValidatorsList():
	result = list()
	toncenterData = GetToncenterData()
	validators = toncenterData.get("validators")
	for item in validators:
		adnlAddr = item.get("adnlAddr")
		if adnlAddr:
			result.append(adnlAddr)
	return result
#end define

def InitBot():
	# bot = Bot(token=telegramBotToken)
	telegramBotToken = local.buffer.get("telegramBotToken")
	updater = Updater(token=telegramBotToken, use_context=True)
	dispatcher = updater.dispatcher
	local.buffer["updater"] = updater

	# Create handlers
	echoHandler = MessageHandler(Filters.text & (~Filters.command), EchoCmd)
	startHandler = CommandHandler("start", StartCmd)
	statusHandler = CommandHandler("status", StatusCmd)
	stHandler = CommandHandler("st", StatusCmd)
	addHandler = CommandHandler("add", AddCmd)
	delHandler = CommandHandler("del", DelCmd)
	listHandler = CommandHandler("list", ListCmd)
	lsHandler = CommandHandler("ls", ListCmd)
	unknownHandler = MessageHandler(Filters.command, UnknownCmd)

	# Add handlers
	dispatcher.add_handler(echoHandler)
	dispatcher.add_handler(startHandler)
	dispatcher.add_handler(statusHandler)
	dispatcher.add_handler(stHandler)
	dispatcher.add_handler(addHandler)
	dispatcher.add_handler(delHandler)
	dispatcher.add_handler(listHandler)
	dispatcher.add_handler(lsHandler)
	dispatcher.add_handler(unknownHandler)

	return updater
#end define

def EchoCmd(update, context):
	#input = update.message.text
	#input = context.args
	chatId = update.effective_chat.id
	output = "Хм..."
	output = "Hm..."
	SendMessage(chatId, output)
#end define

def UnknownCmd(update, context):
	chatId = update.effective_chat.id
	output = "Извините, я не понял эту команду."
	output = "Sorry, I didn't understand that command."
	SendMessage(chatId, output)
#end define

def StartCmd(update, context):
	chatId = update.effective_chat.id
	output = "Данный бот позволяет следить за состоянием валидатора."
	output = "This bot allows you to monitor the state of the validator."
	SendMessage(chatId, output)
#end define

def AddCmd(update, context):
	chatId = update.effective_chat.id
	userId = update.effective_user.id
	inputArgs = context.args
	inputAdnl = GetItem(inputArgs) # <adnl-addr>
	inputLabel = GetItem(inputArgs, 1) # <label>

	validatorsList = GetValidatorsList()
	adnl = FindTextInList(validatorsList, inputAdnl)
	if inputAdnl is None:
		output = "error"
	elif adnl is None:
		output = "error2"
	else:
		userAdnlList = GetUserAdnlList(userId)
		userAdnlList.append(adnl)
		output = "ok"
		if inputLabel is not None:
			userLabels = GetUserLabels(userId)
			userLabels[adnl] = inputLabel
	SendMessage(chatId, output)
#end define

def DelCmd(update, context):
	chatId = update.effective_chat.id
	userId = update.effective_user.id
	inputArgs = context.args
	inputItem = GetItem(inputArgs)

	userLabels = GetUserLabels(userId)
	userAdnlList = GetUserAdnlList(userId)
	adnl = FindTextInList(userAdnlList, inputItem)
	if inputItem is None:
		output = "error"
	elif adnl is None:
		output = "error2"
	else:
		userAdnlList.remove(adnl)
		if adnl in userLabels:
			userLabels.pop(adnl)
		output = "ok"
	SendMessage(chatId, output)
#end define

def ListCmd(update, context):
	chatId = update.effective_chat.id
	userId = update.effective_user.id
	userAdnlList = GetUserAdnlList(userId)
	userLabels = GetUserLabels(userId)
	output = ""
	for adnl in userAdnlList:
		label = userLabels.get(adnl, "")
		output += f"`{adnl} {label}`"
	# output = json.dumps(userAdnlList, indent=2)
	# output = f"`{output}`"
	SendMessage(chatId, output)
#end define


def StatusCmd(update, context):
	chatId = update.effective_chat.id
	userId = update.effective_user.id
	inputArgs = context.args
	inputItem = GetItem(inputArgs)

	if inputItem is None:
		# Отобразить статусы своих валидаторов
		data = GetMyStatus(userId)
		output = Status2TextWithFraction(data)
	elif inputItem == "all":
		# Отобразить статусы всех валидаторов
		data = GetAllStatus(userId)
		output = Status2TextWithFraction(data)
	elif inputItem == "died":
		# Отобразить статусы мертвых валидаторов
		data = GetDiedStatus(userId)
		output = Status2TextWithFraction(data)
	else:
		# Отобразить статус одного валидатора
		data = GetOneStatus(userId, inputItem)
		output = Status2Text(data)
	#end if

	SendMessage(chatId, output)
#end define

def GetMyStatus(userId):
	'''Отобразить статусы своих валидаторов'''
	userLabels = GetUserLabels(userId)
	userAdnlList = GetUserAdnlList(userId)
	result = list()
	for adnlAddr in userAdnlList:
		data = GetValidatorStatus(adnlAddr)
		data["label"] = userLabels.get(adnlAddr)
		result.append(data)
	return result
#end define

def GetAllStatus(userId):
	'''Отобразить статусы всех валидаторов'''
	userLabels = GetUserLabels(userId)
	validatorsList = GetValidatorsList()
	result = list()
	for adnlAddr in validatorsList:
		data = GetValidatorStatus(adnlAddr)
		data["label"] = userLabels.get(adnlAddr)
		result.append(data)
	return result
#end define

def GetDiedStatus(userId):
	'''Отобразить статусы мертвых валидаторов'''
	userLabels = GetUserLabels(userId)
	validatorsList = GetValidatorsList()
	result = list()
	for adnlAddr in validatorsList:
		data = GetValidatorStatus(adnlAddr)
		data["label"] = userLabels.get(adnlAddr)
		if data["status"] is False:
			result.append(data)
	return result
#end define

def GetOneStatus(userId, inputItem):
	'''Отобразить статус одного валидатора'''
	userLabels = GetUserLabels(userId)
	validatorsList = GetValidatorsList()
	adnlAddr = FindTextInList(validatorsList, inputItem)
	data = GetValidatorStatus(adnlAddr)
	data["label"] = userLabels.get(adnlAddr)
	if adnlAddr is None:
		buff = len(inputItem)
		if buff > 6:
			inputItem = inputItem[buff-6:]
		data["adnlEnding"] = inputItem
	return data
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
	adnlAddr = item.get("adnlAddr")
	adnlEnding = item.get("adnlEnding")
	isValidator = item.get("isValidator")
	isSendTelemetry = item.get("isSendTelemetry")
	isWorking = item.get("isWorking", "unknown")
	efficiency = item.get("efficiency")
	cpuLoad = item.get("cpuLoad")
	netLoad = item.get("netLoad")
	tps = item.get("tps")
	outOfSync = item.get("outOfSync")
	statusIcon = item.get("statusIcon")
	if label:
		output += f"Label:            {label}" + '\n'
	output += f"ADNL:            ...{adnlEnding} `{statusIcon}`" + '\n'
	output += f"Validator:       {isValidator}" + '\n'
	if isValidator:
		output += f"Send telemetry:  {isSendTelemetry}" + '\n'
		output += f"Working:         {isWorking}" + '\n'
		output += f"Efficiency:      {efficiency}" + '\n'
	if isSendTelemetry:
		output += f"Out of sync:     {outOfSync}" + '\n'
		output += f"Cpu load:        {cpuLoad}" + '\n'
		output += f"Net load:        {netLoad}" + '\n'
	output += '\n'
	output = f"`{output}`"
	return output
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

def MessageSender():
	messageSenderList = GetMessageSenderList()
	while len(messageSenderList) > 0:
		item = messageSenderList.pop(0)
		chatId = item.get("chatId")
		text = item.get("text")
		SendMessage(chatId, text)
#end define

def AddMessage(chatId, text):
	if chatId is None:
		return
	messageSenderList = GetMessageSenderList()
	item = dict()
	item["chatId"] = chatId
	item["text"] = text
	messageSenderList.append(item)
#end define

def GetMessageSenderList():
	messageSenderList = local.buffer.get("messageSenderList")
	if messageSenderList is None:
		messageSenderList = list()
		local.buffer["messageSenderList"] = messageSenderList
	return messageSenderList
#end define

def ScanValidators():
	users = GetUsers()
	# print("ScanValidators.users:", json.dumps(users))
	for userId in users:
		ScanUserValidators(userId)
#end define

def ScanUserValidators(userId):
	data = GetMyStatus(userId)
	userAlarmList = GetUserAlarmList(userId)
	# print("ScanUserValidators.data:", json.dumps(data))
	for item in data:
		label = item.get("label", "")
		status = item.get("status")
		adnlAddr = item.get("adnlAddr")
		adnlEnding = item.get("adnlEnding")
		statusIcon = item.get("statusIcon")
		if status is True:
			if adnlAddr in userAlarmList:
				userAlarmList.remove(adnlAddr)
				output = "`[Info]`" + '\n'
				output += f"The validator `...{adnlEnding}` ({label}) has restarted {statusIcon}"
				AddMessage(userId, output)
		elif status is False:
			if adnlAddr not in userAlarmList:
				userAlarmList.append(adnlAddr)
				output = "`[Alarm]`" + '\n'
				output += f"The validator `...{adnlEnding}` ({label}) went down {statusIcon}"
				AddMessage(userId, output)
		#end if
#end define





###
### Start of the program
###

if __name__ == "__main__":
	Init()
	updater = InitBot()
	updater.start_polling()
#end if













