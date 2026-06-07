import json
import random
import uuid
import gspread
from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)

# ⚠️ 여기에 제 1단계에서 복사해 둔 내 구글 엑셀 고유 ID를 큰따옴표 안에 넣어주세요!
# 예: SPREADSHEET_ID = "1A2b3C4d5E6fG..." 
SPREADSHEET_ID = "1BfVlyrK3H13DK-soS42P1aU_4Bnt8T5c1wryIP7BF8A"

def get_google_sheet():
    try:
        gc = gspread.public()
        sh = gc.open_by_key(SPREADSHEET_ID)
        return sh.get_worksheet(0)
    except Exception as e:
        print(f"구글 시트 연결 실패: {e}")
        return None

def load_data():
    sheet = get_google_sheet()
    if not sheet: return {}
    try:
        val = sheet.acell('A1').value
        return json.loads(val) if val else {}
    except: return {}

def save_data(data):
    sheet = get_google_sheet()
    if sheet:
        try:
            sheet.update_acell('A1', json.dumps(data, ensure_ascii=False))
        except Exception as e:
            print(f"구글 시트 저장 실패: {e}")

COMMON_STYLE = """<style>
    body { font-family: 'Malgun Gothic', sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; color: #333; }
    .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    h1, h2 { color: #1e3a8a; text-align: center; }
    .form-group { margin-bottom: 15px; }
    label { display: block; margin-bottom: 5px; font-weight: bold; }
    input[type="text"], input[type="number"] { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
    button { width: 100%; padding: 12px; background-color: #2563eb; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; }
    button:hover { background-color: #1d4ed8; }
    .event-card { border: 1px solid #e5e7eb; padding: 20px; border-radius: 8px; margin-top: 20px; background-color: #fff; position: relative; }
    .btn-close { background-color: #10b981; margin-bottom: 5px; }
    .btn-close:hover { background-color: #059669; }
    .btn-delete { background-color: #ef4444; }
    .btn-delete:hover { background-color: #dc2626; }
    .link-box { background: #f3f4f6; padding: 10px; border-radius: 6px; word-break: break-all; font-size: 14px; margin: 10px 0; border: 1px dashed #cbd5e1; }
    .badge { display: inline-block; padding: 4px 8px; background: #dbeafe; color: #1e40af; border-radius: 4px; font-size: 12px; font
