from __future__ import print_function

import grpc

import signalupdate_pb2
import signalupdate_pb2_grpc


def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = signalupdate_pb2_grpc.GreeterStub(channel)
    while True:
        response = stub.SignalUpdate(signalupdate_pb2.UpdateRequest())
        if response.message:
            print(response.message)


if __name__ == '__main__':
    run()
