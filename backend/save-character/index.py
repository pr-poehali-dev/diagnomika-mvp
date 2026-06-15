import json
import os
import psycopg2
from datetime import date

SCHEMA = os.environ.get('MAIN_DB_SCHEMA', 't_p13645480_diagnomika_mvp')

CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Session-Token',
}


def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URL'])


def handler(event: dict, context) -> dict:
    '''Сохраняет сгенерированного персонажа и задание дня в БД.
    POST / — { character: {...}, task: "..." }
    Заголовок X-Session-Token обязателен.
    '''
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': {**CORS, 'Access-Control-Max-Age': '86400'}, 'body': ''}

    token = event.get('headers', {}).get('x-session-token') or event.get('headers', {}).get('X-Session-Token')
    if not token:
        return {'statusCode': 401, 'headers': CORS, 'body': json.dumps({'error': 'no token'})}

    body = json.loads(event.get('body') or '{}')
    ch = body.get('character', {})
    task_text = body.get('task', '')

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(f"SELECT id FROM {SCHEMA}.users WHERE session_token = %s", (token,))
    user_row = cur.fetchone()
    if not user_row:
        cur.close()
        conn.close()
        return {'statusCode': 404, 'headers': CORS, 'body': json.dumps({'error': 'user not found'})}

    user_id = str(user_row[0])

    cur.execute(
        f"""INSERT INTO {SCHEMA}.characters
            (user_id, name, title, description, soul, soul_level, mind, mind_level,
             body, body_level, strength, need, story, image_url)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            user_id,
            ch.get('name', ''), ch.get('title', ''), ch.get('description', ''),
            ch.get('soul', ''), ch.get('soul_level', 50),
            ch.get('mind', ''), ch.get('mind_level', 50),
            ch.get('body', ''), ch.get('body_level', 50),
            ch.get('strength', ''), ch.get('need', ''),
            ch.get('story', ''), ch.get('image_url', ''),
        )
    )

    today = date.today().isoformat()
    cur.execute(
        f"""INSERT INTO {SCHEMA}.daily_tasks (user_id, task_date, task_text)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, task_date) DO UPDATE SET task_text = EXCLUDED.task_text""",
        (user_id, today, task_text)
    )

    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.journey WHERE user_id = %s",
        (user_id,)
    )
    day_count = cur.fetchone()[0] + 1

    cur.execute(
        f"""INSERT INTO {SCHEMA}.journey (user_id, day_number, title, entry_text, task_date)
            VALUES (%s, %s, %s, %s, %s)""",
        (user_id, day_count, 'Знакомство' if day_count == 1 else f'День {day_count}',
         f'Ты создал персонажа {ch.get("name", "")}. Твой путь начался.' if day_count == 1
         else f'Персонаж обновлён. Путь продолжается.', today)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {
        'statusCode': 200,
        'headers': {**CORS, 'Content-Type': 'application/json'},
        'body': json.dumps({'ok': True}, ensure_ascii=False),
    }
