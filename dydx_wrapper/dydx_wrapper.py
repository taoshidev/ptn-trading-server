import decimal
import time

from dydx3 import Client
from dydx3.constants import POSITION_STATUS_OPEN, ORDER_SIDE_SELL, MARKET_BTC_USD, MARKET_ETH_USD, MARKET_MATIC_USD, \
	MARKET_ADA_USD, MARKET_DOGE_USD, MARKET_DOT_USD, MARKET_LTC_USD, MARKET_AVAX_USD, MARKET_LINK_USD, MARKET_UNI_USD, \
	MARKET_XLM_USD, MARKET_EOS_USD, MARKET_XTZ_USD, MARKET_XMR_USD, MARKET_SOL_USD, ORDER_SIDE_BUY
from dydx3.constants import ORDER_TYPE_LIMIT

from utils.order_util import OrderUtil


class dYdXWrapper:
	SIZE_DECIMAL = 'size_decimal'
	PRICE_DECIMAL = 'price_decimal'

	order_side_map = {
		"LONG": ORDER_SIDE_BUY,
		"SHORT": ORDER_SIDE_SELL,
		OrderUtil.FLAT: OrderUtil.FLAT
	}

	formatter_map = {
		MARKET_BTC_USD: {
			SIZE_DECIMAL: '0.0000',
			PRICE_DECIMAL: '0'
		},
		MARKET_ETH_USD: {
			SIZE_DECIMAL: '0.00',
			PRICE_DECIMAL: '0.0'
		},
		MARKET_MATIC_USD: {
			SIZE_DECIMAL: '0',
			PRICE_DECIMAL: '0.0000'
		},
		MARKET_ADA_USD: {
			SIZE_DECIMAL: '0',
			PRICE_DECIMAL: '0.000'
		},
		MARKET_DOGE_USD: {
			SIZE_DECIMAL: '10',
			PRICE_DECIMAL: '0.0000'
		},
		MARKET_DOT_USD: {
			SIZE_DECIMAL: '0.0',
			PRICE_DECIMAL: '0.00'
		},
		MARKET_LTC_USD: {
			SIZE_DECIMAL: '0.00',
			PRICE_DECIMAL: '0.0'
		},
		MARKET_AVAX_USD: {
			SIZE_DECIMAL: '0.0',
			PRICE_DECIMAL: '0.00'
		},
		MARKET_LINK_USD: {
			SIZE_DECIMAL: '0.0',
			PRICE_DECIMAL: '0.000'
		},
		MARKET_UNI_USD: {
			SIZE_DECIMAL: '0.0',
			PRICE_DECIMAL: '0.000'
		},
		MARKET_XLM_USD: {
			SIZE_DECIMAL: '0',
			PRICE_DECIMAL: '0.0000'
		},
		MARKET_EOS_USD: {
			SIZE_DECIMAL: '0',
			PRICE_DECIMAL: '0.000'
		},
		MARKET_XTZ_USD: {
			SIZE_DECIMAL: '0',
			PRICE_DECIMAL: '0.000'
		},
		MARKET_XMR_USD: {
			SIZE_DECIMAL: '0.00',
			PRICE_DECIMAL: '0.0'
		},
		MARKET_SOL_USD: {
			SIZE_DECIMAL: '0.0',
			PRICE_DECIMAL: '0.000'
		}
	}

	def __init__(self, private_key, eth_address, eth_private_key):

		self._stark_private_key = private_key
		self._eth_address = eth_address
		self._eth_private_key = eth_private_key

		self._client = Client(host='https://api.dydx.exchange',
		                      stark_private_key=self._stark_private_key,
		                      default_ethereum_address=self._eth_address,
		                      eth_private_key=self._eth_private_key)

	def format_size(self, size, market):
		return decimal.Decimal(size).quantize(decimal.Decimal(self.formatter_map[market][self.SIZE_DECIMAL]),
		                                      rounding=decimal.ROUND_DOWN)

	def get_market_price(self, market):
		return self._client.public.get_markets().data['markets'][market]['indexPrice']

	def get_account_balance(self):
		return self._client.private.get_account().data['account']['equity']

	def get_free_collateral(self):
		return self._client.private.get_account().data['account']['freeCollateral']

	def get_account_position_id(self):
		return self._client.private.get_account().data['account']['positionId']

	def create_order(self, order, market, logger, price_multiplier=float(0)):

		side = dYdXWrapper.order_side_map[order["order_type"]]

		leverage = order["leverage"]

		logger.info(f"creating order with specifications. "
		            f"side: [{side}], "
		            f"leverage: + [{str(leverage)}], "
		            f"price multiplier: [{str(price_multiplier)}]")

		# ensure orders fill
		if price_multiplier == 0:
			if side == ORDER_SIDE_SELL:
				price_multiplier = 0.998
			else:
				price_multiplier = 1.002

		# standard is using free collateral
		market_price = float(self.get_market_price(market))

		account_balance = self.get_account_balance()
		if side == OrderUtil.FLAT:
			curr_position = self.get_position(market)
			size = curr_position['size']
			if curr_position['side'] == ORDER_SIDE_BUY:
				side = ORDER_SIDE_SELL
			elif curr_position['side'] == ORDER_SIDE_SELL:
				side = ORDER_SIDE_BUY
			else:
				logger.warn(f"unrecognized position side [{side}]")
		else:
			size = self.format_size(float(account_balance) / market_price * leverage, market)

		price = decimal.Decimal(market_price * price_multiplier) \
			.quantize(decimal.Decimal(self.formatter_map[market][self.PRICE_DECIMAL]), rounding=decimal.ROUND_DOWN)

		order_type = ORDER_TYPE_LIMIT
		# Post an bid at a price that is unlikely to match.
		order_params = {
			'position_id': self.get_account_position_id(),
			'market': market,
			'side': side,
			'order_type': order_type,
			'post_only': False,
			'size': str(size),
			'price': str(price),
			'limit_fee': '0.0015',
			'expiration_epoch_seconds': time.time() + 840,
		}
		self._client.private.create_order(**order_params)

	def get_position(self, trade_pair):
		positions = self._client.private.get_positions(
			market=trade_pair,
			status=POSITION_STATUS_OPEN
		).data['positions']
		if len(positions) > 0:
			return positions[0]
		else:
			return None
