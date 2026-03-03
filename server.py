#!/usr/bin/env python3
"""HTTP server that responds to every request with the raw contents of response.txt."""

import socket
import sys
import os

RESPONSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "response.txt")
DEFAULT_PORT = 8080


def load_response():
    with open(RESPONSE_FILE, "rb") as f:
        return f.read()


def serve(port):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", port))
    srv.listen(16)
    print(f"Serving on http://0.0.0.0:{port}")
    print(f"Response file: {RESPONSE_FILE}")
    print("Edit response.txt at any time -- each request re-reads the file.\n")

    try:
        while True:
            conn, addr = srv.accept()
            try:
                # Read enough of the request to not leave the client hanging
                conn.recv(4096)
                raw = load_response()
                conn.sendall(raw)
            except Exception as e:
                print(f"[error] {addr}: {e}")
            finally:
                conn.close()
            print(f"[served] {addr[0]}:{addr[1]}")
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        srv.close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    serve(port)
