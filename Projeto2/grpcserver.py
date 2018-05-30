import time
import grpc
from concurrent import futures
import crud_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class RemoteServer():
    server = None

    def __init__(self, cmd_map, grpc_port):
        RemoteServer.setup(cmd_map, grpc_port)

    @classmethod
    def setup(cls, cmd_map, grpc_port):
        cls.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        crud_pb2_grpc.add_MapServicer_to_server(cmd_map, cls.server)
        port = f'[::]:{grpc_port}'
        cls.server.add_insecure_port(port)

    def serve(self):
        RemoteServer.server.start()
        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            RemoteServer.server.stop(0)
