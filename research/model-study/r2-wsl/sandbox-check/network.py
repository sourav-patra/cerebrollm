import socket
try:
    socket.create_connection(("1.1.1.1", 53), timeout=5)
except OSError as e:
    print("network denied:", e)
else:
    raise SystemExit("NETWORK REACHABLE")
