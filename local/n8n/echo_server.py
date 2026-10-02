from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        ln = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(ln)
        open(r'C:\Users\pol\AppData\Local\Temp\opencode\echo_body.bin', 'wb').write(body)
        open(r'C:\Users\pol\AppData\Local\Temp\opencode\echo_head.txt', 'w').write(str(self.headers))
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"text":"echo-ok"}')
    def log_message(self, *a):
        pass
HTTPServer(('127.0.0.1', 8099), H).serve_forever()
