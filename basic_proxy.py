import socket
import select
import threading

def handle_client(client_socket):
	request = client_socket.recv(4096*16)
	request = request.decode("utf-8")

	cmd = request.split(" ")[0]
	urlport = request.split(" ")[1]
	
	url = urlport.split(":")[0]
	port = int(urlport.split(":")[1])
	useragent = " ".join(request.split(' ')[2:])

	# print(f"[*] Received request for {url}:{port}")
	if (cmd == "CONNECT"):
		threading.Thread(target=relay_data, args=(client_socket, url, port)).start()
	else:
		print(cmd, url, port, useragent)

def relay_data(client_socket, url, port):
	proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	proxy_server.connect((url, port))
	client_socket.send("HTTP/1.1 200 Connection Established\r\n\r\n".encode("utf-8"))
	print(f"[*] Connected to {url}:{port}")
	sockets = [client_socket, proxy_server]
	while True:
		recv, _, _ = select.select(sockets, [], [])
		for s in recv:
			try:
				data = s.recv(4096)
			except:
				exit()
			if s is proxy_server:
				client_socket.send(data)
			else:
				try:
					proxy_server.send(data)
				except:
					exit()



def start_server(listen_address, listen_port):
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind((listen_address, listen_port))
	server_socket.listen(5)
	print(f"[*] Listening on {listen_address}:{listen_port}")

	while True:
		client_socket, addr = server_socket.accept()
		# print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")
		handle_client(client_socket)

if __name__ == "__main__":
	start_server("127.0.0.1", 1080)
