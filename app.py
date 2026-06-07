import json
import random
import uuid
import requests
from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)

# =================================================================
# ⚠️ [필수 수정]기에 구글 배포에서 복사한 '웹 앱 URL' 주소를 넣어주세요!
GOOGLE_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzmqGWxKe3ur3W-OnRy-rdVnkG4DrlX5LNDOYtFVowtZ-X4hkvSjiVuHZ810ruHRaD1PA/exec"
# =================================================================

def load_data():
    try:
        res = requests.get(GOOGLE_WEB_APP_URL)
        if res.status_code == 200: return res.json()
    except: pass
    return {}

def save_data(data):
    try: requests.post(GOOGLE_WEB_APP_URL, json=data)
    except: pass

# Render 구문 에러를 방지하기 위해 스타일과 HTML을 모두 한 줄로 결합했습니다.
COMMON_STYLE = "<style>body { font-family: 'Malgun Gothic', sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; color: #333; } .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); } h1, h2 { color: #1e3a8a; text-align: center; } .form-group { margin-bottom: 15px; } label { display: block; margin-bottom: 5px; font-weight: bold; } input[type='text'], input[type='number'] { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; } button { width: 100%; padding: 12px; background-color: #2563eb; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; } button:hover { background-color: #1d4ed8; } .event-card { border: 1px solid #e5e7eb; padding: 20px; border-radius: 8px; margin-top: 20px; background-color: #fff; position: relative; } .btn-close { background-color: #10b981; margin-bottom: 5px; } .btn-close:hover { background-color: #059669; } .btn-delete { background-color: #ef4444; } .btn-delete:hover { background-color: #dc2626; } .link-box { background: #f3f4f6; padding: 10px; border-radius: 6px; word-break: break-all; font-size: 14px; margin: 10px 0; border: 1px dashed #cbd5e1; } .badge { display: inline-block; padding: 4px 8px; background: #dbeafe; color: #1e40af; border-radius: 4px; font-size: 12px; font-weight: bold; } .badge-closed { background: #fee2e2; color: #991b1b; }</style>"

ADMIN_TEMPLATE = "<!DOCTYPE html><html><head><title>혜타민 추첨기</title>{{ style|safe }}</head><body><div class='container'><h1>🛠️ 혜타민 추첨기</h1><form action='/admin/create' method='POST'><div class='form-group'><label>🎁 상품 이름</label><input type='text' name='prize_name' placeholder='예: 교촌치킨 허니콤보' required></div><div class='form-group'><label>🏆 당첨 인원 수</label><input type='number' name='winner_count' min='1' value='1' required></div><button type='submit'>이벤트 만들기</button></form><h2>[ 내 이벤트 목록 ]</h2>{% if not events %}<p style='text-align: center; color: #666;'>아직 만든 이벤트가 없거나 구글 연동 대기 중입니다.</p>{% endif %}{% for id, ev in events.items() %}<div class='event-card'><h3>{{ ev.prize_name }} {% if ev.closed %}<span class='badge badge-closed'>마감됨</span>{% else %}<span class='badge'>모집중</span>{% endif %}</h3><p><b>선택 인원:</b> {{ ev.winner_count }}명 / <b>현재 참여자:</b> {{ ev.participants|length }}명</p><div class='link-box'>🔗 참가 링크: <a href='{{ ev.user_url }}' target='_blank'>{{ ev.user_url }}</a></div>{% if not ev.closed %}<form action='/admin/close/{{ id }}' method='POST'><button type='submit' class='btn-close'>🚫 마감 및 추첨하기</button></form>{% else %}<div style='background: #f0fdf4; padding: 10px; border-radius: 6px; border: 1px solid #bbf7d0;'><b>🏆 당첨자 결과:</b> {{ ev.winners|join(', ') if ev.winners else '참여자 없음' }}</div>{% endif %}<form action='/admin/delete/{{ id }}' method='POST' style='margin-top: 10px;'><button type='submit' class='btn-delete'>🗑️ 삭제</button></form></div>{% endfor %}</div></body></html>"

USER_TEMPLATE = "<!DOCTYPE html><html><head><title>혜타민 추첨기 참여</title>{{ style|safe }}</head><body><div class='container'><h1>🎁 혜타민 추첨기 응모하기</h1><div style='text-align: center; margin-bottom: 20px; background: #eff6ff; padding: 15px; border-radius: 8px;'><h2 style='margin: 0 0 10px 0; color: #2563eb;'>{{ event.prize_name }}</h2><p style='margin: 0;'>총 <b>{{ event.winner_count }}명</b>에게 선물을 드립니다!</p></div>{% if event.closed %}<div style='background: #fee2e2; padding: 20px; border-radius: 8px; text-align: center;'><h3 style='color: #dc2626;'>마감된 이벤트입니다 🚫</h3><b>🏆 당첨자:</b> {{ event.winners|join(', ') if event.winners else '없음' }}</div>{% else %}<form action='/submit/{{ event_id }}' method='POST'><div class='form-group'><label>📝 내 닉네임</label><input type='text' name='username' required></div><button type='submit'>이벤트 응모하기 🚀</button></form>{% endif %}</div></body></html>"

@app.route("/")
def home(): return redirect(url_for("admin_page"))

@app.route("/admin")
def admin_page():
    events = load_data()
    return render_template_string(ADMIN_TEMPLATE, events=events, style=COMMON_STYLE)

@app.route("/admin/create", methods=["POST"])
def create_event():
    events = load_data()
    prize_name = request.form.get("prize_name")
    winner_count = int(request.form.get("winner_count", 1))
    event_id = str(uuid.uuid4())[:8]
    user_url = request.host_url + f"event/{event_id}"
    events[event_id] = {
        "prize_name": prize_name, "winner_count": winner_count,
        "participants": [], "winners": [], "closed": False, "user_url": user_url
    }
    save_data(events)
    return redirect(url_for("admin_page"))

@app.route("/admin/close/<event_id>", methods=["POST"])
def close_event(event_id):
    events = load_data()
    if event_id in events and not events[event_id]["closed"]:
        ev = events[event_id]
        ev["closed"] = True
        if ev["participants"]:
            ev["winners"] = random.sample(ev["participants"], min(len(ev["participants"]), ev["winner_count"]))
        save_data(events)
    return redirect(url_for("admin_page"))

@app.route("/admin/delete/<event_id>", methods=["POST"])
def delete_event(event_id):
    events = load_data()
    if event_id in events: del events[event_id]
    save_data(events)
    return redirect(url_for("admin_page"))

@app.route("/event/<event_id>")
def user_page(event_id):
    events = load_data()
    if event_id not in events: return "<h3>존재하지 않는 이벤트입니다.</h3>", 404
    return render_template_string(USER_TEMPLATE, event=events[event_id], event_id=event_id, style=COMMON_STYLE)

@app.route("/submit/<event_id>", methods=["POST"])
def submit_entry(event_id):
    events = load_data()
    if event_id not in events: return "이벤트가 없습니다.", 404
    ev = events[event_id]
    username = request.form.get("username", "").strip()
    if username and username not in ev["participants"]:
        ev["participants"].append(username)
        save_data(events)
    return f'<script>alert("{username}님 응모 완료!"); window.location.href = "/event/{event_id}";</script>'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
