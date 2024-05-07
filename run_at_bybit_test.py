# Copyright © 2024 Taoshi Inc (edits by sirouk)

import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import json
import http.client
import ssl

from utils.logger_util import LoggerUtil
from utils.order_util import OrderUtil
from utils.time_util import TimeUtil
from datetime import datetime, timezone


# Initialize the logger
logger = LoggerUtil.init_logger()

EXCHANGE = "bybit_test"
API_KEY = os.getenv("API_KEY")
RUN_SLEEP_TIME = 3
MAX_LEVERAGE = 1 # trades should be closed if you want to change this
MAX_RANK = 1
CONTINUOUS_TRADE_MODE = False
USE_PAIR_MAP_RANK = True

# current infra only works for one miner at a time
# needs adjusted logic to work for every one as you'll have conflicting positions
# UPDATE: working on a solution to handle multiple miners
#  CONTINUOUS_TRADE_MODE was an attempt at this, but the flaw was shifting rank and no local taken position cache
#  The next solution would be to pass the muid to the bybit layer and keep positions separately with an ID based apprroch, which would allow this to manage multiple positions per asset pair and thererfore multiple miners
pair_map_json = os.getenv("PAIR_MAP_TEST")
pair_map = json.loads(pair_map_json)
logger.info(f"Pair map:\n{pair_map_json}")
#quit()


def get_secrets():
	#return json.loads(open("secrets.json", "r").read())["secrets"]
	return ""


def calculate_gradient_allocation(max_rank):
	# Calculate the gradient allocation for each rank with lower ranks (higher priority) receiving larger portions.

	# Calculate the total weight by summing the inverted rank values
	total_weight = sum(max_rank + 1 - rank for rank in range(1, max_rank + 1))

	# Calculate the allocation for each rank
	allocations = {}
	for rank in range(1, max_rank + 1):
		inverted_rank = max_rank + 1 - rank
		numerator = inverted_rank
		denominator = total_weight
		allocations[rank] = (numerator, denominator)
	
	return allocations


def send_to_bybit(market, order, rank_gradient_allocation, timestamp_utc):
	# Prepare order information
	bybit_order = {
		"symbol": market.upper(),
		"direction": "",
		"action": "",
		"leverage": f"{MAX_LEVERAGE}",  # Assuming leverage is an integer value
		"size": "",
		"priority": "high",
		"takeprofit": "0.0",
		"trailstop": "0.0",
		"order_time": timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
		"order_price": order["price"],
		"position_uuid": order["position_uuid"],
		"muid": order["muid"],
		"muid_rank": order["rank"],
	}

	# Calculate the trade size
	trade_numerator, trade_denominator = rank_gradient_allocation[order["rank"]]

	

	
	# Interpret the order type
	if order["order_type"] == "LONG":

		bybit_order["action"] = "buy"	
		# align leverage with direction	
		order["leverage"] = abs(order["leverage"])

		# Trade size uses ranked allocation
		trade_numerator *= order["leverage"]

	elif order["order_type"] == "SHORT":

		bybit_order["action"] = "sell"
		# align leverage with direction
		order["leverage"] = abs(order["leverage"]) * -1
		
		# Trade size uses ranked allocation
		trade_numerator *= order["leverage"]

	elif order["order_type"] == "FLAT":

		# We do not send flat orders to Bybit, instaed we send the opposite order proprtionate to the leverage
		if USE_PAIR_MAP_RANK:
			position_leverage = OrderUtil.total_leverage_by_position_type(order["position_uuid"], rank_gradient_allocation, order["rank"], EXCHANGE, logger)
		else:
			position_leverage = OrderUtil.total_leverage_by_position_type(order["position_uuid"], rank_gradient_allocation, None, EXCHANGE, logger)

		leverage_sum = position_leverage["LONG"] + position_leverage["SHORT"]

		# Override Direction
		if leverage_sum > 0:
			if CONTINUOUS_TRADE_MODE:
				order["order_type"] = "SHORT"
			bybit_order["action"] = "sell"
		else:
			if CONTINUOUS_TRADE_MODE:
				order["order_type"] = "LONG"
			bybit_order["action"] = "buy"
		
		# Flip leverage sum to negate the position
		order["leverage"] = leverage_sum * -1
		
		# This method is already adjusted for ranked allocation
		trade_numerator = order["leverage"]
	

	# Order Direction
	bybit_order["direction"] = order["order_type"].lower()

	# This will remain the same, adjusted for max leverage "their sandbox"
	trade_denominator *= MAX_LEVERAGE

	bybit_order["size"] = f'{trade_numerator}/{trade_denominator}'


	# Convert the order to a string format
	order_str = json.dumps(bybit_order)
	logger.info(f"Sending order to Dale via Bybit relay: {order_str}")


	# Headers and endpoint with trailing slash
	endpoint = "/bybit-tdale/"
	headers = {'Content-Type': 'application/json'}

	# Create connection and POST
	try:
		conn = http.client.HTTPSConnection("localhost", context=ssl._create_unverified_context())
		conn.request("POST", endpoint, body=order_str, headers=headers)

		# Get the response
		response = conn.getresponse()
		logger.info(f"Status: {response.status}")
		logger.info(f"Response: {response.read().decode()}")

	except http.client.HTTPException as e:
		# Handle specific HTTP exceptions if needed
		logger.error(f"HTTP error occurred: {e}")

	except Exception as e:
		# Handle any other exceptions
		logger.error(f"An error occurred: {e}")

	finally:
		# This block will run whether or not an exception occurred
		conn.close()


	return response


