import json
import os
import urllib.request
import psycopg2
from datetime import datetime, date

SCHEMA = os.environ.get('MAIN_DB_SCHEMA', 't_p13645480_diagnomika_mvp')

CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Session-Token',
}


def _openai(payload: dict) -> dict:
    req = urllib.request.Request(
        'https://api.openai.com/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f"Bearer {os.environ['OPENAI_API_KEY']}",
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URL'])


def handler(event: dict, context) -> dict:
    '''Отмечает задание дня выполненным и возвращает тёплый отклик персонажа.'''
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': {**CORS, 'Access-Control-Max-Age': '86400'}, 'body': ''}

    token = (event.get('headers') or {}).get('x-session-token') or (event.get('headers') or {}).get('X-Session-Token')
    if not token:
        return {'statusCode': 401, 'headers': CORS, 'body': json.dumps({'error': 'no token'})}

    body = json.loads(event.get('body') or '{}')
    feeling = body.get('feeling', '')

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(f"SELECT id FROM {SCHEMA}.users WHERE session_token = %s", (token,))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        return {'statusCode': 404, 'headers': CORS, 'body': json.dumps({'error': 'user not found'})}

    user_id = str(row[0])
    today = date.today().isoformat()

    cur.execute(
        f"""UPDATE {SCHEMA}.daily_tasks
            SET completed = TRUE, completed_at = %s
            WHERE user_id = %s AND task_date = %s""",
        (datetime.utcnow(), user_id, today)
    )

    cur.execute(
        f"""SELECT task_text, category FROM {SCHEMA}.daily_tasks
            WHERE user_id = %s AND task_date = %s""",
        (user_id, today)
    )
    task_row = cur.fetchone()

    cur.execute(
        f"""SELECT name, title, soul_level, mind_level, body_level
            FROM {SCHEMA}.characters WHERE user_id = %s
            ORDER BY created_at DESC LIMIT 1""",
        (user_id,)
    )
    char_row = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    char_name = char_row[0] if char_row else 'твой персонаж'
    task_text = task_row[0] if task_row else ''
    category = task_row[1] if task_row else 'soul'

    feeling_context = f' Человек написал: «{feeling}».' if feeling else ''

    sphere_map = {'soul': 'Душа (Смысл, принятие, внутренняя опора)', 'mind': 'Ум (Ясность, мышление, эмоции, фокус)', 'body': 'Тело (Энергия, здоровье, физическая основа)'}
    sphere = sphere_map.get(category, category)

    system_prompt = f"""Ты — голос внутреннего персонажа по имени {char_name} в мире Диагномики.
Человек только что выполнил задание из сферы «{sphere}»: «{task_text}».{feeling_context}

Колесо баланса Диагномики включает три сферы — Душа, Ум, Тело — и 12 направлений внутри них.
Каждое выполненное задание делает персонажа чуть ярче в своей сфере.

Напиши тёплый, живой, короткий отклик от лица персонажа — 2-3 предложения.
НЕ хвали банально. Отметь что-то настоящее в этом конкретном действии. Говори «я» и «мы».
Затем — одну мысль-подсказку на завтра: в какую сферу или направление стоит заглянуть дальше.

Ответь ТОЛЬКО валидным JSON:
{{
  "response": "тёплый отклик от лица персонажа (2-3 предложения)",
  "next_hint": "одна мысль на завтра — куда обратить внимание (1 предложение, без конкретного задания)"
}}"""

    result = _openai({
        'model': 'gpt-4o-mini',
        'messages': [{'role': 'system', 'content': system_prompt}],
        'temperature': 0.9,
        'response_format': {'type': 'json_object'},
    })

    data = json.loads(result['choices'][0]['message']['content'])

    return {
        'statusCode': 200,
        'headers': {**CORS, 'Content-Type': 'application/json'},
        'body': json.dumps({
            'ok': True,
            'response': data.get('response', 'Маленький шаг. Настоящий.'),
            'next_hint': data.get('next_hint', 'Завтра — новый день и новый шаг.'),
        }, ensure_ascii=False),
    }