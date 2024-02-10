import struct

def show_packet(data, verbose):
	if (verbose):
		print(data)

def h_position(data, verbose):
	x,y,z = struct.unpack('>ddd', data[0:24])
	if (y > 80):
		x -= 5
	show_packet("[pos] {:.0f}, {:.0f}, {:.0f}".format(x, y, z),verbose)
	return struct.pack('>ddd', x, y, z) + data[24].to_bytes(1, byteorder='big')

def h_looking(data, verbose):
	x,y = struct.unpack('>ff', data[0:8])
	show_packet("[look] {:.0f}, {:.0f}".format(x, y),verbose)
	return struct.pack('>ff', x, y) + data[8].to_bytes(1, byteorder='big')

def h_look_and_pos(data, verbose):
	x,y,z = struct.unpack('>ddd', data[0:24])
	show_packet("[pos] {:.0f}, {:.0f}, {:.0f}".format(x, y, z),verbose)
	xlook,ylook = struct.unpack('>ff', data[24:32])
	show_packet("[look] {:.0f}, {:.0f}".format(x, y),verbose)
	return struct.pack('>dddff', x, y, z, xlook, ylook) + data[32].to_bytes(1, byteorder='big')

def break_block(data, verbose):
	single_byte = data[0]
	show_packet(f"[break] {single_byte}", verbose)
	return single_byte.to_bytes(1, byteorder='big')