if __name__ == "__main__":
	# to be named: Taoshi SN8 - Dale @ Bybit'
	secrets = get_secrets()

	# Calculate the gradient allocation for each rank
	logger.info(f"Calculating gradient allocation for ranks 1 to {MAX_RANK}...")
	rank_gradient_allocation = calculate_gradient_allocation(MAX_RANK)	
	logger.info(rank_gradient_allocation)

	while True:
		logger.info("starting another check for new orders...")

		new_orders, old_orders = OrderUtil.get_new_orders(API_KEY, EXCHANGE, logger)
		
		if True:

			# Aggregate the account allocation and leverage
			queued_order = {}
			
			# Combine the new and old orders
			all_orders = []
			if old_orders:
				all_orders += old_orders
			if new_orders:
				all_orders += new_orders


			for order in all_orders:

				# Skip if the order is already a FLAT position
				if order["position_type"] == "FLAT" and order["order_type"] != "FLAT":
					#logger.info(f"Skipping order [{order['order_uuid']}] as it is already a FLAT position!")
					continue
			
				if order["position_type"] != "FLAT" and order["order_type"] == "FLAT":
					logger.info(f"Non-Flat Position with Flat Order Type: {order}")
					quit()


				#print(order)
				#quit()

				market, max_rank, allocations = None, None, None

				# Iterate through each element in the trade_pair list
				for trade_pair_element in order["trade_pair"]:

					pair_info = pair_map.get(trade_pair_element)
					if pair_info:
						exchange = pair_info.get("exchange", "")			
						if exchange == EXCHANGE:
							market = pair_info["ticker"]
							max_rank = pair_info.get("max_rank", None)
							allocations = pair_info.get("allocations", None)
							break


				# Check to see if muid is in the allocated muid list
				if market and max_rank and (order["muid"] in allocations or order["rank"] in range(1, max_rank)):
					
					

					# if net leverage is positive, set the multiplier to 1, otherwise -1
	 				# if order["order_type"] == "FLAT":
					# 	if order["position_type"] == "LONG":
					# 		order["leverage"] = 1
					direction = order["order_type"] # LONG, SHORT, FLAT

					# Prepare the order	 				
					if not queued_order.get(market):
						queued_order[market] = {"LONG": {"allocation": {}}, "SHORT": {"allocation": {}}, "FLAT": {"allocation": {}}, "timestamp_utc": datetime.fromtimestamp(order["processed_ms"] / 1000, timezone.utc)}			

					# Size of the trade for each Long and Short positions
					if order["muid"] in allocations:
						# Use the static muid allocation
						queued_order[market][direction]["allocation"][order["muid"]] = allocations[order["muid"]]
					else:
						# Use the rank to calculate the allocation					
						rank_gradient_allocation = calculate_gradient_allocation(max_rank)	
						trade_numerator, trade_denominator = rank_gradient_allocation[order["rank"]]

						# print the numerator and denominator
						logger.info(f"Rank: {order['rank']}, Numerator: {trade_numerator}, Denominator: {trade_denominator}")

						queued_order[market][direction]["allocation"][order["muid"]] = trade_numerator / trade_denominator
						print(queued_order)
						quit()



					# convert processed_ms to a timestamp in UTC
					# if queued order is long and has an allocation with a sum greater than one
					if direction == "LONG" and sum(queued_order[market][direction]["allocation"].values()) > 1:
						logger.info(queued_order)
						quit()
						#continue					
					


					# Proceed with your logic, since a valid market was found
					logger.info(f"New trade to process: {queued_order}")

					TimeUtil.sleeper(1, "sent order", logger)
					#quit()

		TimeUtil.sleeper(RUN_SLEEP_TIME, "completed request", logger)