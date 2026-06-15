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
    '''Создаёт внутреннего персонажа по ответам интервью: текстовое описание через ИИ и изображение.'''
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

    system_prompt = (
        'Ты — мудрый и тёплый проводник в приложении Диагномика. '
        'По ответам человека на интервью создай его внутреннего персонажа, '
        'отражающего состояние Души, Ума и Тела. Отвечай ТОЛЬКО валидным JSON без markdown. '
        'Формат: {"name": "имя персонажа", "title": "короткий титул", '
        '"description": "2-3 предложения образа", '
        '"soul": "состояние Души 2-4 слова", "soul_level": число 0-100, '
        '"mind": "состояние Ума 2-4 слова", "mind_level": число 0-100, '
        '"body": "состояние Тела 2-4 слова", "body_level": число 0-100, '
        '"strength": "сильная сторона 2-3 слова", '
        '"need": "скрытая потребность 2-3 слова", '
        '"story": "короткая тёплая история 2 предложения", '
        '"task": "одно простое задание на день", '
        '"image_prompt": "детальный prompt НА АНГЛИЙСКОМ для генерации изображения персонажа, '
        'fairy-tale realistic style, soft warm light, no text"}'
    )

    chat = _openai('chat/completions', {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'Ответы интервью:\n{qa_text}'},
        ],
        'temperature': 0.9,
        'response_format': {'type': 'json_object'},
    })

    character = json.loads(chat['choices'][0]['message']['content'])

    image_url = ''
    img = _openai('images/generations', {
        'model': 'dall-e-3',
        'prompt': character.get('image_prompt', 'a calm inner spirit character, fairy-tale realistic, soft warm light'),
        'n': 1,
        'size': '1024x1024',
        'response_format': 'b64_json',
    })
    img_b64 = img['data'][0]['b64_json']
    img_bytes = base64.b64decode(img_b64)

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
