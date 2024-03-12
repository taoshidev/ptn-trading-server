# Copyright © 2024 Taoshi Inc

import logging


class LoggerUtil:

    @staticmethod
    def init_logger():
        # Create a logger
        logger = logging.getLogger('example_logger')

        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(handler)
        return logger
