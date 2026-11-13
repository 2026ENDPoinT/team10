"""Groq chat adapter. Credentials stay on the Flask server."""
import json

import httpx


def answer_groq(payload, config):
    from .service import INSTRUCTIONS, REPLY_FORMAT, TutorError, build_input, parse_reply

    key = config.get('GROQ_API_KEY', '').strip()
    if not key:
        raise TutorError('.env에 GROQ_API_KEY를 입력하고 서버를 다시 실행해 주세요.', 503)
    body = {
        'model': config.get('GROQ_MODEL', 'openai/gpt-oss-120b'),
        'messages': [{'role': 'system', 'content': INSTRUCTIONS
            + '\nCurrent teaching mode: ' + payload['mode']
            + '\nLearning preferences: ' + json.dumps(payload['preferences'])}] + build_input(payload),
        'max_completion_tokens': 4096,
        'reasoning_effort': 'low',
        'response_format': {'type': 'json_schema', 'json_schema': {
            'name': REPLY_FORMAT['name'], 'strict': True, 'schema': REPLY_FORMAT['schema']}},
    }
    return parse_reply(request_groq(body, key)['choices'][0]['message']['content'])


def request_groq(body, key):
    from .service import TutorError
    if not key:
        raise TutorError('.env에 GROQ_API_KEY를 입력하고 서버를 다시 실행해 주세요.', 503)
    try:
        response = httpx.post('https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': 'Bearer ' + key}, json=body, timeout=45.0)
        if response.status_code == 429:
            raise TutorError('Groq 무료 사용 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.', 429)
        if response.status_code in (401, 403):
            raise TutorError('Groq API 키 또는 모델 사용 권한을 확인해 주세요.', 503)
        if response.status_code in (400, 404):
            raise TutorError('Groq 모델 또는 요청 설정을 확인해 주세요.', 503)
        response.raise_for_status()
        data = response.json()
        choice = data['choices'][0]
        if choice.get('finish_reason') != 'stop':
            raise TutorError('답변이 완료되지 않았습니다. 질문을 짧게 나누어 다시 시도해 주세요.')
        if not isinstance(choice['message']['content'], str):
            raise ValueError()
        return data
    except httpx.TimeoutException:
        raise TutorError('Groq 응답 시간이 초과되었습니다. 다시 시도해 주세요.', 504) from None
    except httpx.HTTPError:
        raise TutorError('Groq에 연결하지 못했습니다. 인터넷 연결 또는 서비스 상태를 확인해 주세요.', 502) from None
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        raise TutorError('Groq 응답 형식이 올바르지 않습니다. 다시 시도해 주세요.', 502) from None
