from socks5 import Socks5
import packet_functions
import sys, importlib
from threading import Thread

verbose = False

def get_packets():
	return {
		b'\x1b\x00\x14': packet_functions.h_position,
		b'\x0b\x00\x16': packet_functions.h_looking,
		b'#\x00\x15': packet_functions.h_look_and_pos,
		b'\x03\x00/': packet_functions.break_block
	}

def on_connect(client_socket, addr):
	print(f"[*] Connected to {addr[0]}:{addr[1]}")

def on_disconnect(client_socket):
	print(f"[-] {client_socket.getpeername()} disconnected")

def on_sending(remote_socket, data):
	global verbose
	print(data)
	try:
		importlib.reload(packet_functions)
		packets = get_packets()
	except Exception as e:
		print(e)
		return data

	new_data = b''
	while len(data) > 0:
		packet_type = data[0:3]
		if packet_type in packets:
			current_packet = packet_type + packets[packet_type](data[3:], verbose)
			new_data += current_packet
			data = data[3+len(current_packet):]
		else:
			print(packet_type, "not found")
			break
	if (new_data == b''):
		new_data = data
	return new_data

def on_receiving(client_socket, data):
	print(data)
	return data

def packet_injector(server):
	global verbose

	while True:
		command = input("Enter command: ")
		if command == "v":
			verbose = not verbose
		elif command == ('getsock'):
			for sock in server.remote_list:
				print(sock.getpeername())
		elif command.startswith('s '):
			args = command.split(' ')
			servernum = int(args[1])
			packet = args[2].encode('utf-8')
			server.remote_list[servernum].send(packet)

if __name__ == '__main__':
	server = Socks5('0.0.0.0', 8888)

	server.on_connect = on_connect
	server.on_disconnect = on_disconnect
	server.on_sending = on_sending
	server.on_receiving = on_receiving

	Thread(target=server.run).start()
	packet_injector(server)
