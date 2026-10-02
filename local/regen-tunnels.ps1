# regen-tunnels.ps1 — สร้าง Quick Tunnel ใหม่ (n8n + web) + อัปเดต URL ในไฟล์ให้เอง
# วิธีใช้: คลิกขวา > Run with PowerShell (หรือเปิด PowerShell ในโฟลเดอร์ local\ แล้วรัน .\regen-tunnels.ps1)
# หลังรันเสร็จ เหลือแค่ 1 อย่างที่ต้องทำมือ:
#   1) วาง Webhook URL ใหม่ใน LINE Developers console แล้วกด Verify
#
# หมายเหตุ: veya ถูกตัดออกแล้ว — ไม่มีขั้นตอนอัปโหลด/voice tunnel สาธารณะ
# เสียง (STT/TTS) ทำงานภายในผ่าน host.docker.internal:8080 ไม่ต้องมี tunnel

$D = 'C:\Users\pol\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe'
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path   # โฟลเดอร์ local\

function New-Tunnel($name, $target) {
    Write-Host "`n=== $name ($target) ===" -ForegroundColor Cyan
    & $D rm -f $name 2>$null | Out-Null
    & $D run -d --name $name --restart unless-stopped cloudflare/cloudflared:latest tunnel --no-autoupdate --url $target | Out-Null
    $url = ''
    for ($i = 0; $i -lt 12 -and -not $url; $i++) {
        Start-Sleep -Seconds 5
        $log = & $D logs $name 2>&1 | Out-String
        if ($log -match '(https://[a-z0-9-]+\.trycloudflare\.com)') { $url = $Matches[1] }
    }
    if (-not $url) { throw "ดึง URL ของ $name ไม่สำเร็จ ดู log: docker logs $name" }
    Write-Host "URL ใหม่: $url" -ForegroundColor Green
    return $url
}

function Replace-Url($file, $newUrl) {
    $t = Get-Content $file -Raw
    $t2 = $t -replace 'https://[a-z0-9-]+\.trycloudflare\.com', $newUrl
    if ($t2 -ne $t) { Set-Content $file $t2 -NoNewline; Write-Host "  อัปเดต: $file" }
}

# 1) n8n (LINE)
$n8n = New-Tunnel 'chatdesk-cf-n8n' 'http://host.docker.internal:5678'
# 2) ChatDesk web
$web = New-Tunnel 'chatdesk-cf-web' 'http://host.docker.internal:8081'

# อัปเดตไฟล์ local อัตโนมัติ
Replace-Url "$ROOT\www\chatdesk\config.php" $n8n

Write-Host "`n================ สรุป ================" -ForegroundColor Yellow
Write-Host "1) วางใน LINE Developers console -> Webhook URL แล้วกด Verify:"
Write-Host "   $n8n/webhook/chatdesk-mgr" -ForegroundColor Green
Write-Host "2) เว็บสาธารณะ: $web"
Write-Host "3) ถ้าใช้รูป LINE: python3 local/n8n/update_public_base.py $web"
Write-Host "`nเสร็จแล้วครับ" -ForegroundColor Yellow
