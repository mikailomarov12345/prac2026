from math import sqrt
import socket

def sqroots(s) -> str:

	a, b, c = s.split(" ")
	a, b, c = float(a), float(b), float(c)
	D = b**2 - 4*a*c

	if D < 0: return ""

	elif D == 0: return str(-b/(2*a))

	x1 = str((-b + sqrt(D))/(2*a))
	x2 = str((-b - sqrt(D))/(2*a))

	return x1 + " " + x2

def sqrootsnet(coeffs: str, s: socket.socket) -> str:
	s.sendall((coeffs + "\n").encode())
	return s.recv(128).decode().strip()

if __name__ == "__main__":
	import sys
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as:
		s.connect(("127.0.0.1", 1337))
		s.sendall(sys.argv[1].encode()+b"\n")
		print(s.recv(1024).rstrip().decode())
