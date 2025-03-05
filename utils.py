#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import time
import json
import urllib.request
from mypylib.mypylib import Dict, get_timestamp


def read_file(file_path):
	with open(file_path, "rt") as file:
		text = file.read()
	return text
#end define

def get_config(config_path):
	text = read_file(config_path)
	data = json.loads(text)
	return Dict(data)
#end define

def try_get_url(url):
	for i in range(3):
		try:
			data = get_url(url)
			return data
		except Exception as ex:
			err = ex
			time.sleep(1)
	raise Exception(f"try_get_url error: {err}")
#end define

def get_url(url):
	req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
	conn = urllib.request.urlopen(req)
	data = conn.read()
	text = data.decode()
	return text
#end define

def with_buffer(local, func, *args, **kwargs):
	# Get buffer
	buffer_hash = hash(f"{args}_{kwargs}")
	buffer_name = f"{func.__name__}_{buffer_hash}"
	buff = get_function_buffer(local, buffer_name, timeout=60)
	if buff:
		return buff
	#end if

	# Run function
	result = func(*args, **kwargs)

	# Set buffer
	set_function_buffer(local, buffer_name, result)
	return result
#end define

def get_function_buffer(local, buffer_name, timeout=10):
	timestamp = get_timestamp()
	buff = local.buffer.get(buffer_name)
	if buff is None:
		return
	buff_time = buff.get("time")
	diff_time = timestamp - buff_time
	if diff_time > timeout:
		return
	data = buff.get("data")
	return data
#end define

def set_function_buffer(local, buffer_name, data):
	buff = dict()
	buff["time"] = get_timestamp()
	buff["data"] = data
	local.buffer[buffer_name] = buff
#end define

def find_text_in_list(inputList, text):
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

def get_item_from_list(input_args, index=0):
	try:
		input_item = input_args[index]
	except:
		input_item = None
	return input_item
#end define

def get_dict_from(db_or_buffer, name):
	users = db_or_buffer.get(name)
	if users is None:
		users = Dict()
		db_or_buffer[name] = users
	return users
#end define

def get_adnl_text(user, adnl_addr):
	user_labels = user.get_labels()
	label = user_labels.get(adnl_addr)
	label_text = f" ({label})" if label else ''
	adnl_short = adnl_addr[0:6] + "..." + adnl_addr[58:64]
	adnl_text = f"{adnl_short}{label_text}"
	return adnl_text
#end define

def collect_template(local, template_name, **kwargs):
	template = local.buffer.templates.get(template_name)
	return template.format(**kwargs)
#end define

def class_list2str_list(class_list):
	result = list()
	for item in class_list:
		class_name = type(item).__name__
		result.append(class_name)
	return result
#end define

def amount_formatting(amount):
	return f"{amount:,}".replace(',', ' ')
#end define
