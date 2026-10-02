<?php
// ChatDesk LOCAL — จัดการผู้ใช้และกลุ่ม (เฉพาะ ADMIN)
require_once __DIR__ . '/../inc/bootstrap.php';
$me = cd_current_user();
if (!$me) { header('Location: ../index.php'); exit; }
if (!cd_is_admin()) { http_response_code(403); echo 'เฉพาะกลุ่ม ADMIN'; exit; }
?>
<!doctype html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>จัดการผู้ใช้ • <?= e($CFG['app']['title']) ?></title>
<link rel="icon" href="../assets/omnidesk-icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../assets/css/app.css?v=<?= cd_asset_ver('assets/css/app.css') ?>">
<style>
.wrap{max-width:960px;margin:24px auto;padding:0 16px}
.card{background:#fff;border-radius:14px;padding:18px;margin-bottom:16px;box-shadow:0 2px 10px rgba(0,0,0,.06)}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{border-bottom:1px solid #eef1f6;padding:8px 10px;text-align:left}
.badge{display:inline-block;background:#e8f3ff;color:#287dfa;border-radius:8px;padding:1px 8px;font-size:12px;margin-right:4px}
.badge.admin{background:#e6f9ee;color:#00a651}
.btn{background:#287dfa;color:#fff;border:0;border-radius:8px;padding:8px 14px;cursor:pointer;font-weight:700}
.btn.red{background:#ff5b5b}.btn.ghost{background:#eef2f9;color:#333}
input,select{border:1.5px solid #dfe4ee;border-radius:8px;padding:8px 10px;font-size:14px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:end}
.topnav{margin-bottom:12px}.topnav a{color:#287dfa;font-weight:700;text-decoration:none;margin-right:12px}
</style></head>
<body style="background:#f3f5f9;font-family:'IBM Plex Sans Thai',system-ui,sans-serif">
<div class="wrap">
  <div class="topnav"><a href="../index.php">← กลับกล่องข้อความ</a><a href="../rag/">🧠 RAG System</a></div>
  <div class="card"><h2 style="margin:0 0 4px"><img src="../assets/omnidesk-icon.svg" alt="" style="height:1.1em;vertical-align:-0.15em"> จัดการผู้ใช้และกลุ่ม</h2>
    <p style="margin:0;color:#667;font-size:13px">เฉพาะกลุ่ม ADMIN • รหัสผ่านเก็บแบบ hash ไม่เก็บ plain text</p></div>

  <div class="card"><h3>＋ เพิ่มผู้ใช้</h3>
    <div class="row">
      <div><label>ชื่อผู้ใช้<br><input id="f_user" placeholder="เช่น staff1"></label></div>
      <div><label>รหัสผ่าน<br><input id="f_pass" type="password" placeholder="อย่างน้อย 4 ตัว"></label></div>
      <div><label>ชื่อแสดง<br><input id="f_name" placeholder="เช่น พนักงาน 1"></label></div>
      <div><label>กลุ่ม<br><select id="f_groups" multiple size="2" style="min-width:140px"></select></label></div>
      <div><br><button class="btn" onclick="saveUser(0)">บันทึก</button></div>
    </div>
  </div>

  <div class="card"><h3>ผู้ใช้ทั้งหมด</h3><div id="userList">กำลังโหลด…</div></div>

  <div class="card"><h3>กลุ่มผู้ใช้</h3>
    <div class="row"><div><label>ชื่อกลุ่มใหม่<br><input id="g_name" placeholder="เช่น MANAGER"></label></div>
    <div><label>คำอธิบาย<br><input id="g_desc" placeholder=""></label></div>
    <div><br><button class="btn" onclick="addGroup()">เพิ่มกลุ่ม</button></div></div>
    <div id="groupList" style="margin-top:10px"></div>
  </div>
</div>
<div class="toast" id="toast" hidden></div>
<script>
var CSRF = <?= json_encode($csrf = cd_csrf_token()) ?>;
function toast(m){ var t=document.getElementById('toast'); t.textContent=m; t.hidden=false; clearTimeout(t._h); t._h=setTimeout(function(){t.hidden=true},2500); }
async function api(path, body){
  var r = await fetch(path, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(Object.assign({csrf:CSRF}, body||{})) });
  return r.json();
}
async function load(){
  var u = await api('api/list.php', {});
  if(!u.ok){ toast(u.error||'โหลดไม่สำเร็จ'); return; }
  var gs = u.groups.map(function(g){ return '<option value="'+g.id+'">'+g.name+'</option>'; }).join('');
  document.getElementById('f_groups').innerHTML = gs;
  document.getElementById('groupList').innerHTML = u.groups.map(function(g){
    var prot = (g.name==='ADMIN'||g.name==='STAFF') ? ' <small>(กลุ่มระบบ)</small>' : ' <button class="btn ghost" onclick="delGroup('+g.id+')">ลบ</button>';
    return '<div>• <b>'+g.name+'</b> — '+g.description+prot+'</div>';
  }).join('');
  document.getElementById('userList').innerHTML = '<table><tr><th>ผู้ใช้</th><th>ชื่อแสดง</th><th>กลุ่ม</th><th>สถานะ</th><th>จัดการ</th></tr>' +
    u.users.map(function(x){
      var badges = x.groups.map(function(g){ return '<span class="badge'+(g==='ADMIN'?' admin':'')+'">'+g+'</span>'; }).join('');
      return '<tr><td><b>'+x.username+'</b></td><td>'+x.display_name+'</td><td>'+badges+'</td><td>'+(x.is_active==='1'||x.is_active===1?'ใช้งาน':'ปิด')+'</td><td>' +
        '<button class="btn ghost" onclick="resetPass('+x.id+',\''+x.username+'\')">รีเซ็ตรหัส</button> ' +
        '<button class="btn ghost" onclick="toggleActive('+x.id+','+(x.is_active==='1'||x.is_active===1?0:1)+')">'+(x.is_active==='1'||x.is_active===1?'ปิด':'เปิด')+'</button> ' +
        '<button class="btn red" onclick="delUser('+x.id+',\''+x.username+'\')">ลบ</button></td></tr>';
    }).join('') + '</table>';
}
async function saveUser(){
  var gsel = Array.prototype.map.call(document.getElementById('f_groups').selectedOptions, function(o){ return o.value; });
  var r = await api('api/save.php', { username: document.getElementById('f_user').value, password: document.getElementById('f_pass').value, display_name: document.getElementById('f_name').value, groups: gsel });
  toast(r.ok ? 'บันทึกแล้ว' : ('ผิดพลาด: ' + (r.error||'')));
  if(r.ok){ document.getElementById('f_user').value=''; document.getElementById('f_pass').value=''; document.getElementById('f_name').value=''; load(); }
}
async function resetPass(id, name){
  var p = prompt('รหัสผ่านใหม่ของ ' + name + ':');
  if(!p) return;
  var r = await api('api/save.php', { id: id, password: p });
  toast(r.ok ? 'เปลี่ยนรหัสแล้ว' : ('ผิดพลาด: ' + (r.error||'')));
}
async function toggleActive(id, to){ var r = await api('api/save.php', { id: id, is_active: to }); toast(r.ok?'บันทึกแล้ว':r.error); if(r.ok) load(); }
async function delUser(id, name){ if(!confirm('ลบผู้ใช้ ' + name + '?')) return; var r = await api('api/delete.php', { id: id }); toast(r.ok?'ลบแล้ว':r.error); if(r.ok) load(); }
async function addGroup(){
  var r = await api('api/group.php', { op: 'add', name: document.getElementById('g_name').value, description: document.getElementById('g_desc').value });
  toast(r.ok ? 'เพิ่มกลุ่มแล้ว' : ('ผิดพลาด: ' + (r.error||'')));
  if(r.ok){ document.getElementById('g_name').value=''; document.getElementById('g_desc').value=''; load(); }
}
async function delGroup(id){ if(!confirm('ลบกลุ่มนี้? (สมาชิกจะหลุดจากกลุ่ม)')) return; var r = await api('api/group.php', { op: 'delete', id: id }); toast(r.ok?'ลบแล้ว':r.error); if(r.ok) load(); }
load();
</script>
</body></html>
