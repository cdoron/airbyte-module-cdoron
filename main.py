#
# Copyright 2020 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#
import argparse
from abm.server import ABMServer
from abm.logging import logger

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ABM Server')
    parser.add_argument(
        '-p', '--port', type=int, default=8080, help='Listening port')
    parser.add_argument(
        '-c', '--config', type=str, default='/etc/conf/conf.yaml', help='Path to config file')
    parser.add_argument(
        '-l', '--loglevel', type=str, default='warning', help='logging level', 
        choices=['info', 'debug', 'warning', 'error', 'critical'])
    args = parser.parse_args()

    server = ABMServer(args.config, args.port, args.loglevel.upper())