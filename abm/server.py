#
# Copyright 2020 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#

from .logging import init_logger, logger, DataSetID, ForUser
from .config import Config
from .connector import GenericConnector
from .ticket import ABMTicket
import http.server
import json
import os
import socketserver
from http import HTTPStatus
import pyarrow.flight as fl

class ABMHttpHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.config_path = server.config_path
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    def do_GET(self):
        with Config(self.config_path) as config:
            asset_name = self.path.lstrip('/')
            try:
                asset_conf = config.for_asset(asset_name)
                connector = GenericConnector(asset_conf, logger)
            except ValueError:
                logger.error('asset not found or malformed configuration')
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                return

            dataset = connector.get_dataset()
            if dataset:
                self.send_response(HTTPStatus.OK)
                self.end_headers()
                for line in dataset:
                    self.wfile.write(line + b'\n')
            else:
                self.send_response(HTTPStatus.BAD_REQUEST)
                self.end_headers()

class ABMHttpServer(socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass,
                 config_path):
        self.config_path = config_path
        socketserver.TCPServer.__init__(self, server_address,
                                        RequestHandlerClass)

class ABMFlightServer(fl.FlightServerBase):
    def __init__(self, config_path: str, port: int, *args, **kwargs):
        super(ABMFlightServer, self).__init__(
                "grpc://0.0.0.0:{}".format(port), *args, **kwargs)
        self.config_path = config_path

    def _get_locations(self):
        locations = []
        local_address = os.getenv("MY_POD_IP")
        if local_address:
            locations += "grpc://{}:{}".format(local_address, self.port)
        return locations

    def _get_endpoints(self, tickets, locations):
        endpoints = []
        i = 0
        for ticket in tickets:
            if locations:
                endpoints.append(fl.FlightEndpoint(ticket.toJSON(), [locations[i]]))
                i = (i + 1) % len(locations)
            else:
                endpoints.append(fl.FlightEndpoint(ticket.toJSON(), []))
        return endpoints

    def get_flight_info(self, context, descriptor):
        asset_name = json.loads(descriptor.command)['asset']
        logger.info('getting flight information',
            extra={'command': descriptor.command,
                   DataSetID: asset_name,
                   ForUser: True})

        with Config(self.config_path) as config:
            asset_conf = config.for_asset(asset_name)
            # given the asset configuration, let us determine the schema
            connector = GenericConnector(asset_conf, logger)
            schema = connector.get_schema()

        # Build endpoint to this server
        locations = self._get_locations()

        tickets = [ABMTicket(asset_name)]

        endpoints = self._get_endpoints(tickets, locations)
        return fl.FlightInfo(schema, descriptor, endpoints, -1, -1)

class ABMServer():
    def __init__(self, config_path: str, port: int, loglevel: str, *args, **kwargs):
        with Config(config_path) as config:
            init_logger(loglevel, config.app_uuid)

        server = ABMHttpServer(("0.0.0.0", port), ABMHttpHandler,
                               config_path)
        server.serve_forever()
