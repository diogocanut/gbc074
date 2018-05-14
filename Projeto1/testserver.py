import server
import json

if __name__ == '__main__':
    with open('config.json') as config:
        data = json.load(config)
    addr = (data['host'], data['port'])

    print("=====================SERVER-SIDE=====================")
    s = server.Server(*addr)
    a, b, c = s.setup_threads()
