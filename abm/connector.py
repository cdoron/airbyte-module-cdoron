#
# Copyright 2020 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#
import docker
import json
import tempfile
import pyarrow as pa

class GenericConnector:
    def __init__(self, config, logger):
        supported_connectors = ['postgres', 'mysql', 'google-sheets', 'us-census', 'file']
        if 'connection' not in config:
            raise ValueError("'connection' field missing from configuration")
        airbyte_conf_key = None
        for key in config['connection']:
            if key in supported_connectors or key.startswith('airbyte-'):
               airbyte_conf_key = key
               break

        if not airbyte_conf_key:
            raise ValueError("airbyte connector configuration missing")

        self.config = config['connection'][airbyte_conf_key]
        if 'connector' not in self.config:
            raise ValueError("'connector' field missing from configuration")

        self.client = docker.from_env()
        self.connector = self.config['connector']
        del self.config['connector']
        self.logger = logger
        if 'port' in self.config and type(self.config['port']) == str:
            self.config['port'] = int(self.config['port'])

    def extract_data(self, line_dict):
        return json.dumps(line_dict['record']['data']).encode('utf-8')

    def filter_reply(self, lines):
        ret = []
        for line in lines:
            try:
               line_dict = json.loads(line)
               if 'type' in line_dict:
                   if line_dict['type'] == 'CATALOG':
                       ret.append(line)
                   elif line_dict['type'] == 'RECORD':
                       ret.append(self.extract_data(line_dict))
            finally:
               continue
        return ret

    def run_container(self, command):
        try:
            reply = self.client.containers.run(self.connector, command,
                volumes=['/json:/json'], network_mode='host')
            return self.filter_reply(reply.splitlines())
        except docker.errors.DockerException as e:
            self.logger.error('Running of docker container failed',
                              extra={'error': str(e)})
            return None

    def get_catalog(self, conf_file):
        conf_file.write(json.dumps(self.config).encode('utf-8'))
        conf_file.flush()
        return self.run_container('discover --config ' + conf_file.name)

    translate = {
        'number': 'INT64',
        'string': 'STRING',
    }

    def get_schema(self, catalog_dict):
        schema = pa.schema({})
        properties = catalog_dict['catalog']['streams'][0]['json_schema']['properties']
        for field in properties:
            schema = schema.append(pa.field(field, self.translate[properties[field]['type'][0]]))
        return schema

    def read_stream(self, catalog_dict, conf_file, catalog_file):
        streams = []
        for stream in catalog_dict['catalog']['streams']:
            stream_dict = {}
            stream_dict['sync_mode'] = 'full_refresh'
            stream_dict['destination_sync_mode'] = 'overwrite'
            stream_dict['stream'] = {}
            stream_dict['stream']['source_defined_cursor'] = False
            stream_dict['stream']['name'] = stream['name']
            if 'namespace' in stream:
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
                self.logger.error('Received more than a single response line from connector.')
                return None

            try:
                catalog_dict = json.loads(airbyte_catalog[0])
            except ValueError as err:
                self.logger.error('Failed to parse AirByte Catalog JSON',
                             extra={'error': str(err)})
                return None

            with tempfile.NamedTemporaryFile(dir='/json') as tmp_configured_catalog:
                return self.read_stream(catalog_dict, tmp_config, tmp_configured_catalog)
