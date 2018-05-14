import socket
import threading
import time
import grpc
from queue import Queue
from concurrent import futures

import helloworld_pb2
import helloworld_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class Greeter(helloworld_pb2_grpc.GreeterServicer):

    def SayHello(self, request, context):
        return helloworld_pb2.HelloReply(message='Hello, %s!' % request.name)


class Server:
    _sock = None

    def __init__(self, host, port):
        Server.setup_socket(host, port)
        self.host = host
        self.port = port
        self.flag = True
        self.cmd_queue = Queue()
        self.exec_queue = Queue()
        self.log_queue = Queue()
        self.cmd_map = {}
        self.read_map_log()

    @classmethod
    def setup_socket(cls, host, port):
        cls._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cls._sock.bind((host, port))

    def setup_threads(self):
        recv_thread = threading.Thread(name='recv_thread',
                                       target=self.recv_cmd)
        recv_thread.start()
        exec_thread = threading.Thread(name='process_thread',
                                       target=self.process_cmd)
        exec_thread.start()

        grpc_thread = threading.Thread(
            name='grpc_thread',
            target=self.serve
        )

        grpc_thread.start()

        return recv_thread, exec_thread, grpc_thread

    def write_cmd_log(self, result):
        if self.log_queue.empty():
            return
        req = self.log_queue.get()
        origin = req[0]
        cmd = req[1][0]
        key = req[1][1]

        with open('cmd.log', 'a') as cmd_log:
            if result:
                cmd_log.write(f'{origin}: success: {cmd} key {key}\n')
            else:
                cmd_log.write(f'{origin}: failed to {cmd} key {key}\n')

    def write_map_log(self):
        with open('map.log', 'w') as logfile:
            for key in self.cmd_map.keys():
                logfile.write(f'{key} {self.cmd_map[key]}\n')

    def read_map_log(self):
        with open('map.log') as logfile:
            for line in logfile:
                line = line.split()
                if len(line) >= 2:
                    line[1] = ' '.join([i for i in line if line.index(i) > 0])
                self.cmd_map.update({int(line[0]): line[1]})

    def recv_cmd(self):
        while True:
            data, addr = self._sock.recvfrom(1400)
            print(f"Receiving request from {addr}")
            data = data.decode('utf-8').split()
            print(data)

            data[1] = int(data[1])
            if len(data) > 2:
                data[2] = ' '.join([i for i in data if data.index(i) >= 2])

            self.cmd_queue.put((addr, data))

    def process_cmd(self):
        while True:
            if not self.cmd_queue.empty():
                return
            self.flag = False
            next_cmd = self.cmd_queue.get()
            self.exec_queue.put(next_cmd)
            self.log_queue.put(next_cmd)
            result = self.exec_cmd()
            self.write_cmd_log(result)
            self.flag = True

    def exec_cmd(self):
        if self.exec_queue.empty():
            return

        result = ''
        dequeue = self.exec_queue.get()
        success = 0
        entry = dequeue[1]
        key = entry[1]
        value = ''
        key_exists = self.cmd_map.get(key)

        if len(entry) > 2:
            value = entry[2]

        if entry[0] == 'create' and not key_exists:
            self.cmd_map.update({key: value})
            success = 1

        if key_exists:
            if entry[0] == 'read':
                value = key_exists
                success = 1
            elif entry[0] == 'update':
                self.cmd_map.update({key: value})
                success = 1
            elif entry[0] == 'delete':
                value = key_exists
                self.cmd_map.pop(key)
                success = 1

        log_entry = f'{entry[0]} {{{key}: {value}}}'
        if success:
            result = f'success: {log_entry}'
        else:
            result = f'failed to {entry[0]} key {key}.'
        print(result)
        self._sock.sendto(result.encode('utf-8'), dequeue[0])
        self.write_map_log()
        return success

    def serve(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
        server.add_insecure_port('[::]:50051')
        server.start()
        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            server.stop(0)
