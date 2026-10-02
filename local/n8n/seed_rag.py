import urllib.request, http.cookiejar, json, re
BASE = 'http://127.0.0.1:8081'
CJ = r'C:\Users\pol\AppData\Local\Temp\cd3.txt'
cj = http.cookiejar.MozillaCookieJar(CJ)
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
login = urllib.parse.urlencode({'login_user': 'admin', 'login_pass': '10203040'}).encode()
op.open(urllib.request.Request(BASE + '/chatdesk/index.php', data=login,
                              headers={'User-Agent': 'Mozilla/5.0',
                                       'Content-Type': 'application/x-www-form-urlencoded'}), timeout=30).read()
cj.save(CJ, ignore_discard=True, ignore_expires=True)
html = op.open(urllib.request.Request(BASE + '/chatdesk/rag/',
                                      headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode()
csrf = re.search(r'var CSRF = "([a-f0-9]+)"', html).group(1)

def post(path, obj):
    req = urllib.request.Request(BASE + path, data=json.dumps(obj).encode(),
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    return json.loads(op.open(req, timeout=300).read())

docs = [
    ('text', 1, 'เช็กอินโรงแรมภูเก็ต',
     'โรงแรมในภูเก็ตส่วนใหญ่ให้เช็กอินตั้งแต่เวลา 14:00 น. และเช็กเอาต์ก่อน 12:00 น. '
     'หากมาถึงก่อนเวลาสามารถฝากกระเป๋าที่ล็อบบี้ได้ฟรี กรุณาแสดงบัตรประชาชนหรือพาสปอร์ตตอนเช็กอิน'),
    ('text', 2, 'สิทธิลาพักร้อนพนักงาน',
     'พนักงานประจำมีสิทธิลาพักร้อนปีละ 10 วันทำการ ต้องแจ้งล่วงหน้าอย่างน้อย 3 วัน '
     'วันลาที่เหลือสะสมไปปีถัดไปได้ไม่เกิน 5 วัน'),
    ('text', 2, 'เบิกค่าเดินทาง',
     'พนักงานเบิกค่าเดินทางไปปฏิบัติงานต่างจังหวัดได้ตามจริง ไม่เกิน 2,000 บาทต่อทริป '
     'แนบใบเสร็จทุกครั้ง ยื่นภายใน 7 วันหลังเดินทาง'),
]
for typ, gid, title, text in docs:
    r = post('/chatdesk/rag/api/ingest.php',
             {'csrf': csrf, 'type': typ, 'group_id': gid, 'title': title, 'text': text})
    print(title, '->', r.get('ok'), r.get('message') or r.get('error'))

for q, gid in [('เช็กอินภูเก็ตได้กี่โมง', 1), ('ลาพักร้อนได้กี่วัน', 2), ('เบิกค่าเดินทางได้เท่าไร', None)]:
    r = post('/chatdesk/rag/api/ask.php',
             {'csrf': csrf, 'question': q, 'group_id': gid} if gid else
             {'csrf': csrf, 'question': q})
    print('Q:', q)
    print('A:', (r.get('text') or r.get('error'))[:160])
    print('src:', r.get('sources'))
