# Copyright © 2024 Taoshi Inc (edits by sirouk)

import json
import os
import pickle
from typing import Union



class StorageUtil:

	@staticmethod
	def make_dir(d: str) -> None:
		if not os.path.exists(d):
			os.makedirs(d)

	@staticmethod
	def write_to_dir(
			wd: str, data: Union[dict, object], is_pickle: bool = False

	) -> None:
		with open(wd, StorageUtil.get_write_type(is_pickle)) as f:
			pickle.dump(data, f) if is_pickle else f.write(json.dumps(data))
		f.close()

	@staticmethod
	def write_file(
			wd: str, data: Union[dict, object], is_pickle: bool = False

	) -> None:
		StorageUtil.write_to_dir(wd, data, is_pickle)

	@staticmethod
	def get_file(file, is_pickle: bool = False) -> Union[str, object]:
		with open(file, StorageUtil.get_read_type(is_pickle)) as f:
			return pickle.load(f) if is_pickle else f.read()

	@staticmethod
	def get_read_type(is_pickle: bool) -> str:
		return "rb" if is_pickle else "r"

	@staticmethod
	def get_write_type(is_pickle: bool) -> str:
		return "wb" if is_pickle else "w"
