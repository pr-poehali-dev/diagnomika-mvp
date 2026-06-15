import json
import os
import psycopg2
from datetime import datetime, date

SCHEMA = os.environ.get('MAIN_DB_SCHEMA', 't_p13645480_diagnomika_mvp')

CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Session-Token',
}


def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URL'])


def handler(event: dict, context) -> dict:
    '''Отмечает задание дня выполненным.'''
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': {**CORS, 'Access-Control-Max-Age': '86400'}, 'body': ''}

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

    user_id = str(user_row[0])
    today = date.today().isoformat()

    cur.execute(
        f"""UPDATE {SCHEMA}.daily_tasks
            SET completed = TRUE, completed_at = %s
            WHERE user_id = %s AND task_date = %s""",
        (datetime.utcnow(), user_id, today)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {
        'statusCode': 200,
        'headers': {**CORS, 'Content-Type': 'application/json'},
        'body': json.dumps({'ok': True}),
    }
