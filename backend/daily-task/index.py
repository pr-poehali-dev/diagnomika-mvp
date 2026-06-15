import json
import os
import urllib.request
import psycopg2
from datetime import date

SCHEMA = os.environ.get('MAIN_DB_SCHEMA', 't_p13645480_diagnomika_mvp')

CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Session-Token',
}

CATEGORIES = {
    'body':  ['вода', 'дыхание', 'прогулка', 'сон', 'растяжка', 'питание', 'отдых'],
    'mind':  ['фокус', 'порядок', 'запись мыслей', 'выбор одного действия', 'анализ', 'обучение', 'ограничение информационного шума'],
    'soul':  ['благодарность', 'творчество', 'тишина', 'радость', 'принятие', 'внутренний ребёнок', 'доброе действие'],
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
    '''Генерирует задание дня через ИИ, учитывая персонажа и историю выполненных заданий.'''
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': {**CORS, 'Access-Control-Max-Age': '86400'}, 'body': ''}

    token = (event.get('headers') or {}).get('x-session-token') or (event.get('headers') or {}).get('X-Session-Token')
    if not token:
        return {'statusCode': 401, 'headers': CORS, 'body': json.dumps({'error': 'no token'})}

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
        f"SELECT task_text, category, completed FROM {SCHEMA}.daily_tasks WHERE user_id = %s AND task_date = %s",
        (user_id, today)
    )
    existing = cur.fetchone()
    if existing:
        cur.close(); conn.close()
        return {
            'statusCode': 200,
            'headers': {**CORS, 'Content-Type': 'application/json'},
            'body': json.dumps({
                'task': existing[0],
                'category': existing[1] or 'soul',
                'completed': existing[2] or False,
                'is_new': False,
            }, ensure_ascii=False),
        }

    cur.execute(
        f"""SELECT c.soul_level, c.mind_level, c.body_level, c.name, c.title, c.description
            FROM {SCHEMA}.characters c
            WHERE c.user_id = %s
            ORDER BY c.created_at DESC LIMIT 1""",
        (user_id,)
    )
    char_row = cur.fetchone()

    cur.execute(
        f"""SELECT task_text, category FROM {SCHEMA}.daily_tasks
            WHERE user_id = %s AND task_date != %s
            ORDER BY task_date DESC LIMIT 7""",
        (user_id, today)
    )
    recent_tasks = cur.fetchall()

    if char_row:
        soul_l, mind_l, body_l, char_name, char_title, char_desc = char_row
        levels = {'soul': soul_l or 50, 'mind': mind_l or 50, 'body': body_l or 50}
        weakest = min(levels, key=levels.get)
        categories_context = (
            f"Душа: {soul_l}/100, Ум: {mind_l}/100, Тело: {body_l}/100. "
            f"Слабее всего сейчас — {weakest}."
        )
        char_context = f"Персонаж: {char_name}, {char_title}. {char_desc}"
    else:
        weakest = 'soul'
        categories_context = "Данных о персонаже нет."
        char_context = ""

    recent_context = ""
    if recent_tasks:
        recent_list = '; '.join(f'«{t[0]}» ({t[1]})' for t in recent_tasks)
        recent_context = f"\nПоследние задания (не повторяй): {recent_list}"

    system_prompt = f"""Ты — голос внутреннего персонажа в мире Диагномики.
Твоя задача: создать одно задание дня для человека.

Принцип: Один день. Одна задача. Один результат.

Правила задания:
— Простое, выполнимое за 1–10 минут
— Не требует денег и специальных условий
— Связано с Телом, Умом или Душой
— Тёплое по тону, конкретное по действию
— НЕ говори «я знаю, как тебе жить» — предлагай проверить одно маленькое действие

Категории Тела: {', '.join(CATEGORIES['body'])}
Категории Ума: {', '.join(CATEGORIES['mind'])}
Категории Души: {', '.join(CATEGORIES['soul'])}

Состояние персонажа: {categories_context}
{char_context}
{recent_context}

Выбери категорию (body/mind/soul) и подкатегорию с учётом состояния.
Предпочти ту область, которая слабее всего.

Примеры хороших заданий:
— «Выпей стакан воды и 30 секунд поблагодари тело» (body/вода)
— «Запиши одну фразу: что я сейчас на самом деле чувствую?» (soul/запись мыслей)
— «Убери телефон на 10 минут и посиди в тишине» (soul/тишина)
— «Сделай 20 спокойных шагов без музыки» (body/прогулка)
— «Напиши одно действие, которое приблизит тебя к себе» (mind/выбор одного действия)

Ответь ТОЛЬКО валидным JSON:
{{
  "task": "текст задания — одно предложение, тёплое и конкретное",
  "category": "body" | "mind" | "soul",
  "subcategory": "подкатегория из списка",
  "why": "одно предложение — почему именно это задание сейчас"
}}"""

    result = _openai({
        'model': 'gpt-4o-mini',
        'messages': [{'role': 'system', 'content': system_prompt}],
        'temperature': 0.95,
        'response_format': {'type': 'json_object'},
    })

    data = json.loads(result['choices'][0]['message']['content'])
    task_text = data.get('task', 'Выпей стакан воды и 30 секунд поблагодари своё тело.')
    category = data.get('category', 'soul')
    subcategory = data.get('subcategory', '')
    why = data.get('why', '')

    cur.execute(
        f"""INSERT INTO {SCHEMA}.daily_tasks (user_id, task_date, task_text, category, subcategory)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, task_date) DO UPDATE
            SET task_text = EXCLUDED.task_text, category = EXCLUDED.category, subcategory = EXCLUDED.subcategory""",
        (user_id, today, task_text, category, subcategory)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        'statusCode': 200,
        'headers': {**CORS, 'Content-Type': 'application/json'},
        'body': json.dumps({
            'task': task_text,
            'category': category,
            'subcategory': subcategory,
            'why': why,
            'completed': False,
            'is_new': True,
        }, ensure_ascii=False),
    }
