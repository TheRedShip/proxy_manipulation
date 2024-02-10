import socket
import threading
import select

VERSION = b'\x05\x00\x00'
CMD_CONNECT = 1
ATYP_IPV4 = 1
ATYP_DOMAINNAME = 3

verbose = False
verbose_ip = []

class SOCKS5:
	def __init__(self, listen_address, listen_port):
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind((listen_address, listen_port))
		self.server.listen(5)
		print("Listening on", listen_address, listen_port)

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
						if (verbose or host in verbose_ip):
							print("[*] REQUESTED RECEIVED", data)
						client_socket.send(data)
					else:
						if (verbose or host in verbose_ip):
							print("[*] REQUESTED SENDING", data)
						remote_socket.send(data)
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
					if (verbose):
						print("[*] REQUESTED", command, realip, port)
					remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					remote_socket.connect((realip, port))
					client_socket.send(b'\x05\x00\x00\x01' + host + port.to_bytes(2, "big"))

				elif (host_type == ATYP_DOMAINNAME):
					realip = host.decode()
					if (verbose):
						print("[*] REQUESTED", command, realip, port)

					remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					remote_socket.connect((realip, port))
					client_socket.send(b'\x05\x00\x00\x03' + len(host).to_bytes(1, "big") + host + port.to_bytes(2, "big"))
				else:
					print("non géré!")
					client_socket.close()
				self.handle_tcp(client_socket, remote_socket, realip)
			else:
				print("non géré")
				client_socket.close()
		else:
			print("autre methode authentification")
			client_socket.close()

	def run(self):
		while True:
			client_socket, addr = self.server.accept()
			if (verbose):
				print(f"[*] Connected to {addr[0]}:{addr[1]}")
			threading.Thread(target=self.handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
	socks = SOCKS5("0.0.0.0", 8888)
	threading.Thread(target=socks.run).start()

	while True:
		cmd = input("> ")
		if (cmd == "v"):
			verbose = not verbose
		elif (cmd.startswith("v ")):
			ip = cmd.split(" ")[1]
			if (ip in verbose_ip):
				verbose_ip.remove(ip)
			else:
				verbose_ip.append(ip)