"""Gemini REST adapter; reuses httpx so no additional installation is needed."""
import json
import re
import httpx


def answer_gemini(payload, config):
    from .service import INSTRUCTIONS, REPLY_FORMAT, TutorError, build_input, parse_reply
    key = config.get('GEMINI_API_KEY', '').strip()
    if not key:
        raise TutorError('.env에 GEMINI_API_KEY를 입력하고 서버를 다시 실행해 주세요.', 503)
    model = config.get('GEMINI_MODEL', 'gemini-3.5-flash-lite')
    if not re.fullmatch(r'gemini-[a-zA-Z0-9.\-]+', model):
        raise TutorError('GEMINI_MODEL 설정을 확인해 주세요.', 503)
    contents = []
    for message in build_input(payload):
        role = 'model' if message['role'] == 'assistant' else 'user'
        part = {'text': message['content']}
        if contents and contents[-1]['role'] == role:
            contents[-1]['parts'].append(part)
        else:
            contents.append({'role': role, 'parts': [part]})
    body = {
        'systemInstruction': {'parts': [{'text': INSTRUCTIONS + '\nCurrent teaching mode: ' + payload['mode']
            + '\nLearning preferences: ' + json.dumps(payload['preferences'])}]},
        'contents': contents,
        'generationConfig': {'maxOutputTokens': 4096, 'responseFormat': {'text': {
            'mimeType': 'APPLICATION_JSON', 'schema': REPLY_FORMAT['schema']}}},
    }
    try:
        response = httpx.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                              headers={'x-goog-api-key': key}, json=body, timeout=45.0)
        if response.status_code == 429:
            raise TutorError('Gemini 사용 한도에 도달했습니다. 잠시 후 다시 시도하거나 AI Studio에서 할당량을 확인해 주세요.', 429)
        if response.status_code == 403:
            # Classify only; never expose the provider's raw message or credentials.
            try:
                provider_message = str(response.json().get('error', {}).get('message', '')).lower()
            except (ValueError, AttributeError):
                provider_message = ''
            if 'free tier is not available' in provider_message or 'free tier unavailable' in provider_message:
                raise TutorError('이 Google 프로젝트는 Gemini 무료 API를 사용할 수 없습니다. AI Studio에서 프로젝트의 무료 등급 자격을 확인해 주세요. 앱에서 결제를 자동으로 활성화하지 않습니다.', 503)
            if 'verification' in provider_message:
                raise TutorError('Google 프로젝트 또는 계정 인증이 필요합니다. AI Studio의 인증 안내를 확인해 주세요.', 503)
        if response.status_code in (400, 401, 403):
            raise TutorError('Gemini API 키, 프로젝트 권한 또는 요청 설정을 확인해 주세요.', 503)
        if response.status_code == 404:
            raise TutorError('이 모델을 사용할 수 없습니다. AI Studio에서 GEMINI_MODEL의 사용 가능 여부를 확인해 주세요.', 503)
        response.raise_for_status()
        data = response.json()
        candidates = data.get('candidates', []) if isinstance(data, dict) else []
        if not candidates:
            raise TutorError('답변을 생성하지 못했습니다. 질문을 다른 표현으로 입력해 주세요.')
        candidate = candidates[0]
        if candidate.get('finishReason') != 'STOP':
            raise TutorError('답변이 완료되지 않았습니다. 질문을 짧게 나누거나 다른 표현으로 시도해 주세요.')
        parts = candidate.get('content', {}).get('parts', [])
        answer = ''.join(p['text'] for p in parts if isinstance(p, dict) and isinstance(p.get('text'), str) and not p.get('thought'))
        return parse_reply(answer)
    except httpx.TimeoutException:
        raise TutorError('Gemini 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.', 504) from None
    except httpx.HTTPError:
        raise TutorError('Gemini에 연결하지 못했습니다. 인터넷 연결 또는 서비스 상태를 확인해 주세요.', 502) from None
    except (ValueError, TypeError, AttributeError, IndexError):
        raise TutorError('Gemini 응답 형식이 올바르지 않습니다. 다시 시도해 주세요.', 502) from None
