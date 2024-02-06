import socket
import threading

class SOCKS5:
	def __init__(self, listen_address, listen_port):
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind((listen_address, listen_port))
		self.server.listen(5)
		print("Listening on", listen_address, listen_port)

	def get_host_from_type(self, client_socket):
		host_type = client_socket.recv(1)[0]
		if (host_type == 1):
			adress = client_socket.recv(4)
			return adress, host_type
		elif (host_type == 3):
			host_length = client_socket.recv(1)[0]
			adress = client_socket.recv(host_length)
			return adress, host_type

	def handle_tcp(self, client_socket, remote_socket):
		while True:
			recv_data = client_socket.recv(4096)
			print("[*] RECEIVING REQUEST", recv_data)
			if len(recv_data) > 0:
				remote_socket.send(recv_data)
			else:
				break
			recv_data = remote_socket.recv(4096)
			print("[*] RESPONSE REQUEST", recv_data)
			if len(recv_data) > 0:
				client_socket.send(recv_data)
			else:
				break
		print(client_socket.getpeername(), "disconnected")
		remote_socket.close()
		client_socket.close()

	def handle_client(self, client_socket):
		initial_request = client_socket.recv(8)
		print("INITIAL REQUEST", len(initial_request), initial_request)
		auths_method = [method for method in initial_request[2:]]

		if 0 in auths_method:
			client_socket.send(b'\x05\x00')

			response = client_socket.recv(3)

			command = response[1]
			host, host_type = self.get_host_from_type(client_socket)
			port = int.from_bytes(client_socket.recv(2), "big")
			
			if command == 1:	
				if (host_type == 1):
					print("[*] REQUESTED", command, socket.inet_ntoa(host), port)
					remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					remote_socket.connect((socket.inet_ntoa(host), port))
					client_socket.send(b'\x05\x00\x00\x01' + host + port.to_bytes(2, "big"))

				elif (host_type == 3):
					print("[*] REQUESTED", command, host.decode(), port)

					remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					remote_socket.connect((host.decode(), port))
					client_socket.send(b'\x05\x00\x00\x03' + len(host).to_bytes(1, "big") + host + port.to_bytes(2, "big"))
				else:
					print("non géré!")
					client_socket.close()
				self.handle_tcp(client_socket, remote_socket)
			else:
				print("non géré")
				client_socket.close()
		else:
			print("autre methode authentification")
			client_socket.close()

	def run(self):
		while True:
			client_socket, addr = self.server.accept()
			print(f"[*] Connected to {addr[0]}:{addr[1]}")
			threading.Thread(target=self.handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
	socks = SOCKS5("0.0.0.0", 8888)
	socks.run()		