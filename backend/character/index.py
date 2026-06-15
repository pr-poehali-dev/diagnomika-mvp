import json
import os
import urllib.request
import base64
import uuid

import boto3


def _openai(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f'https://api.openai.com/v1/{path}',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f"Bearer {os.environ['OPENAI_API_KEY']}",
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode('utf-8'))


def handler(event: dict, context) -> dict:
    '''Создаёт сказочного внутреннего персонажа по ответам интервью.'''
    method = event.get('httpMethod', 'GET')
    cors = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }

    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': {**cors, 'Access-Control-Max-Age': '86400'}, 'body': ''}

    if method != 'POST':
        return {'statusCode': 405, 'headers': cors, 'body': json.dumps({'error': 'Method not allowed'})}

    body = json.loads(event.get('body') or '{}')
    answers = body.get('answers', [])

    qa_text = '\n'.join(f'- {a.get("q", "")}: {a.get("a", "")}' for a in answers)

    system_prompt = """Ты — Архитектор образа жизни в мире Диагномики.
Твоя задача — по ответам человека создать его уникального внутреннего персонажа.
Это не тест и не диагноз. Это живой сказочный образ — отражение его Души, Ума и Тела прямо сейчас.

Правила создания персонажа:
— Имя должно быть красивым, тёплым, немного сказочным (например: Лира, Солм, Ирэй, Тавас, Дорин, Асем, Велар)
— Титул — поэтический, 2-4 слова (например: «Страж тихого света», «Искатель верного пути»)
— Описание — 2-3 живых предложения, как будто ты видишь этого персонажа перед собой. Без клише. Образно и тепло.
— Состояния Души, Ума, Тела — честные, но добрые формулировки (2-4 слова каждое)
— Уровни 0-100 — отражают реальное состояние из ответов, не всегда высокие
— Сила — то, что уже есть в человеке прямо сейчас
— Потребность — то, чего душа просит в тихий момент
— История — маленькая поэтичная зарисовка (2 предложения), как будто ты описываешь сцену из сказки про этого персонажа
— Задание дня — одно конкретное маленькое действие, которое этот персонаж мог бы сделать сегодня. Тёплое, простое, выполнимое.
— image_prompt — детальный prompt на АНГЛИЙСКОМ для DALL-E 3. Стиль: fairy-tale digital art, cinematic warm lighting, bokeh background, highly detailed character portrait, full body or half-body, magical atmosphere, no text, no watermark. Опиши внешность персонажа конкретно: одежда, цвета, выражение лица, окружение.

Отвечай ТОЛЬКО валидным JSON без markdown и пояснений.

Формат ответа:
{
  "name": "имя",
  "title": "титул",
  "description": "описание образа",
  "soul": "состояние Души",
  "soul_level": 75,
  "mind": "состояние Ума",
  "mind_level": 60,
  "body": "состояние Тела",
  "body_level": 55,
  "strength": "сильная сторона",
  "need": "скрытая потребность",
  "story": "поэтичная история персонажа",
  "task": "задание дня",
  "greeting": "первые слова персонажа при знакомстве — тёплое личное обращение к человеку (2-3 предложения от первого лица персонажа)",
  "image_prompt": "detailed English prompt for DALL-E 3"
}"""

    chat = _openai('chat/completions', {
        'model': 'gpt-4o',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'Ответы человека на интервью:\n{qa_text}'},
        ],
        'temperature': 1.0,
        'response_format': {'type': 'json_object'},
    })

    character = json.loads(chat['choices'][0]['message']['content'])

    img = _openai('images/generations', {
        'model': 'dall-e-3',
        'prompt': (
            character.get('image_prompt', '') +
            ' Style: fairy-tale digital art, cinematic warm golden light, magical bokeh, '
            'highly detailed, painterly, no text, no watermark, vertical portrait composition'
        ),
        'n': 1,
        'size': '1024x1024',
        'response_format': 'b64_json',
    })
    img_bytes = base64.b64decode(img['data'][0]['b64_json'])

    s3 = boto3.client(
        's3',
        endpoint_url='https://bucket.poehali.dev',
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    )
    key = f'characters/{uuid.uuid4().hex}.png'
    s3.put_object(Bucket='files', Key=key, Body=img_bytes, ContentType='image/png')
    image_url = f"https://cdn.poehali.dev/projects/{os.environ['AWS_ACCESS_KEY_ID']}/bucket/{key}"

    character['image_url'] = image_url
    character.pop('image_prompt', None)

    return {
        'statusCode': 200,
        'headers': {**cors, 'Content-Type': 'application/json'},
        'isBase64Encoded': False,
        'body': json.dumps(character, ensure_ascii=False),
    }
