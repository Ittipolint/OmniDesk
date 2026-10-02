const path = require('path');
const fs = require('fs');
const base = '/usr/local/lib/node_modules/n8n/node_modules';
const cands = ['better-sqlite3', 'sqlite3', 'sql.js', 'node-sqlite3'];
let mod = null, modName = '';
for (const c of cands) {
  try { mod = require(path.join(base, c)); modName = c; break; } catch (e) {}
}
if (!mod) { console.log('NO_SQLITE_DRIVER'); process.exit(1); }
console.log('DRIVER=' + modName);
const db = new mod.Database('/home/node/.n8n/database.sqlite', mod.SQLITE_OPEN_READONLY);
const q = (sql) => new Promise((res, rej) => db.all(sql, (e, rows) => e ? rej(e) : res(rows)));
(async () => {
console.log('--- workflows ---');
(await q('SELECT id, name, active FROM workflow_entity ORDER BY name')).forEach(r => console.log(r.id + ' | ' + r.name + ' | active=' + !!r.active));
console.log('--- users ---');
(await q('SELECT id, email FROM "user"')).forEach(r => console.log(r.id + ' | ' + r.email));
console.log('--- api keys (prefix only) ---');
try { (await q('SELECT id, label, apiKey FROM user_api_keys')).forEach(r => console.log(r.id + ' | ' + r.label + ' | ' + String(r.apiKey).slice(0, 12) + '...')); }
catch (e) { console.log('apikey err: ' + e.message); }
console.log('--- credentials ---');
try { (await q('SELECT id, name, type FROM credentials_entity')).forEach(r => console.log(r.id + ' | ' + r.name + ' | ' + r.type)); }
catch (e) { console.log('cred err: ' + e.message); }
console.log('n8n=' + require('/usr/local/lib/node_modules/n8n/package.json').version);
db.close();
})();
