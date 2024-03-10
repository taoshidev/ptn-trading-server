import requests

from utils.output_util import OutputUtil


class TGBot:
	def __init__(self):
		self._api_token = 'xxxx'
		self._chat_id = 'xxxx'
		self._send_url = f'https://api.telegram.org/bot{self._api_token}/sendMessage'

	def send_message(self, payload):
		payload_json = {
			'chat_id': self._chat_id,
			'parse_mode': 'HTML',
			'text': payload
		}

		return_message = requests.post(self._send_url, json=payload_json)
		OutputUtil.output(str(return_message))
		return self
