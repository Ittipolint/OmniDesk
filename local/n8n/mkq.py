import urllib.request, json, subprocess
key = '__GEMINI_API_KEY__'
body = json.dumps({'content': {'parts': [{'text': 'ยกเลิกที่พักภูเก็ต'}]},
                   'taskType': 'RETRIEVAL_QUERY', 'outputDimensionality': 768}).encode()
req = urllib.request.Request(
    'https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key=' + key,
    data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
vals = json.load(urllib.request.urlopen(req, timeout=60))['embedding']['values']
print('dims:', len(vals))
lit = '[' + ','.join(map(str, vals)) + ']'
sql = ("SELECT c.content, 1 - (c.embedding <=> '%s'::vector) AS sim FROM rag_chunks c "
       "ORDER BY c.embedding <=> '%s'::vector LIMIT 4" % (lit, lit))
open(r'C:\Users\pol\AppData\Local\Temp\opencode\q.sql', 'w', encoding='utf-8').write(sql)
print('sql bytes:', len(sql))
