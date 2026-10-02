const s = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3').verbose();
const db = new s.Database('/home/node/.n8n/database.sqlite', s.OPEN_READONLY);
const id = process.argv[2] || '310';
db.all('PRAGMA table_info(execution_data)', (e, r) => {
  if (e) { console.log('ERR ' + e.message); process.exit(1); }
  console.log('cols: ' + r.map(c => c.name + ':' + c.type).join(','));
  db.all('SELECT executionId, SUBSTR(data, 1, 300) AS head FROM execution_data WHERE executionId = ?', [id], (e2, rows) => {
    if (e2) { console.log('ERR2 ' + e2.message); process.exit(1); }
    console.log(JSON.stringify(rows).slice(0, 600));
    db.close();
  });
});
