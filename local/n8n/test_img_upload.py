import urllib.request, http.cookiejar, json, mimetypes, uuid, urllib.parse
CJ = r'C:\Users\pol\AppData\Local\Temp\cd3.txt'
cj = http.cookiejar.MozillaCookieJar(CJ)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
# fresh login
login = urllib.parse.urlencode({'login_user': 'admin', 'login_pass': '10203040'}).encode()
op.open(urllib.request.Request('http://127.0.0.1:8081/chatdesk/index.php', data=login,
                              headers={'User-Agent': 'Mozilla/5.0',
                                       'Content-Type': 'application/x-www-form-urlencoded'}), timeout=30).read()
cj.save(CJ, ignore_discard=True, ignore_expires=True)

# get fresh csrf
html = op.open(urllib.request.Request('http://127.0.0.1:8081/chatdesk/rag/',
                                      headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode()
import re
csrf = re.search(r'var CSRF = "([a-f0-9]+)"', html).group(1)
print('csrf:', csrf)

# multipart: image file + fields
boundary = '----RAGTEST' + uuid.uuid4().hex
img = open(r'C:\Users\pol\AppData\Local\Temp\rag_img.jpg', 'rb').read()
parts = []
def field(name, val):
    parts.append('--' + boundary + '\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (name, val))
for k, v in [('csrf', csrf), ('type', 'image'), ('group_id', '1'),
             ('title', 'หาดป่าตองยามเย็น'), ('text', '')]:
    field(k, v)
parts.append('--' + boundary + '\r\nContent-Disposition: form-data; name="file"; filename="beach.jpg"\r\n'
             + 'Content-Type: image/jpeg\r\n\r\n')
body = ''.join(parts).encode() + img + ('\r\n--' + boundary + '--\r\n').encode()
req = urllib.request.Request('http://127.0.0.1:8081/chatdesk/rag/api/ingest.php', data=body,
                             headers={'Content-Type': 'multipart/form-data; boundary=' + boundary,
                                      'User-Agent': 'Mozilla/5.0'})
try:
    print(op.open(req, timeout=300).read().decode()[:400])
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode()[:400])
