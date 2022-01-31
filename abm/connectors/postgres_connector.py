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
        if 'airbyte' not in config['connection']:
            raise ValueError("'airbyte' field missing from configuration")

        self.config = config['connection']['airbyte']
        if 'connector' not in self.config:
            raise ValueError("'connector' field missing from configuration")

        self.client = docker.from_env()
        self.connector = self.config['connector']
        del self.config['connector']
        self.logger = logger
        if 'port' in self.config and type(self.config['port']) == str:
            self.config['port'] = int(self.config['port'])

    def filter_log(self, lines):
        ret = []
        for line in lines:
            if str(line).find('\\x1b[32mINFO\\x1b[m') == -1 and \
                str(line).find('\\x1b[33mWARN\\x1b[m') == -1:
                ret.append(line)
        return ret

    def run_container(self, command):
        try:
            log = self.client.containers.run(self.connector, command,
                volumes=['/json:/json'], network_mode='host')
            return self.filter_log(log.splitlines())
        except docker.errors.DockerException as e:
            self.logger.error('Running of docker container failed',
                              extra={'error': str(e)})
            return None

    def get_catalog(self, conf_file):
        conf_file.write(json.dumps(self.config).encode('utf-8'))
        conf_file.flush()
        return self.run_container('discover --config ' + conf_file.name)

    def read_stream(self, catalog_dict, conf_file, catalog_file):
        streams = []
        for stream in catalog_dict['catalog']['streams']:
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

        catalog_file.write(json.dumps({'streams': streams}).encode('utf-8'))
        catalog_file.flush()
        return self.run_container('read --config ' + conf_file.name +
                            ' --catalog ' + catalog_file.name)

    def get_dataset(self):
        with tempfile.NamedTemporaryFile(dir='/json') as tmp_config:
            airbyte_catalog = self.get_catalog(tmp_config)
            if not airbyte_catalog:
                return None

            if len(airbyte_catalog) != 1:
                logger.error('Received more than a single response line from connector.')
                return None

            try:
                catalog_dict = json.loads(airbyte_catalog[0])
            except ValueError as err:
                logger.error('Failed to parse AirByte Catalog JSON',
                             extra={'error': str(err)})
                return None

            with tempfile.NamedTemporaryFile(dir='/json') as tmp_configured_catalog:
                return self.read_stream(catalog_dict, tmp_config, tmp_configured_catalog)
