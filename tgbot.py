import requests

from utils.logger_util import LoggerUtil


class TGBot:
	def __init__(self):
		self._api_token = 'xxxx'
		self._chat_id = 'xxxx'
		self._send_url = f'https://api.telegram.org/bot{self._api_token}/sendMessage'

	def send_message(self, payload, logger):
		payload_json = {
			'chat_id': self._chat_id,
			'parse_mode': 'HTML',
			'text': payload
		}

		return_message = requests.post(self._send_url, json=payload_json)
		logger.info(str(return_message))
		return self
