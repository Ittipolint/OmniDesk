from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        ln = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(ln)
        open(r'C:\Users\pol\AppData\Local\Temp\opencode\mitm_req.bin', 'wb').write(body)
        # forward to whisper as-is
        req = urllib.request.Request('http://127.0.0.1:8080/asr?task=transcribe&language=th&output=json&vad_filter=true',
                                     data=body, headers={'Content-Type': self.headers.get('Content-Type')},
                                     method='POST')
        try:
            r = urllib.request.urlopen(req, timeout=300)
            resp = r.read()
            open(r'C:\Users\pol\AppData\Local\Temp\opencode\mitm_resp.bin', 'wb').write(resp)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(resp)
        except Exception as e:
            open(r'C:\Users\pol\AppData\Local\Temp\opencode\mitm_resp.bin', 'wb').write(('ERR:' + str(e)).encode())
            raise
    def log_message(self, *a):
        pass
HTTPServer(('127.0.0.1', 8098), H).serve_forever()
