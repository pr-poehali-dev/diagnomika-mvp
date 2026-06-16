import json
import os
import random
import smtplib
import psycopg2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone


SCHEMA = os.environ.get('MAIN_DB_SCHEMA', 't_p13645480_diagnomika_mvp')

CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Session-Token',
}


def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URL'])


def send_code_email(to_email: str, code: str):
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ['SMTP_USER']
    smtp_pass = os.environ['SMTP_PASS']
    from_name = os.environ.get('SMTP_FROM_NAME', 'Диагномика')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'{code} — твой код входа в Диагномику'
    msg['From'] = f'{from_name} <{smtp_user}>'
    msg['To'] = to_email

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f5f0eb;font-family:-apple-system,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f0eb;padding:40px 20px;">
    <tr><td align="center">
      <table width="480" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:24px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:linear-gradient(135deg,#c9a96e 0%,#e8d5b7 100%);padding:32px;text-align:center;">
            <p style="margin:0;font-size:13px;letter-spacing:.15em;text-transform:uppercase;color:#7a5c2e;font-weight:600;">Диагномика</p>
            <h1 style="margin:8px 0 0;font-size:28px;color:#3d2b0f;font-weight:700;">Добро пожаловать</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:40px 40px 32px;">
            <p style="margin:0 0 24px;font-size:16px;color:#555;line-height:1.6;">Твой код для входа:</p>
            <div style="background:#f9f5f0;border:2px dashed #c9a96e;border-radius:16px;padding:24px;text-align:center;margin:0 0 24px;">
              <p style="margin:0;font-size:48px;font-weight:800;letter-spacing:12px;color:#3d2b0f;font-family:monospace;">{code}</p>
            </div>
            <p style="margin:0;font-size:14px;color:#888;line-height:1.6;">
              Код действителен <strong>10 минут</strong>.<br>
              Если ты не запрашивал вход — просто проигнорируй это письмо.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 40px 32px;border-top:1px solid #f0ebe4;">
            <p style="margin:24px 0 0;font-size:13px;color:#aaa;text-align:center;">
              Диагномика — путь к себе<br><em>Один день. Одна задача. Один шаг.</em>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body></html>"""

    msg.attach(MIMEText(html, 'html', 'utf-8'))
    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.ehlo(); s.starttls(); s.login(smtp_user, smtp_pass)
        s.sendmail(smtp_user, to_email, msg.as_bytes())


def handle_send(body: dict) -> dict:
    email = (body.get('email') or '').strip().lower()
    if not email or '@' not in email:
        return {'statusCode': 400, 'headers': CORS, 'body': json.dumps({'error': 'invalid email'})}

    code = str(random.randint(1000, 9999))
    conn = get_conn(); cur = conn.cursor()
    cur.execute(f"INSERT INTO {SCHEMA}.auth_codes (email, code) VALUES (%s, %s)", (email, code))
    conn.commit(); cur.close(); conn.close()

    send_code_email(email, code)
    return {'statusCode': 200, 'headers': CORS, 'body': json.dumps({'ok': True})}


def handle_verify(body: dict) -> dict:
    email = (body.get('email') or '').strip().lower()
    code = str(body.get('code', '')).strip()
    if not email or not code:
        return {'statusCode': 400, 'headers': CORS, 'body': json.dumps({'error': 'email and code required'})}

    now = datetime.now(timezone.utc)
    conn = get_conn(); cur = conn.cursor()

    cur.execute(
        f"""SELECT id FROM {SCHEMA}.auth_codes
            WHERE email=%s AND code=%s AND used=FALSE AND expires_at>%s
            ORDER BY created_at DESC LIMIT 1""",
        (email, code, now)
    )
    code_row = cur.fetchone()
    if not code_row:
        cur.close(); conn.close()
        return {'statusCode': 401, 'headers': CORS, 'body': json.dumps({'error': 'invalid or expired code'})}

    cur.execute(f"UPDATE {SCHEMA}.auth_codes SET used=TRUE WHERE id=%s", (code_row[0],))

    cur.execute(f"SELECT id, session_token FROM {SCHEMA}.users WHERE email=%s", (email,))
    user_row = cur.fetchone()
    is_new = not bool(user_row)

    if user_row:
        user_id, session_token = str(user_row[0]), user_row[1]
    else:
        cur.execute(
            f"INSERT INTO {SCHEMA}.users (email, session_token) VALUES (%s, gen_random_uuid()::text) RETURNING id, session_token",
            (email,)
        )
        row = cur.fetchone()
        user_id, session_token = str(row[0]), row[1]

    conn.commit(); cur.close(); conn.close()
    return {
        'statusCode': 200, 'headers': CORS,
        'body': json.dumps({'ok': True, 'session_token': session_token, 'user_id': user_id, 'is_new': is_new}),
    }


def handler(event: dict, context) -> dict:
    '''Профиль + авторизация по email-коду.
    POST /send   — отправить код на email
    POST /verify — проверить код, вернуть session_token
    POST /       — создать анонимную сессию (устарело, для совместимости)
    GET  /       — получить профиль по X-Session-Token
    '''
    method = event.get('httpMethod', 'GET')
    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': {**CORS, 'Access-Control-Max-Age': '86400'}, 'body': ''}

    path = (event.get('path') or '/').rstrip('/')
    action = path.split('/')[-1]
    body = json.loads(event.get('body') or '{}')

    if method == 'POST' and action == 'send':
        return handle_send(body)

    if method == 'POST' and action == 'verify':
        return handle_verify(body)

    if method == 'POST':
        # Анонимная сессия (обратная совместимость)
        conn = get_conn(); cur = conn.cursor()
        cur.execute(f"INSERT INTO {SCHEMA}.users (session_token) VALUES (gen_random_uuid()::text) RETURNING id, session_token")
        row = cur.fetchone()
        conn.commit(); cur.close(); conn.close()
        return {'statusCode': 200, 'headers': CORS, 'body': json.dumps({'user_id': str(row[0]), 'session_token': row[1]})}

    # GET — загрузка профиля
    token = (event.get('headers') or {}).get('x-session-token') or (event.get('headers') or {}).get('X-Session-Token')
    if not token:
        return {'statusCode': 401, 'headers': CORS, 'body': json.dumps({'error': 'no token'})}

    conn = get_conn(); cur = conn.cursor()
    cur.execute(f"SELECT id, email FROM {SCHEMA}.users WHERE session_token=%s", (token,))
    user_row = cur.fetchone()
    if not user_row:
        cur.close(); conn.close()
        return {'statusCode': 404, 'headers': CORS, 'body': json.dumps({'error': 'user not found'})}

    user_id, user_email = user_row[0], user_row[1]

    cur.execute(
        f"""SELECT name, title, description, soul, soul_level, mind, mind_level,
                   body, body_level, strength, need, story, image_url, created_at
            FROM {SCHEMA}.characters WHERE user_id=%s ORDER BY created_at DESC LIMIT 1""",
        (str(user_id),)
    )
    ch = cur.fetchone()
    character = None
    if ch:
        character = {
            'name': ch[0], 'title': ch[1], 'description': ch[2],
            'soul': ch[3], 'soul_level': ch[4],
            'mind': ch[5], 'mind_level': ch[6],
            'body': ch[7], 'body_level': ch[8],
            'strength': ch[9], 'need': ch[10],
            'story': ch[11], 'image_url': ch[12],
            'created_at': ch[13].isoformat() if ch[13] else None,
        }

    cur.execute(
        f"""SELECT task_text, completed, task_date, category, subcategory
            FROM {SCHEMA}.daily_tasks WHERE user_id=%s ORDER BY task_date DESC LIMIT 1""",
        (str(user_id),)
    )
    t = cur.fetchone()
    today_task = None
    if t:
        today_task = {'task_text': t[0], 'completed': t[1], 'task_date': str(t[2]), 'category': t[3], 'subcategory': t[4]}

    cur.execute(
        f"SELECT day_number, title, entry_text, task_date FROM {SCHEMA}.journey WHERE user_id=%s ORDER BY day_number ASC",
        (str(user_id),)
    )
    journey = [{'day_number': r[0], 'title': r[1], 'text': r[2], 'task_date': str(r[3])} for r in cur.fetchall()]

    cur.close(); conn.close()
    return {
        'statusCode': 200,
        'headers': {**CORS, 'Content-Type': 'application/json'},
        'body': json.dumps({
            'user_id': str(user_id),
            'email': user_email,
            'character': character,
            'today_task': today_task,
            'journey': journey,
        }, ensure_ascii=False),
    }
