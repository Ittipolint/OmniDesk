import urllib.request, json, base64
key = '__GEMINI_API_KEY__'
img = base64.b64encode(open(r'C:\Users\pol\AppData\Local\Temp\rag_img.jpg', 'rb').read()).decode()
body = json.dumps({'contents': [{'parts': [
    {'text': 'พากย์ภาพนี้เป็นภาษาไทย 1-2 ประโยค'},
    {'inline_data': {'mime_type': 'image/jpeg', 'data': img}}]}]}).encode()
req = urllib.request.Request(
    'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=' + key,
    data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
try:
    r = urllib.request.urlopen(req, timeout=120)
    d = json.loads(r.read())
    print('OK:', d['candidates'][0]['content']['parts'][0]['text'][:200])
except Exception as e:
    print('FAIL:', str(e)[:200])
    try:
        print(e.read().decode()[:400])
    except Exception:
        pass
