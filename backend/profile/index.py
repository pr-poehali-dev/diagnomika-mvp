import json
import os
import psycopg2


SCHEMA = os.environ.get('MAIN_DB_SCHEMA', 't_p13645480_diagnomika_mvp')

CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Session-Token',
}


def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URL'])


def handler(event: dict, context) -> dict:
    '''Профиль пользователя: создаёт сессию, возвращает персонажа и историю.
    GET /  — получить профиль по X-Session-Token
    POST / — создать нового пользователя (возвращает session_token)
    '''
    method = event.get('httpMethod', 'GET')

    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': {**CORS, 'Access-Control-Max-Age': '86400'}, 'body': ''}

    if method == 'POST':
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO {SCHEMA}.users (session_token) VALUES (gen_random_uuid()::text) RETURNING id, session_token"
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {
            'statusCode': 200,
            'headers': {**CORS, 'Content-Type': 'application/json'},
            'body': json.dumps({'user_id': str(row[0]), 'session_token': row[1]}),
        }

    token = event.get('headers', {}).get('x-session-token') or event.get('headers', {}).get('X-Session-Token')
    if not token:
        return {'statusCode': 401, 'headers': CORS, 'body': json.dumps({'error': 'no token'})}

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(f"SELECT id FROM {SCHEMA}.users WHERE session_token = %s", (token,))
    user_row = cur.fetchone()
    if not user_row:
        cur.close()
        conn.close()
        return {'statusCode': 404, 'headers': CORS, 'body': json.dumps({'error': 'user not found'})}

    user_id = user_row[0]

    cur.execute(
        f"""SELECT name, title, description, soul, soul_level, mind, mind_level,
                   body, body_level, strength, need, story, image_url, created_at
            FROM {SCHEMA}.characters WHERE user_id = %s ORDER BY created_at DESC LIMIT 1""",
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
        f"""SELECT task_text, completed, task_date FROM {SCHEMA}.daily_tasks
            WHERE user_id = %s ORDER BY task_date DESC LIMIT 1""",
        (str(user_id),)
    )
    t = cur.fetchone()
    today_task = None
    if t:
        today_task = {'task_text': t[0], 'completed': t[1], 'task_date': str(t[2])}

    cur.execute(
        f"""SELECT day_number, title, entry_text, task_date FROM {SCHEMA}.journey
            WHERE user_id = %s ORDER BY day_number ASC""",
        (str(user_id),)
    )
    journey = [
        {'day_number': r[0], 'title': r[1], 'text': r[2], 'task_date': str(r[3])}
        for r in cur.fetchall()
    ]

    cur.close()
    conn.close()

    return {
        'statusCode': 200,
        'headers': {**CORS, 'Content-Type': 'application/json'},
        'body': json.dumps({
            'user_id': str(user_id),
            'character': character,
            'today_task': today_task,
            'journey': journey,
        }, ensure_ascii=False),
    }
