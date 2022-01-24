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
            catalog_json = json.loads(airbyte_catalog)

            streams = []
            for stream in catalog_json['catalog']['streams']:
                stream_dict = {}
                stream_dict['sync_mode'] = 'full_refresh'
                stream_dict['stream'] = {}
                stream_dict['stream']['source_defined_cursor'] = False
                stream_dict['stream']['name'] = stream['name']
                stream_dict['stream']['namespace'] = stream['namespace']
                stream_dict['stream']['supported_sync_modes'] = \
                    stream['supported_sync_modes']
                stream_dict['stream']['json_schema'] = stream['json_schema']
                streams.append(stream_dict)

            with tempfile.NamedTemporaryFile(dir='/json') as tmp_configured_catalog:
                tmp_configured_catalog.write(json.dumps({'streams': streams}).encode('utf-8'))
                tmp_configured_catalog.flush()
                dataset=self.run_container('read --config ' + tmp_config.name +
                            ' --catalog ' + tmp_configured_catalog.name)
        return dataset
