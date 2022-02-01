#
# Copyright 2020 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#

from .logging import init_logger, logger
from .config import Config
from .connector import GenericConnector
import http.server
import socketserver
from http import HTTPStatus

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

class ABMServer():
    def __init__(self, config_path: str, port: int, loglevel: str, *args, **kwargs):
        with Config(config_path) as config:
            init_logger(loglevel, config.app_uuid)

        server = ABMHttpServer(("0.0.0.0", port), ABMHttpHandler,
                               config_path)
        server.serve_forever()
