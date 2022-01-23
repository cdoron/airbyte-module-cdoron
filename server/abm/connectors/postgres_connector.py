#
# Copyright 2020 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#
import docker
import json
import tempfile

class PostgresConnector:
    def __init__(self, config, logger):
        if 'connection' not in config:
            raise ValueError("'connection' field missing from configuration")
        if 'connector' not in config:
            raise ValueError("'connector' field missing from configuration")

        self.client = docker.from_env()
        self.config = config
        self.logger = logger

    def filter_log(self, lines):
        ret = []
        for line in lines:
            if str(line).find('\\x1b[32mINFO\\x1b[m') == -1 and \
                str(line).find('\\x1b[33mWARN\\x1b[m') == -1:
                ret.append(line)
        return ret

    def run_container(self, command):
        log = self.client.containers.run(self.config['connector'], command,
            volumes=['/json:/json'], network_mode='host')
        return self.filter_log(log.splitlines())

    def get_dataset(self):
        with tempfile.NamedTemporaryFile(dir='/json') as tmp_config:
            tmp_config.write(json.dumps(self.config['connection']).encode('utf-8'))
            tmp_config.flush()
            airbyte_catalog = self.run_container('discover --config ' +
                tmp_config.name)[0]
