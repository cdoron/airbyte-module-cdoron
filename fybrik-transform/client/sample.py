#
# Copyright 2020 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#
from timeit import repeat
import pyarrow.flight as fl
import json

# taken from https://github.com/apache/arrow/blob/master/python/pyarrow/tests/test_flight.py#L450
class HttpBasicClientAuthHandler(fl.ClientAuthHandler):
    """An example implementation of HTTP basic authentication."""

    def __init__(self, username, password):
        super().__init__()
        self.basic_auth = fl.BasicAuth(username, password)
        self.token = None

    def authenticate(self, outgoing, incoming):
        auth = self.basic_auth.serialize()
        outgoing.write(auth)
        self.token = incoming.read()

    def get_token(self):
        return self.token

request = {
    "asset": "fybrik-notebook-sample/google-sheets-asset", 
}

def read_from_endpoint(endpoint):
    client = fl.connect("grpc://{}:{}".format(args.host, args.port))
    if args.username or args.password:
        client.authenticate(
                HttpBasicClientAuthHandler(args.username, args.password))
    result: fl.FlightStreamReader = client.do_get(endpoint.ticket)
    print(result.read_all().to_pandas())
    #for s in result:
    #    pass

def read_dataset():
    threads = []
    for endpoint in info.endpoints:
        read_from_endpoint(endpoint)

def main(host, port, num_repeat, username, password):
    global client, info
    client = fl.connect("grpc://{}:{}".format(host, port))
    if username or password:
        client.authenticate(HttpBasicClientAuthHandler(username, password))
    info = client.get_flight_info(
        fl.FlightDescriptor.for_command(json.dumps(request)))

    print("Timing " + str(num_repeat) + " runs of retrieving the dataset:" +
          str(repeat(stmt="read_dataset()",
              setup="from __main__ import read_dataset",
              repeat=num_repeat, number=1)))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='arrow-flight-module sample')
    parser.add_argument(
        '--host', type=str, default='localhost', help='afm hostname')
    parser.add_argument(
        '--port', type=int, default=8080, help='Listening port')
    parser.add_argument(
        '--repeat', type=int, default=3, help='Number of times we measure the time to go over dataset')
    parser.add_argument(
        '--username', type=str, default=None, help='Authentication username')
    parser.add_argument(
        '--password', type=str, default=None, help='Authentication password')
    args = parser.parse_args()

    main(args.host, args.port, args.repeat, args.username, args.password)
