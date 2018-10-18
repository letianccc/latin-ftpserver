
from v2.ftp.server_ import FTPServer
from .config import *


def main():
    server_addr = (SERVER_IP, SERVER_PORT)
    server = FTPServer()
    server.listen(server_addr)
    server.run()

if __name__ == '__main__':
    main()
