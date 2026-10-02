import urllib.request
body = open(r'C:\Users\pol\AppData\Local\Temp\opencode\echo_body.bin', 'rb').read()
head = open(r'C:\Users\pol\AppData\Local\Temp\opencode\echo_head.txt').read()
ct = [l for l in head.splitlines() if l.lower().startswith('content-type')]
print('ct:', ct)
req = urllib.request.Request(
    'http://127.0.0.1:8080/asr?task=transcribe&language=th&output=json&vad_filter=true',
    data=body, headers={'Content-Type': ct[0].split(': ', 1)[1], 'User-Agent': 'n8n'},
    method='POST')
r = urllib.request.urlopen(req, timeout=180)
print(r.status)
print(r.read().decode()[:300])
