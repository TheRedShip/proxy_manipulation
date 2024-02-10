import socket
import threading
import select

VERSION = b'\x05\x00\x00'
CMD_CONNECT = 0x01
ATYP_IPV4 = 0x01
ATYP_DOMAINNAME = 0x03

class Socks5:
	def __init__(self, listen_address, listen_port):
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind((listen_address, listen_port))
		self.server.listen(5)

		self.remote_list = []

		self.on_connect = None
		self.on_disconnect = None
		self.on_sending = None
		self.on_receiving = None
		
		print("Listening on", listen_address, listen_port)

	def run_handler(self, handler, *args):
		if (handler != None):
			return handler(*args)

	def get_host_from_type(self, client_socket):
		host_type = client_socket.recv(1)[0]
		if (host_type == ATYP_IPV4):
			adress = client_socket.recv(4)
			return adress, host_type
		elif (host_type == ATYP_DOMAINNAME):
			host_length = client_socket.recv(1)[0]
			adress = client_socket.recv(host_length)
			return adress, host_type
		
	def handle_tcp(self, client_socket, remote_socket, host):
		while True:
			try:
				reader, _, _ = select.select([client_socket, remote_socket], [], [], 1)
			except select.error as err:
				return
			if not reader:
				continue
			try:
				for sock in reader:
					data = sock.recv(2048)
					if not data:
						return
					if sock is remote_socket:
						new_data = self.run_handler(self.on_receiving, remote_socket, data)
						if new_data is None:
							new_data = data
						client_socket.send(new_data)
					else:
						new_data = self.run_handler(self.on_sending, remote_socket, data)
						if new_data is None:
							new_data = data
						remote_socket.send(new_data)
			except socket.error as err:
				return

	def handle_client(self, client_socket):
		initial_request = client_socket.recv(8)
		auths_method = [method for method in initial_request[2:]]

		if 0 in auths_method:
			client_socket.send(b'\x05\x00')

			response = client_socket.recv(3)

			command = response[1]
			host, host_type = self.get_host_from_type(client_socket)
			port = int.from_bytes(client_socket.recv(2), "big")
			realip = None

			if command == CMD_CONNECT:	
				if (host_type == ATYP_IPV4):
					realip = socket.inet_ntoa(host)
					remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					remote_socket.connect((realip, port))
					client_socket.send(VERSION + b'\x01' + host + port.to_bytes(2, "big"))

				elif (host_type == ATYP_DOMAINNAME):
					realip = host.decode()
					remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					remote_socket.connect((realip, port))
					client_socket.send(VERSION + b'\x03' + len(host).to_bytes(1, "big") + host + port.to_bytes(2, "big"))
				self.remote_list.append(remote_socket)
				self.handle_tcp(client_socket, remote_socket, realip)
		self.remote_list.remove(remote_socket)
		self.run_handler(self.on_disconnect, client_socket)
		client_socket.close()

	def run(self):
		while True:
			client_socket, addr = self.server.accept()
			self.run_handler(self.on_connect, client_socket, addr)

			threading.Thread(target=self.handle_client, args=(client_socket,)).start()
