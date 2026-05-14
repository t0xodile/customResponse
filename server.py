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
        data = f.read()
    # Normalize line endings to \r\n as required by the HTTP RFC.
    # Replace existing \r\n first to avoid doubling, then convert bare \n.
    data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return data


def log_request(log_file, addr, request_data):
    timestamp = datetime.datetime.now().isoformat()
    with open(log_file, "a") as f:
        f.write(f"--- {timestamp} from {addr[0]}:{addr[1]} ---\n")
        f.write(request_data.decode("utf-8", errors="replace"))
        if not request_data.endswith(b"\n"):
            f.write("\n")
        f.write("\n")


def parse_request(request_data):
    """Return (method, headers_dict_lowercased)."""
    try:
        head = request_data.split(b"\r\n\r\n", 1)[0].decode("iso-8859-1")
    except Exception:
        return None, {}
    lines = head.split("\r\n")
    method = lines[0].split(" ", 1)[0] if lines else None
    headers = {}
    for line in lines[1:]:
        name, sep, value = line.partition(":")
        if sep:
            headers[name.strip().lower()] = value.strip()
    return method, headers


def inject_cors_headers(raw, method, headers):
    sep = b"\r\n\r\n"
    idx = raw.find(sep)
    if idx == -1:
        return raw

    origin = headers.get("origin", "*")
    req_method = headers.get("access-control-request-method")
    req_headers = headers.get("access-control-request-headers")

    extra_lines = [
        f"Access-Control-Allow-Origin: {origin}",
        "Access-Control-Allow-Credentials: true",
        f"Access-Control-Allow-Methods: {req_method}" if req_method
            else "Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD",
    ]
    if req_headers:
        extra_lines.append(f"Access-Control-Allow-Headers: {req_headers}")
    extra_lines.append("Access-Control-Max-Age: 86400")
    # Tell caches the response varies by these request headers.
    extra_lines.append("Vary: Origin, Access-Control-Request-Method, Access-Control-Request-Headers")

    extra = ("\r\n".join(extra_lines) + "\r\n").encode("iso-8859-1")
    return raw[:idx] + b"\r\n" + extra.rstrip(b"\r\n") + raw[idx:]


def serve(port, log_file=None, cors_reflect=False):
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
                if cors_reflect:
                    method, headers = parse_request(request_data)
                    raw = inject_cors_headers(raw, method, headers)
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
    parser.add_argument(
        "--cors-reflect",
        action="store_true",
        help="reflect the request's Origin header into Access-Control-Allow-Origin "
             "and add Access-Control-Allow-Credentials: true",
    )
    args = parser.parse_args()
    serve(args.port, log_file=args.log, cors_reflect=args.cors_reflect)
