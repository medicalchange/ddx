import http.server
import json
import sys
import threading

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
OUTPUT = 'data/seed-data.json'

class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/data':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
            return
        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length)
        try:
            decoded = body.decode('utf-8')
        except UnicodeDecodeError:
            decoded = body.decode('utf-8', 'replace')
        with open(OUTPUT, 'w', encoding='utf-8') as fh:
            fh.write(decoded)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'OK')
        threading.Thread(target=self.server.shutdown).start()

    def log_message(self, format, *args):
        return

if __name__ == '__main__':
    print(f'Listening on http://127.0.0.1:{PORT}/data to receive seed JSON...')
    server = http.server.HTTPServer(('127.0.0.1', PORT), Handler)
    try:
        server.serve_forever()
    finally:
        print('Server shutting down')
