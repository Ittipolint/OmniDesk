const http = require('http');
const urls = ['http://host.docker.internal:8080/', 'http://host.docker.internal:5678/rest/settings'];
(async () => {
  for (const u of urls) {
    await new Promise((res) => {
      const req = http.get(u, { timeout: 8000 }, (r) => {
        let n = 0;
        r.on('data', (c) => { n += c.length; });
        r.on('end', () => { console.log(u, '->', r.statusCode, n + ' bytes'); res(); });
      });
      req.on('timeout', () => { console.log(u, '-> TIMEOUT'); req.destroy(); res(); });
      req.on('error', (e) => { console.log(u, '-> ERR', e.message); res(); });
    });
  }
})();
