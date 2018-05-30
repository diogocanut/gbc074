import json
import grpc
import threading

import crud_pb2
import crud_pb2_grpc


class RemoteClient:
    def __init__(self, host, port):
        self.addr = f"{host}:{port}"
        self.channel = grpc.insecure_channel(self.addr)
        self.stub = crud_pb2_grpc.MapStub(self.channel)
        self.tracked = None

    def setup_threads(self):
        input_thread = threading.Thread(name='input_thread',
                                        target=self.process_input)
        input_thread.start()
        track_thread = threading.Thread(name='output_thread',
                                        target=self.track)
        track_thread.start()

        return input_thread, track_thread

    def process_value(self, cmd):
        value = ''
        if cmd in ['create', 'update']:
            value = input("Type a value for your key:")
            while(len(value.encode('utf-8')) > 1450):
                print('Value cannot exceed 1400 bytes!')
                value = input()
        return value

    def process_key(self):
        print('Type your key:')
        while True:
            key = input()
            try:
                int(key)
            except ValueError:
                print("Key must be an integer!")

            # Smallest 'int' object is of size 24 bytes
            # For that reason I am considering 24 + 20 bytes for key size check
            if int(key) < (2 ** 150):
                return int(key)
            else:
                print('Key cannot exceed 20 bytes!')

    def process_cmd(self):
        cmd = ''
        valid_ops = ['create', 'read', 'update', 'delete', 'track']

        cmd = input('Create, Read, Update, Delete or Track?\n').lower()
        while cmd not in valid_ops:
            print('Invalid operation!')
            cmd = input().lower()
        return cmd

    def process_input(self):
        response = ''
        while True:
            cmd = self.process_cmd()
            key = self.process_key()
            value = self.process_value(cmd)

            if cmd in ['read', 'delete']:
                response = self.stub.Crud(crud_pb2.CommandRequest(name=cmd,
                                                                  key=key))
            if cmd in ['create', 'update']:
                response = self.stub.Crud(crud_pb2.CommandRequest(name=cmd,
                                                                  key=key,
                                                                  value=value))
            if cmd == 'track':
                self.tracked = key
                response = self.stub.Crud(crud_pb2.CommandRequest(name=cmd, key=key))
            if response:
                    print(response.message)

    def track(self):
        while True:
            responses = None
            key = self.tracked
            if key:
                responses = self.stub.Track(crud_pb2.TrackReq(key=self.tracked))
                if responses:
                    for reply in responses:
                        print(reply.message)


if __name__ == '__main__':
    print("=====================GRPC-CLIENT=====================")
    with open('config.json') as config:
        data = json.load(config)
    host = data['host']
    port = data['grpc_port']

    client = RemoteClient(host, port)
    in_thread, track_thread = client.setup_threads()
