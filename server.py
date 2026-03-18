#!/usr/bin/env python3
"""HTTP server that responds to every request with the raw contents of response.txt."""

import argparse
import datetime
import socket
import os

RESPONSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "response.txt")
DEFAULT_PORT = 8080


def load_response():
    with open(RESPONSE_FILE, "rb") as f:
        return f.read()


def log_request(log_file, addr, request_data):
    timestamp = datetime.datetime.now().isoformat()
    with open(log_file, "a") as f:
        f.write(f"--- {timestamp} from {addr[0]}:{addr[1]} ---\n")
        f.write(request_data.decode("utf-8", errors="replace"))
        if not request_data.endswith(b"\n"):
            f.write("\n")
        f.write("\n")


def serve(port, log_file=None):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", port))
    srv.listen(16)
    print(f"Serving on http://0.0.0.0:{port}")
    print(f"Response file: {RESPONSE_FILE}")
    if log_file:
        print(f"Logging requests to: {log_file}")
    print("Edit response.txt at any time -- each request re-reads the file.\n")

    try:
        while True:
            conn, addr = srv.accept()
            try:
                # Read enough of the request to not leave the client hanging
                request_data = conn.recv(4096)
                if log_file:
                    log_request(log_file, addr, request_data)
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
    parser = argparse.ArgumentParser(description="HTTP server that replies with response.txt")
    parser.add_argument("port", nargs="?", type=int, default=DEFAULT_PORT, help="port to listen on")
    parser.add_argument("--log", metavar="FILE", help="log received requests to FILE")
    args = parser.parse_args()
    serve(args.port, log_file=args.log)
