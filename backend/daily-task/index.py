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

# Колесо баланса Диагномики — 12 направлений, 3 сферы
WHEEL = {
    'soul': {
        'label': 'Душа',
        'subtitle': 'Смысл, принятие, внутренняя опора',
        'directions': {
            'Ценности и миссия': {
                'desc': 'Предназначение, ценности, личная миссия',
                'tasks': [
                    'Запиши одну главную цель на ближайшие 90 дней.',
                    'Ответь письменно: «Что для меня действительно важно сегодня?»',
                ]
            },
            'Эмоциональное принятие': {
                'desc': 'Самопринятие, благодарность, доверие жизни',
                'tasks': [
                    'Напиши 3 вещи, за которые благодарен прямо сейчас.',
                    'Скажи себе вслух: «Я принимаю себя таким, какой я есть сегодня».',
                ]
            },
            'Духовные практики': {
                'desc': 'Медитация, молитва, чтение, развитие души',
                'tasks': [
                    '10 минут медитации на дыхание — просто наблюдай.',
                    '5 минут молитвы, созерцания или чтения вдохновляющего текста.',
                ]
            },
            'Творчество и радость': {
                'desc': 'Хобби, творчество, вдохновение, удовольствие',
                'tasks': [
                    'Нарисовать, написать или создать что-то своими руками.',
                    'Сделать одно фото момента дня, который тебя тронул.',
                    'Сделать один поступок просто ради удовольствия.',
                ]
            },
        }
    },
    'mind': {
        'label': 'Ум',
        'subtitle': 'Ясность, мышление, эмоции, фокус',
        'directions': {
            'Эмоции и стресс': {
                'desc': 'Управление эмоциями, стрессоустойчивость, внутренний баланс',
                'tasks': [
                    'Запиши все тревоги на бумагу и закрой список.',
                    'Сделать дыхательную практику 5 минут: 4 вдох — 4 задержка — 4 выдох.',
                ]
            },
            'Окружение и информация': {
                'desc': 'Круг общения, окружение, информационная гигиена',
                'tasks': [
                    'День без новостей и информационного шума.',
                    'Позвонить человеку, который вдохновляет.',
                    'Провести день без многозадачности.',
                ]
            },
            'Время и фокус': {
                'desc': 'Тайм-менеджмент, приоритеты, фокусировка',
                'tasks': [
                    'Выполнить одну важную задачу за 45 минут без отвлечений.',
                    'Выбросить или отдать 10 ненужных вещей.',
                ]
            },
            'Обучение и развитие': {
                'desc': 'Новые знания, навыки, рост мышления',
                'tasks': [
                    'Прочитать 20 страниц книги.',
                    'Посмотреть один обучающий урок и сделать конспект.',
                    'Устроить себе маленькое приключение в новом месте.',
                ]
            },
        }
    },
    'body': {
        'label': 'Тело',
        'subtitle': 'Энергия, здоровье, физическая основа',
        'directions': {
            'Питание и привычки': {
                'desc': 'Качественная еда, водный баланс, полезные привычки',
                'tasks': [
                    'Выпить 2 литра воды за день — поставь напоминание.',
                    'Один день без сахара и сладких напитков.',
                    'Добавить овощи минимум в два приёма пищи.',
                ]
            },
            'Движение и активность': {
                'desc': 'Тренировки, повседневная активность, гибкость',
                'tasks': [
                    '10 000 шагов за день.',
                    'Сделать 50 приседаний в любом формате.',
                    '15 минут растяжки или мобильности.',
                ]
            },
            'Сон и восстановление': {
                'desc': 'Качественный сон, отдых, режим, восстановление',
                'tasks': [
                    'Лечь спать на 1 час раньше обычного.',
                    'За час до сна убрать телефон и экраны.',
                ]
            },
            'Пространство и порядок': {
                'desc': 'Чистое пространство, минимализм, организация среды',
                'tasks': [
                    'Разобрать один ящик или полку.',
                ]
            },
        }
    },
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

    # Строим компактное описание колеса для промпта
    wheel_desc = []
    for cat_key, cat_val in WHEEL.items():
        dirs = []
        for dir_name, dir_val in cat_val['directions'].items():
            example = dir_val['tasks'][0]
            dirs.append(f'  • {dir_name}: например «{example}»')
        wheel_desc.append(f"{cat_val['label']} ({cat_key}):\n" + '\n'.join(dirs))
    wheel_text = '\n\n'.join(wheel_desc)

    system_prompt = f"""Ты — голос внутреннего персонажа в мире Диагномики.
Твоя задача: выбрать одно задание дня из Колеса баланса Диагномики.

Принцип: Один день. Одна задача. Один результат.

ПРАВИЛО ДНЯ: Сегодня выполняется только выпавшее действие. Не больше и не меньше.

Правила задания:
— Простое, выполнимое за 1–10 минут
— Не требует денег и специальных условий
— Тёплое по тону, конкретное по действию
— НЕ говори «я знаю, как тебе жить» — предлагай проверить одно маленькое действие

КОЛЕСО БАЛАНСА ДИАГНОМИКИ (12 направлений):
{wheel_text}

Состояние персонажа: {categories_context}
{char_context}
{recent_context}

Инструкция:
1. Определи, какая сфера (Душа/Ум/Тело) требует внимания — ориентируйся на уровни персонажа
2. Выбери одно направление из колеса в этой сфере
3. Сформулируй задание — можешь взять пример из колеса или создать похожее в том же духе
4. Задание должно быть вариацией, а не точной копией примера — добавь живую деталь

Ответь ТОЛЬКО валидным JSON:
{{
  "task": "текст задания — одно предложение, тёплое и конкретное",
  "category": "body" или "mind" или "soul",
  "subcategory": "название направления из колеса (например: Питание и привычки)",
  "why": "одно предложение — почему именно это направление сейчас важно"
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