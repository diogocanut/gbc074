import socket
import threading
from queue import Queue

from dictmap import Map
from grpcserver import RemoteServer

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class Server:
    _sock = None

    def __init__(self, host='localhost', port=8000, grpc_port=50051):
        Server.setup_socket(host, port)
        self.cmd_map = Map()
        self.grpc = RemoteServer(self.cmd_map, grpc_port)
        self.flag = True

        self.host = host
        self.port = port

        self.cmd_queue = Queue()
        self.exec_queue = Queue()
        self.log_queue = Queue()

        self.tracked = set()

        self.read_map_log()

    @classmethod
    def setup_socket(cls, host, port):
        cls._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cls._sock.bind((host, port))

    def setup_threads(self):
        recv_thread = threading.Thread(name='recv_thread',
                                       target=self.recv_cmd)
        recv_thread.start()
        exec_thread = threading.Thread(name='queues_thread',
                                       target=self.organize_queues)
        exec_thread.start()

        grpc_thread = threading.Thread(name='grpc_thread',
                                       target=self.grpc.serve)
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

    def read_map_log(self):
        with open('map.log') as logfile:
            for line in logfile:
                line = line.split()
                if len(line) >= 2:
                    line[1] = ' '.join([i for i in line if line.index(i) > 0])
                self.cmd_map.cmd_map.update({int(line[0]): line[1]})

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

    def organize_queues(self):
        while True:
            if not self.cmd_queue.empty():
                return

            self.flag = False

            next_cmd = self.cmd_queue.get()
            self.exec_queue.put(next_cmd)
            self.log_queue.put(next_cmd)
            result = self.process_cmd()
            self.write_cmd_log(result)

            self.flag = True

    def process_cmd(self):
        if self.exec_queue.empty():
            return

        command = self.exec_queue.get()
        origin = command[0]
        entry = command[1]

        operation = entry[0]
        key = entry[1]
        value = entry[2] if len(entry) > 2 else ''
        success, result = self.cmd_map.exec_cmd(operation, key, value)
        print(result)

        self._sock.sendto(result.encode('utf-8'), origin)
        self.cmd_map.write_log()
        return success
