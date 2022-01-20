#
# Copyright 2020 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#

from abm.logging import init_logger

from .config import Config

class ABMServer():
    def __init__(self, config_path: str, port: int, loglevel: str, *args, **kwargs):
        with Config(config_path) as config:
            init_logger(loglevel, config.app_uuid)
            self.config_path = config_path

    def serve(self):
        pass
