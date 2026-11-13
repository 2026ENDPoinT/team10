"""Boundary between the existing browser quiz and the tutoring service."""


def text(value, label, limit=4000, required=True):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(f'{label} must be text with at most {limit} characters.')
    value = value.strip()
    if required and not value:
        raise ValueError(f'{label} is required.')
    return value


def validate_payload(data):
    if not isinstance(data, dict):
        raise ValueError('Send a JSON object.')
    message = text(data.get('message'), 'message')
    mode = data.get('mode', 'explain')
    if mode not in ('explain', 'hint', 'practice', 'videos'):
        raise ValueError('mode must be explain, hint, practice or videos.')
    preferences = data.get('preferences', {})
    if not isinstance(preferences, dict):
        raise ValueError('preferences must be an object.')
    clean_preferences = {}
    for field, default, allowed in (
        ('language', 'ko', ('auto', 'en', 'ko')),
        ('level', 'beginner', ('beginner', 'intermediate', 'advanced')),
        ('video_duration', 'any', ('any', 'short', 'medium', 'long')),
    ):
        value = preferences.get(field, default)
        if value not in allowed:
            raise ValueError(f'Invalid preference: {field}.')
        clean_preferences[field] = value
    history = data.get('history', [])
    if not isinstance(history, list) or len(history) > 12:
        raise ValueError('history must contain at most 12 messages.')
    clean_history = []
    for item in history:
        if not isinstance(item, dict) or item.get('role') not in ('user', 'assistant'):
            raise ValueError('History roles must be user or assistant.')
        clean_history.append({'role': item['role'], 'content': text(item.get('content'), 'history content', 12000)})
    if sum(len(item['content']) for item in clean_history) > 30000:
        raise ValueError('Conversation is too long. Start a new chat.')

    context = data.get('quiz_context')
    clean_context = None
    if context is not None:
        if not isinstance(context, dict):
            raise ValueError('quiz_context must be an object.')
        subject = text(context.get('subject', ''), 'subject', 200, required=False)
        questions = context.get('questions')
        if not isinstance(questions, list) or not 1 <= len(questions) <= 10:
            raise ValueError('quiz_context.questions must contain 1 to 10 questions.')
        cleaned = []
        for question in questions:
            if not isinstance(question, dict):
                raise ValueError('Each quiz question must be an object.')
            choices = question.get('choices')
            if not isinstance(choices, list) or len(choices) != 4:
                raise ValueError('Each quiz question needs four choices.')
            choices = [text(choice, 'choice', 1000) for choice in choices]
            answer = question.get('answer')
            selected = question.get('selected_answer')
            if type(answer) is not int or not 0 <= answer < 4:
                raise ValueError('answer must be an index from 0 to 3.')
            if selected is not None and (type(selected) is not int or not 0 <= selected < 4):
                raise ValueError('selected_answer must be null or an index from 0 to 3.')
            cleaned.append({
                'question': text(question.get('question'), 'question', 2000),
                'choices': choices, 'answer': answer, 'selected_answer': selected,
                'explanation': text(question.get('explanation', ''), 'explanation', 2000, required=False),
                'is_correct': selected == answer,
            })
        clean_context = {'subject': subject, 'questions': cleaned}
    return {'message': message, 'mode': mode, 'history': clean_history,
            'quiz_context': clean_context, 'preferences': clean_preferences}
