import crud_pb2
import crud_pb2_grpc


class Map(crud_pb2_grpc.MapServicer):
    def __init__(self):
        self.cmd_map = {}
        self.tracked = {}
        self.read_map_log()

    def exec_cmd(self, operation, key, value):
        key_in_map = self.cmd_map.get(key)
        success = False
        result = ''

        if operation == 'track' and key not in self.tracked:
            self.tracked.update({key: []})
            success = True
        elif operation == 'create' and not key_in_map:
            self.cmd_map.update({key: value})
            success = True
        elif operation != 'create' and key_in_map:
            if operation == 'read':
                value = key_in_map
            elif operation == 'update':
                self.cmd_map.update({key: value})
            elif operation == 'delete':
                value = key_in_map
                self.cmd_map.pop(key)
            success = True

        log_entry = f'{operation} {{{key}: {value}}}'
        if success:
            result = f'success: {log_entry}'
        else:
            result = f'failed to {operation} key {key}.'

        if key in self.tracked:
            self.tracked[key].append(result)
        return success, result

    def Crud(self, request, context):
        print(context.peer())
        op = request.name
        key = request.key
        value = request.value
        success, result = self.exec_cmd(op, key, value)
        return crud_pb2.CommandReply(message=result)
        self.write_log()

    def Track(self, request, context):
        print(dict(context.invocation_metadata()))
        updates = self.tracked[request.key]
        while True:
            if updates:
                for command in updates:
                    updates.pop(0)
                    yield crud_pb2.CommandReply(message=command)
            else:
                continue

    def write_log(self):
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
