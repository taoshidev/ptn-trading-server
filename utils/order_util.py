from typing import List, Dict

from utils.logger_util import LoggerUtil
import json
import requests

from utils.storage_util import StorageUtil
from utils.time_util import TimeUtil


class OrderUtil:
	URL = "http://127.0.0.1:80/miner-positions"

	MINER_POSITIONS_DIR = "miner_positions/"
	MINER_POSITIONS_FILE = "miner_positions.json"
	MINER_POSITION_LOCATION = MINER_POSITIONS_DIR + MINER_POSITIONS_FILE

	FLAT = "FLAT"


	@staticmethod
	def get_new_miner_positions(api_key):
		# Pass API key
		data = {
			'api_key': api_key
		}
		# Convert the Python dictionary to JSON format
		json_data = json.dumps(data)
		# Set the headers to specify that the content is in JSON format
		headers = {
			'Content-Type': 'application/json',
		}
		# Make the GET request with JSON data
		return requests.get(OrderUtil.URL, data=json_data, headers=headers)


	@staticmethod
	def get_flattened_order_map(data):
		flattened_order_map = {}
		unique_order_uuids = set()
		_rank = 0
		for _muid, _ps in data.items():
			_rank += 1
			for _p in _ps["positions"]:
				# if position has been flat for more than 30 minutes ignore its orders
				if _p["position_type"] != OrderUtil.FLAT or (_p["position_type"] == OrderUtil.FLAT and _p[
					"close_ms"] > TimeUtil.now_in_millis() - TimeUtil.minute_in_millis(30)):
					for order in _p["orders"]:
						order["position_uuid"] = _p["position_uuid"]
						order["net_leverage"] = _p["net_leverage"]
						order["rank"] = _rank
						order["muid"] = _muid
						flattened_order_map[order["order_uuid"]] = order
						unique_order_uuids.add(order["order_uuid"])
		return flattened_order_map, unique_order_uuids


	@staticmethod
	def get_new_orders(api_key, logger) -> List[Dict]:
		response = OrderUtil.get_new_miner_positions(api_key)

		# Check if the request was successful (status code 200)
		if response.status_code == 200:
			logger.debug("GET request was successful.")
			new_miner_positions_data = json.loads(response.json())
		else:
			logger.debug(response.__dict__)
			logger.debug("GET request failed with status code: " + response.status_code)
			return None

		# get the response data, if it doesnt exist store it.
		# if it does exist compare it to see if theres any new trades
		# if theres a new order place it in TG

		# safely create the dir if it doesnt exist already
		StorageUtil.make_dir(OrderUtil.MINER_POSITIONS_DIR)

		try:
			miner_positions_data = StorageUtil.get_file(OrderUtil.MINER_POSITION_LOCATION)
			miner_positions_data = json.loads(miner_positions_data)
		except FileNotFoundError:
			logger.debug("miner positions data doesn't exist")
			miner_positions_data = None

		if miner_positions_data is None:
			logger.info("no miner positions file exists, sending all existing orders.")
			# send in all orders if miner positions data doesn't exist
			new_orders, new_order_uuids = OrderUtil.get_flattened_order_map(new_miner_positions_data)
			StorageUtil.write_file(OrderUtil.MINER_POSITION_LOCATION, new_miner_positions_data)
			logger.info(f"new order uuids to send : [{new_order_uuids}]")
			logger.info("updating miner positions file.")
			return [new_order for order_uuid, new_order in new_orders.items()]
		else:
			# compare data against existing and if theres differences send in
			new_orders, new_order_uuids = OrderUtil.get_flattened_order_map(new_miner_positions_data)
			orders, order_uuids = OrderUtil.get_flattened_order_map(miner_positions_data)

			logger.debug(f"new order uuids : [{new_order_uuids}]")
			logger.debug(f"existing order uuids : [{order_uuids}]")

			new_order_uuids_to_send = [value for value in new_order_uuids if value not in order_uuids]
			logger.info(f"new order uuids to send : [{new_order_uuids_to_send}]")
			logger.info("updating miner positions file.")
			StorageUtil.write_file(OrderUtil.MINER_POSITION_LOCATION, new_miner_positions_data)
			return [new_orders[order_uuid] for order_uuid in new_order_uuids_to_send]