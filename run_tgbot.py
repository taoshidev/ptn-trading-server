from utils.logger_util import LoggerUtil
from utils.order_util import OrderUtil
from tgbot import TGBot
from utils.time_util import TimeUtil


API_KEY = "xxxx"
RUN_SLEEP_TIME = 60


def get_new_miner_order(_flattened_order):
	order_position_net_leverage = _flattened_order["net_leverage"]
	order_trade_pair = _flattened_order["trade_pair"]["trade_pair_id"]
	order_type = _flattened_order["order_type"]
	if order_type == OrderUtil.FLAT:
		order_leverage = "N/A"
	else:
		order_leverage = _flattened_order["leverage"]
	price = _flattened_order["price"]
	_rank = _flattened_order["rank"]
	_m = _flattened_order["muid"]

	payload = f"Miner ID: {_m} \n " \
	          f"Position Type: {order_position_net_leverage} \n " \
	          f"Position Net Leverage: {order_position_net_leverage} \n " \
	          f"Rank: {_rank} \n " \
	          f"Order Trade Pair: {order_trade_pair} \n " \
	          f"Order Type: {order_type} \n " \
	          f"Order Leverage: {order_leverage} \n " \
	          f"Order Price: {price}"
	return payload


def send_new_miner_order(_new_order, logger, add_sleep=True):
	nmo = get_new_miner_order(_new_order)
	TGBot().send_message(nmo, logger)
	if add_sleep:
		# standardized sleep time between messages
		TimeUtil.sleeper(5, "new_miner_order", logger)


if __name__ == "__main__":
	logger = LoggerUtil.init_logger()
	while True:
		logger.info("starting another check for new orders...")
		new_orders = OrderUtil.get_new_orders(API_KEY, logger)
		if new_orders is not None:
			for new_order in new_orders:
				send_new_miner_order(new_order, logger)
		TimeUtil.sleeper(RUN_SLEEP_TIME, "completed request", logger)