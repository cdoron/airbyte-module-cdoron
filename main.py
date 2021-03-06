#
# Copyright 2020 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#
import argparse
from abm.server import ABMServer, ABMFlightServer
from abm.logging import logger
import threading

def init_ABMServer(args):
    ABMServer(args.config, args.port, args.loglevel.upper())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ABM Server')
    parser.add_argument(
        '-p', '--port', type=int, default=8080, help='Listening port')
    parser.add_argument(
        '-a', '--arrowport', type=int, default=8081, help='ArrowListening port')
    parser.add_argument(
        '-c', '--config', type=str, default='/etc/conf/conf.yaml', help='Path to config file')
    parser.add_argument(
        '-l', '--loglevel', type=str, default='warning', help='logging level', 
        choices=['info', 'debug', 'warning', 'error', 'critical'])
    args = parser.parse_args()

    t = threading.Thread(target=init_ABMServer, args=(args,))
    t.start()

    server = ABMFlightServer(args.config, args.arrowport)
    logger.info('AFMFlightServer started')
    server.serve()

    t.join()
