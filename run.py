import json
import time

import requests

from utils.storage_util import StorageUtil
from tgbot import TGBot
from utils.time_util import TimeUtil

import logging

# Create a logger
logger = logging.getLogger('example_logger')

logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

API_KEY = "xxxx"

# TODO - update to prod when ready
# test url
URL = "http://127.0.0.1:80/miner-positions"

MINER_POSITIONS_DIR = "miner_positions/"
MINER_POSITIONS_FILE = "miner_positions.json"
MINER_POSITION_LOCATION = MINER_POSITIONS_DIR + MINER_POSITIONS_FILE

FLAT = "FLAT"
RUN_SLEEP_TIME = 60


def get_new_miner_positions():
	# Pass API key
	data = {
		'api_key': API_KEY
	}
	# Convert the Python dictionary to JSON format
	json_data = json.dumps(data)
	# Set the headers to specify that the content is in JSON format
	headers = {
		'Content-Type': 'application/json',
	}
	# Make the GET request with JSON data
	return requests.get(URL, data=json_data, headers=headers)


def get_new_miner_order(_flattened_order):
	order_position_net_leverage = _flattened_order["net_leverage"]
	order_trade_pair = _flattened_order["trade_pair"]["trade_pair_id"]
	order_type = _flattened_order["order_type"]
	if order_type == FLAT:
		order_leverage = "N/A"
	else:
		order_leverage = _flattened_order["leverage"]
	price = _flattened_order["price"]
	_rank = _flattened_order["rank"]
	_m = _flattened_order["muid"]

	payload = f"Miner ID: {_m} \n " \
	          f"Position Net Leverage: {order_position_net_leverage} \n " \
	          f"Rank: {_rank} \n " \
	          f"Order Trade Pair: {order_trade_pair} \n " \
	          f"Order Type: {order_type} \n " \
	          f"Order Leverage: {order_leverage} \n " \
	          f"Order Price: {price}"
	return payload


def sleeper(sleeper_time, subject):
	logger.debug(f"sleeper called for [{subject}]...")
	time.sleep(sleeper_time)
	logger.debug( f"sleeper done for [{subject}].")


def send_new_miner_order(_new_order, add_sleep=True):
	nmo = get_new_miner_order(_new_order)
	TGBot().send_message(nmo)
	if add_sleep:
		# standardized sleep time between messages
		sleeper(5, "new_miner_order")


def get_flattened_order_map(data):
	flattened_order_map = {}
	unique_order_uuids = set()
	_rank = 0
	for _muid, _ps in data.items():
		_rank += 1
		for _p in _ps["positions"]:
			# if position has been flat for more than 30 minutes ignore its orders
			if _p["position_type"] != FLAT or (_p["position_type"] == FLAT and _p[
				"close_ms"] > TimeUtil.now_in_millis() - TimeUtil.minute_in_millis(30)):
				for order in _p["orders"]:
					order["position_uuid"] = _p["position_uuid"]
					order["net_leverage"] = _p["net_leverage"]
					order["rank"] = _rank
					order["muid"] = _muid
					flattened_order_map[order["order_uuid"]] = order
					unique_order_uuids.add(order["order_uuid"])
	return flattened_order_map, unique_order_uuids


if __name__ == "__main__":

	while True:
		logger.info("starting another check for new orders...")

		response = get_new_miner_positions()

		# Check if the request was successful (status code 200)
		if response.status_code == 200:
			logger.debug( "GET request was successful.")
			new_miner_positions_data = json.loads(response.json())
		else:
			logger.debug( response.__dict__)
			logger.debug( "GET request failed with status code: " + response.status_code)
			sleeper(RUN_SLEEP_TIME, "failed request")
			continue

		# get the response data, if it doesnt exist store it.
		# if it does exist compare it to see if theres any new trades
		# if theres a new order place it in TG

		# safely create the dir if it doesnt exist already
		StorageUtil.make_dir(MINER_POSITIONS_DIR)

		try:
			miner_positions_data = StorageUtil.get_file(MINER_POSITION_LOCATION)
			miner_positions_data = json.loads(miner_positions_data)
		except FileNotFoundError:
			logger.debug( "miner positions data doesn't exist")
			miner_positions_data = None

		if miner_positions_data is None:
			# send in all orders if miner positions data doesnt exist
			new_orders, new_order_uuids = get_flattened_order_map(new_miner_positions_data)
			for order_uuid, new_order in new_orders.items():
				send_new_miner_order(new_order)
		else:
			# compare data against existing and if theres differences send in
			new_orders, new_order_uuids = get_flattened_order_map(new_miner_positions_data)
			orders, order_uuids = get_flattened_order_map(miner_positions_data)

			logging.debug(f"new order uuids : [{new_order_uuids}]")
			logging.debug(f"existing order uuids : [{order_uuids}]")

			new_order_uuids_to_send = [value for value in new_order_uuids if value not in order_uuids]

			logging.info(f"new order uuids to send : [{new_order_uuids_to_send}]")

			for order_uuid in new_order_uuids_to_send:
				send_new_miner_order(new_orders[order_uuid])
		StorageUtil.write_file(MINER_POSITION_LOCATION, new_miner_positions_data)

		sleeper(RUN_SLEEP_TIME, "completed request")
