#
# Copyright 2020 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#
import docker

class PostgresConnector:
    def __init__(self, config, logger):
        self.client = docker.from_env()
        self.logger = logger
        self.logger.warn("MOO")

    def check_connection(self):
        pass
