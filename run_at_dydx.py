# Copyright © 2024 Taoshi Inc

import json

from dydx_wrapper.dydx_wrapper import dYdXWrapper
from utils.logger_util import LoggerUtil
from utils.order_util import OrderUtil
from utils.time_util import TimeUtil


API_KEY = "xxxx"
RUN_SLEEP_TIME = 60
LEVERAGE = 1

pair_map = {
	"BTCUSD": "BTC-USD",
	"ETHUSD": "ETH-USD"
}

def get_secrets():
	return json.loads(open("secrets.json", "r").read())["secrets"]


if __name__ == "__main__":
	logger = LoggerUtil.init_logger()
	secrets = get_secrets()

	# current infra only works for one miner at a time
	# needs adjusted logic to work for every one as you'll have conflicting positions
	miner_uid = ""

	while True:
		logger.info("starting another check for new orders...")

		new_orders = OrderUtil.get_new_orders(API_KEY, logger)
		dydx_wrapper = dYdXWrapper(secrets["private_key"], secrets["eth_address"], secrets["eth_private_key"])
		if new_orders is not None:
			for new_order in new_orders:
				if new_order["muid"] == miner_uid and new_order["trade_pair_id"] in pair_map:
					# if short abs so not negative
					new_order["leverage"] = abs(new_order["leverage"])
					market = pair_map[new_order["trade_pair_id"]]
					logger.info(f"sending in order for completion [{new_order['order_uuid']}].")
					dydx_wrapper.create_order(new_order, market, logger)
					logger.info(f"order completed.")
					TimeUtil.sleeper(5, "sent order", logger)
		TimeUtil.sleeper(RUN_SLEEP_TIME, "completed request", logger)