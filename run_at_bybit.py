# Copyright © 2024 Taoshi Inc (edits by sirouk)

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


import json
import http.client
import ssl

from utils.logger_util import LoggerUtil
from utils.order_util import OrderUtil
from utils.time_util import TimeUtil
from datetime import datetime, timezone


API_KEY = os.getenv("API_KEY")
RUN_SLEEP_TIME = 3
MAX_LEVERAGE = 3 # trades should be closed if you want to change this
MAX_RANK = 10

# current infra only works for one miner at a time
# needs adjusted logic to work for every one as you'll have conflicting positions
top_miner_uid = os.getenv("TOP_MINER_UID")

pair_map = {
	"BTCUSD": "BTCUSDT",
	"ETHUSD": "ETHUSDT"
}



def get_secrets():
	#return json.loads(open("secrets.json", "r").read())["secrets"]
	return ""


def calculate_gradient_allocation(max_rank):
    """
    Calculate the gradient allocation for each rank with lower ranks (higher priority) receiving larger portions.
	100 can be changed to adjust max portfolio utilization if doing that at this level is desired.

    Returns:
    A dictionary with each rank's allocation as a fraction (numerator, denominator).
    """
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


def send_to_bybit(market, order, rank_gradient_allocation):
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
		if order["leverage"] < 0:
			order["leverage"] *= -1

		# Trade size uses ranked allocation
		trade_numerator *= order["leverage"]

	elif order["order_type"] == "SHORT":

		bybit_order["action"] = "sell"
		if order["leverage"] > 0:
			order["leverage"] *= -1
		
		# Trade size uses ranked allocation
		trade_numerator *= order["leverage"]

	elif order["order_type"] == "FLAT":

		# We do not send flat orders to Bybit, instaed we send the opposite order proprtionate to the leverage
		position_leverage = OrderUtil.total_leverage_by_position_type(order["position_uuid"], rank_gradient_allocation, logger)
		leverage_sum = position_leverage["LONG"] + position_leverage["SHORT"]
		# Override Direction
		if leverage_sum > 0:
			order["order_type"] = "SHORT"
			bybit_order["action"] = "sell"
		else:
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
	logger = LoggerUtil.init_logger()
	secrets = get_secrets()

	# Calculate the gradient allocation for each rank
	print(f"Calculating gradient allocation for ranks 1 to {MAX_RANK}...")
	rank_gradient_allocation = calculate_gradient_allocation(MAX_RANK)	
	print(rank_gradient_allocation)

	while True:
		logger.info("starting another check for new orders...")

		new_orders = OrderUtil.get_new_orders(API_KEY, logger)
		
		if new_orders is not None:
			for new_order in new_orders:
				#print(new_order)
				#quit()
				
				new_order["leverage"] = abs(new_order["leverage"])

				if (new_order["rank"] <= MAX_RANK or new_order["muid"] == top_miner_uid) and new_order["leverage"] <= MAX_LEVERAGE:
					
					# Initialize market as None
					market = None

					# Iterate through each element in the trade_pair list
					for trade_pair_element in new_order["trade_pair"]:
						if trade_pair_element in pair_map:
							# If a match is found, use the corresponding value from pair_map
							market = pair_map[trade_pair_element]
							break  # Exit the loop once a match is found
					
					#print(market)
					#quit()

					# Check if a market was found
					if market is not None:
						# Proceed with your logic, since a valid market was found
						logger.info(f"sending in order for completion [{new_order['order_uuid']}].")
						logger.info(f"New trade to process: {new_order, market, logger}")
						
						# convert processed_ms to a timestamp in UTC
						timestamp_utc = datetime.fromtimestamp(new_order["processed_ms"] / 1000, timezone.utc)
						print(timestamp_utc)

						send_to_bybit(market, new_order, rank_gradient_allocation)
						#quit()

						# Remember to replace or remove the quit() call as needed for your application logic
						
					else:
						# Handle the case where no match was found
						logger.info(f"No valid trade pair found for order [{new_order['order_uuid']}].")

					logger.info(f"order completed.")
					TimeUtil.sleeper(5, "sent order", logger)
		TimeUtil.sleeper(RUN_SLEEP_TIME, "completed request", logger)