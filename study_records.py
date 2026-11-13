"""퀴즈 오답 노트 / AI 대화 기록 API.

- 성적 데이터와 같은 방식: 세션의 학번 + 비밀번호가 일치하는 자료만 조회·수정할 수 있다.
- 오답은 퀴즈 채점(/ai/api/quiz/grade) 때 서버가 가진 문제 정보로 자동 저장된다 (최대 10개).
- AI 대화는 답변을 받을 때마다 자동 저장된다 (최근 3개).
"""
from flask import jsonify, request, session

from database import (CONVERSATION_LIMIT, WRONG_ANSWER_LIMIT, delete_conversation, delete_wrong_answer,
                      get_conversations, get_wrong_answers, save_conversation)

MAX_MESSAGES = 60            # 대화 하나에 저장되는 메시지 수
MAX_MESSAGE_LENGTH = 12000   # 메시지 하나의 최대 글자 수
MAX_TOTAL_LENGTH = 100000    # 대화 하나의 전체 글자 수
TITLE_LENGTH = 40


class RecordError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def current_account():
    student_id, password = session.get('student_id'), session.get('password')
    if not student_id or not password:
        raise RecordError('로그인이 필요합니다.', 401)
    return student_id, password


def read_json(limit):
    """같은 사이트에서 보낸 JSON 요청만 허용 (다른 사이트가 대신 저장·삭제하지 못하게)."""
    if request.headers.get('Origin', request.host_url.rstrip('/')) != request.host_url.rstrip('/'):
        raise RecordError('다른 사이트의 요청은 허용하지 않습니다.', 403)
    if not request.is_json:
        raise RecordError('JSON 요청이 필요합니다.', 415)
    request.max_content_length = limit
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise RecordError('요청 형식을 확인해 주세요.')
    return data


def error_response(exc):
    return jsonify(error=str(exc)), exc.status


def clean_messages(messages):
    if not isinstance(messages, list) or not 1 <= len(messages) <= MAX_MESSAGES:
        raise RecordError(f'대화는 1~{MAX_MESSAGES}개의 메시지만 저장할 수 있습니다.')
    clean = []
    for item in messages:
        if not isinstance(item, dict) or item.get('role') not in ('user', 'assistant'):
            raise RecordError('대화 형식이 올바르지 않습니다.')
        content = item.get('content')
        if not isinstance(content, str) or not content.strip() or len(content) > MAX_MESSAGE_LENGTH:
            raise RecordError('대화 형식이 올바르지 않습니다.')
        clean.append({'role': item['role'], 'content': content})
    if sum(len(item['content']) for item in clean) > MAX_TOTAL_LENGTH:
        raise RecordError('대화가 너무 길어 저장할 수 없습니다.')
    return clean


def make_title(messages):
    first = next((m['content'] for m in messages if m['role'] == 'user'), messages[0]['content'])
    first = ' '.join(first.split())
    return first if len(first) <= TITLE_LENGTH else first[:TITLE_LENGTH] + '…'


# ---------------- 오답 노트 ----------------
def list_wrong_answers():
    try:
        items = get_wrong_answers(*current_account())
        return jsonify(items=items, limit=WRONG_ANSWER_LIMIT)
    except RecordError as exc:
        return error_response(exc)


def remove_wrong_answer(item_id):
    try:
        account = current_account()
        read_json(1024)
        if not delete_wrong_answer(item_id, *account):
            raise RecordError('저장된 문제를 찾을 수 없습니다.', 404)
        return jsonify(items=get_wrong_answers(*account), limit=WRONG_ANSWER_LIMIT)
    except RecordError as exc:
        return error_response(exc)


# ---------------- AI 대화 기록 ----------------
def list_conversations():
    try:
        return jsonify(items=get_conversations(*current_account()), limit=CONVERSATION_LIMIT)
    except RecordError as exc:
        return error_response(exc)


def store_conversation():
    try:
        account = current_account()
        data = read_json(512 * 1024)
        conversation_id = data.get('id')
        if conversation_id is not None and type(conversation_id) is not int:
            raise RecordError('대화 번호가 올바르지 않습니다.')
        messages = clean_messages(data.get('messages'))
        saved_id = save_conversation(*account, conversation_id, make_title(messages), messages)
        return jsonify(id=saved_id, items=get_conversations(*account), limit=CONVERSATION_LIMIT)
    except RecordError as exc:
        return error_response(exc)


def remove_conversation(conversation_id):
    try:
        account = current_account()
        read_json(1024)
        if not delete_conversation(conversation_id, *account):
            raise RecordError('저장된 대화를 찾을 수 없습니다.', 404)
        return jsonify(items=get_conversations(*account), limit=CONVERSATION_LIMIT)
    except RecordError as exc:
        return error_response(exc)


def init_study_records(app):
    app.add_url_rule('/api/wrong-answers', 'list_wrong_answers', list_wrong_answers, methods=['GET'])
    app.add_url_rule('/api/wrong-answers/<int:item_id>/delete', 'delete_wrong_answer', remove_wrong_answer, methods=['POST'])
    app.add_url_rule('/api/conversations', 'list_conversations', list_conversations, methods=['GET'])
    app.add_url_rule('/api/conversations', 'save_conversation', store_conversation, methods=['POST'])
    app.add_url_rule('/api/conversations/<int:conversation_id>/delete', 'delete_conversation',
                     remove_conversation, methods=['POST'])
