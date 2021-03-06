import socket
import six.moves.configparser
import _thread
import bcolors
import os
import _struct
import time
class server(object) :
    CONFIG_PATH = '~/ffgmsconfig.conf'
    DEFAULT_CONF = '''[settings]
# The port that the server should run on
port: 24713 
# The name of your game
game: Overpowered'''

    def start(self):
        self.CONFIG = six.moves.configparser.ConfigParser()
        if(not self.CONFIG.read([os.path.expanduser(server.CONFIG_PATH)])):
            print(bcolors.bcolors.FAIL + "No config file in {}".format(os.path.expanduser(server.CONFIG_PATH)) + bcolors.bcolors.ENDC)
            print("Creating config file in {}".format(os.path.expanduser(server.CONFIG_PATH)))
            file = open(os.path.expanduser(server.CONFIG_PATH), "w")
            file.write(server.DEFAULT_CONF)
            file.close()
            self.CONFIG.read([os.path.expanduser(server.CONFIG_PATH)])
        self.SERVERS = []
        try:
            self.PORT = int(self.CONFIG.get('settings', 'port'))
            self.GAME = self.CONFIG.get('settings', 'game')
        except six.moves.configparser.NoOptionError as error:
            print(bcolors.bcolors.FAIL + 'Config file at settings.conf not configured correctly.' + bcolors.bcolors.ENDC)
            print(error)
            return
        
        print(bcolors.bcolors.BOLD + 'Starting {} matchmaking server on port {}'.format(self.GAME, self.PORT) + bcolors.bcolors.ENDC)

        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.bind(('0.0.0.0', self.PORT))
        self.serversocket.listen(5)

        while 1:
            self.update()

    def update(self):
        # Accepts a socket request
        (clientsocket, address) = self.serversocket.accept()
        # Creates a thread for the request to run on
        self.t = _thread.start_new_thread(self.client_thread, (clientsocket, address, ))

    def client_thread(self, clientSocket, Address):
        print(bcolors.bcolors.OKGREEN + "Player connected from {}".format(Address[0]) + bcolors.bcolors.ENDC)
        request = clientSocket.recv(5)
        print('Recieved request {}'.format(request))
        if(request[0] == 4):
            print('Recieved send request')
            # This request is when the client wants to register their game
            self.SERVERS.append(Address[0])
            print('Added address {} to the index'.format(Address[0]))
            clientSocket.send(b"\x01\x00\x00\x00\x00")

        elif(request[0] == 3):
            print('Recieved get request')
            if(len(self.SERVERS) == 0):
                # This means that there are no servers on the list
                print(bcolors.bcolors.WARNING + 'No servers...' + bcolors.bcolors.ENDC)
                clientSocket.send(b"\x00\x00\x00\x00\x00")
            else:
                # This means there are servers on the list
                # Sends back the address of the first server on the list
                ipstr = self.SERVERS[0].split('.')
                ip = [1]
                for i in ipstr:
                    ip.append(int(i))
                ipbytes = _struct.pack('BBBBB', ip[0], ip[1], ip[2], ip[3], ip[4])
                clientSocket.send(ipbytes)

        elif(request[0] == 5):
            print('Recieved clear request')
            # This means that the server should be removed from the list
            if(len(self.SERVERS)>0):
                adrs = Address[0]
                index = 0
                deleted = 0
                while(index < len(self.SERVERS)):
                    if(self.SERVERS[index] == adrs):
                        deleted += 1
                        self.SERVERS.pop(index)
                        index -= 1
                    index += 1
                print(bcolors.bcolors.OKGREEN + 'cleared {} occurences of {}'.format(deleted, adrs) + bcolors.bcolors.ENDC)

        elif(request[0] == 2):
            print('Recieved status request')
            clientSocket.sendall(b"\x01\x00\x00\x00\x00")
        else:
            print('Invalid command.')
        print('Sent response')
        clientSocket.close()
        print('Closing thread')
        return