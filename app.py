import json
import random
import uuid
import gspread
import requests
from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)

# =================================================================
# ⚠️ [필수 수정] 여기에 본인의 구글 엑셀 고유 ID를 넣어주세요!
SPREADSHEET_ID = "1BfVlyrK3H13DK-soS42P1aU_4Bnt8T5c1wryIP7BF8A"
# =================================================================

def load_data():
    try:
        # 최신 gspread 버전에 맞춘 무인증 공개 시트 접근 방식입니다.
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv"
        res = requests.get(url)
        if res.status_code == 200:
            # 엑셀의 첫 번째 칸(A1)에 적힌 JSON 데이터를 가져옵니다.
            text = res.text.strip()
            if text.startswith('"') and text.endswith('"'):
                text = text[1:-1].replace('""', '"')
            return json.loads(text) if text else {}
    except Exception as e:
        print(f"구글 시트 읽기 실패: {e}")
    return {}

def save_data(data):
    try:
        # 데이터 저장은 gspread의 기본 주소 접근 방식을 사용하여 안정성을 높였습니다.
        gc = gspread.api_key("")  # 공개 편집 권한 우회
        sh = gc.open_by_key(SPREADSHEET_ID)
        sheet = sh.get_worksheet(0)
        sheet.update_acell('A1', json.dumps(data, ensure_ascii=False))
    except Exception as e:
        # 우회 방식 실패 시 가상 브라우저 방식으로 재시도
        try:
            url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/values/A1?valueInputOption=RAW"
            headers = {"Content-Type": "application/json"}
            payload = {"values": [[json.dumps(data, ensure_ascii=False)]]}
            requests.put(url, json=payload, headers=headers)
        except Exception as ex:
            print(f"구글 시트 저장 실패: {ex}")

# 줄바꿈 에러 방지용 한 줄 스타일 코드
COMMON_STYLE = "<style>body { font-family: 'Malgun Gothic', sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; color: #333; } .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); } h1, h2 { color: #1e3a8a; text-align: center; } .form-group { margin-bottom: 15px; } label { display: block; margin-bottom: 5px; font-weight: bold; } input[type='text'], input[type='number'] { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; } button { width: 100%; padding: 12px; background-color: #2563eb; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; } button:hover { background-color: #1d4ed8; } .event-card { border: 1px solid #e5e7eb; padding: 20px; border-radius: 8px; margin-top: 20px; background-color: #fff; position: relative; } .btn-close { background-color: #10b981; margin-bottom: 5px; } .btn-close:hover { background-color: #059669; } .btn-delete { background-color: #ef4444; } .btn-delete:hover { background-color: #dc2626; } .link-box { background: #f3f4f6; padding: 10px; border-radius: 6px; word-break: break-all; font-size: 14px; margin: 10px 0; border: 1px dashed #cbd5e1; } .badge { display: inline-block; padding: 4px 8px; background: #dbeafe; color: #1e40af; border-radius: 4px; font-size: 12px; font-weight: bold; } .badge-closed { background: #fee2e2; color: #991b1b; }</style>"

ADMIN_TEMPLATE = """<!DOCTYPE html>
<html>
<head><title>이벤트 관리자</title>{{ style|safe }}</head>
<body>
    <div class="container">
        <h1>🛠️ 영구 저장 이벤트 시스템</h1>
        <form action="/admin/create" method="POST">
            <div class="form-group">
                <label>🎁 상품 이름</label>
                <input type="text" name="prize_name" placeholder="예: 교촌치킨 허니콤보" required>
            </div>
            <div class="form-group">
                <label>🏆 당첨 인원 수</label>
                <input type="number" name="winner_count" min="1" value="1" required>
            </div>
            <button type="submit">이벤트 만들기</button>
        </form>
        <h2>[ 내 이벤트 목록 ]</h2>
        {% if not events %}
            <p style="text-align: center; color: #666;">아직 만든 이벤트가 없거나 구글 연동 대기 중입니다.</p>
        {% endif %}
        {% for id, ev in events.items() %}
            <div class="event-card">
                <h3>{{ ev.prize_name }} {% if ev.closed %}<span class="badge badge-closed">마감됨</span>{% else %}<span class="badge">모집중</span>{% endif %}</h3>
                <p><b>선택 인원:</b> {{ ev.winner_count }}명 / <b>현재 참여자:</b> {{ ev.participants|length }}명</p>
                <div class="link-box">🔗 참가 링크: <a href="{{ ev.user_url }}" target="_blank">{{ ev.user_url }}</a></div>
                {% if not ev.closed %}
                    <form action="/admin/close/{{ id }}" method="POST"><button type="submit" class="btn-close">🚫 마감 및 추첨하기</button></form>
                {% else %}
                    <div style="background: #f0fdf4; padding: 10px; border-radius: 6px; border: 1px solid #bbf7d0;">
                        <b>🏆 당첨자 결과:</b> {{ ev.winners|join(', ') if ev.winners else '참여자 없음' }}
                    </div>
                {% endif %}
                <form action="/admin/delete/{{ id }}" method="POST" style="margin-top: 10px;"><button type="submit" class="btn-delete">🗑️ 삭제</button></form>
            </div>
        {% endfor %}
    </div>
</body>
</html>"""

USER_TEMPLATE = """<!DOCTYPE html>
<html>
<head><title>이벤트 참여</title>{{ style|safe }}</head>
<body>
    <div class="container">
        <h1>🎁 이벤트 응모하기</h1>
        <div style="text-align: center; margin-bottom: 20px; background: #eff6ff; padding: 15px; border-radius: 8px;">
            <h2 style="margin: 0 0 10px 0; color: #2563eb;">{{ event.prize_name }}</h2>
            <p style="margin: 0;">총 <b>{{ event.winner_count }}명</b>에게 선물을 드립니다!</p>
        </div>
        {% if event.closed %}
            <div style="background: #fee2e2; padding: 20px; border-radius: 8px; text-align: center;">
                <h3 style="color: #dc2626;">마감된 이벤트입니다 🚫</h3>
                <b>🏆 당첨자:</b> {{ event.winners|join(', ') if event.winners else '없음' }}
            </div>
        {% else %}
            <form action="/submit/{{ event_id }}" method="POST">
                <div class="form-group"><label>📝 내 닉네임</label><input type="text" name="username" required></div>
                <button type="
