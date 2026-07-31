import socket
try:
    print(socket.gethostbyname('api.notion.com'))
except Exception as e:
    print("Failed to resolve:", e)
