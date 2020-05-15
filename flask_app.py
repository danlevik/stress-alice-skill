from flask import Flask, request
import logging
import json
from random import choice
import csv
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)


# создаем словарь, где для каждого пользователя
# мы будем хранить его имя и другие данные
sessionStorage = {}
with open('stress.csv', encoding='windows-1251') as csvfile:
    reader = csv.reader(csvfile, delimiter=';', quotechar='"')
    words = [(i[0], i[1]) for i in reader]


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Я помогу тебе подготовиться к заданию №4 ЕГЭ по русскому языку.\nКак тебя зовут?'
        sessionStorage[user_id] = {
            'first_name': None,
            'training_prepare': False,
            'training': False,
            'training_good': 0,
            'training_wrong': 0,
            'game_mode_prepare': False,
            'game_mode': False,
            'game_mode_good': 0,
            'health': 4,
            'now_word': None
        }
        return

    if any(i in req['request']['original_utterance'].lower() for i in ['помощь', 'что ты умеешь', 'что ты можешь', 'как ты работаешь']):
        res['response']['text'] = 'Этот навык призван помочь ученикам выпускных классов в подготовке к ЕГЭ по русскому языку, ' \
                                  'а именно к заданию №4 на орфоэпические нормы.\n' \
                                  'В навыке доступно 2 режима: Тренировка и Игровой режим.\n' \
                                  'Тренировка предлагает слова, которые пользователь должен попытаться написать с правильным ударением. ' \
                                  'По окончании тренировки выводится статистика верных и неверных ответов.\n' \
                                  'В игровом режиме пользователь отвечает на вопросы до тех пор, пока не совершит 3 ошибки. ' \
                                  'После этого игра заканчивается и выводится количество правильных ответов.'


    elif sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Это не похоже на имя. Повтори, пожалуйста!'
        else:

            sessionStorage[user_id]['first_name'] = first_name

            res['response']['text'] = f'Приятно познакомиться, {sessionStorage[user_id]["first_name"].title()}! ' \
                                      f'Попробуй режим тренировки или игровой режим.\n' \
                                      f'Для этого напиши "Тренировка" или "Игра".'
            res['response']['buttons'] = [
                {
                    'title': 'Тренировка',
                    'hide': True
                },
                {
                    'title': 'Игра',
                    'hide': True
                },
                {
                    'title': 'Прощай',
                    'hide': True
                }
            ]
    else:
        # У нас уже есть имя, и теперь мы ожидаем ответ на предложение.
        if sessionStorage[user_id]['training']:
            training_func(res, req)
            return

        if sessionStorage[user_id]['game_mode']:
            game_func(res, req)
            return


        # проверки для начала тренировочного режима
        if not sessionStorage[user_id]['training_prepare'] and not sessionStorage[user_id]['game_mode_prepare']:
            # если пользователь еще не начал
            if 'тренировка' in req['request']['nlu']['tokens']:

                sessionStorage[user_id]['training_prepare'] = True

                res['response']['text'] = 'Отлично! Я буду называть слова, а ты пиши их с верно выделенным ударением.\n' \
                                          'Если захочешь закончить, напиши "Конец" ' \
                                          'и я выведу статистику верных и неверных ответов.\nТы готов?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    }
                ]
            elif 'игра' in req['request']['nlu']['tokens']:

                sessionStorage[user_id]['game_mode_prepare'] = True

                res['response']['text'] = 'Отлично! В этом режиме ты должен правильно выделять ударения. ' \
                                          'При этом у тебя есть всего 3 права на ошибку. ' \
                                          'Постарайся дать как можно больше правильных ответов.\n' \
                                          'Если захочешь закончить раньше, напиши "Конец" ' \
                                          'и я выведу количество верных ответов.\nТы готов?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    }
                ]

            elif 'прощай' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Хорошо. До свидания!'
                res['response']['end_session'] = True
            else:
                res['response']['text'] = f'Я Вас не понимаю, {sessionStorage[user_id]["first_name"].title()}.\n' \
                                          f'Напишите "Тренировка" для тренировочного режима, "Игра" для игрового режима ' \
                                          f'или "Прощай", чтобы закончить диалог'
                res['response']['buttons'] = [
                    {
                        'title': 'Тренировка',
                        'hide': True
                    },
                    {
                        'title': 'Игра',
                        'hide': True
                    },
                    {
                        'title': 'Прощай',
                        'hide': True
                    }
                ]


        # пользователь увидел информацию о тренировочном режиме
        elif sessionStorage[user_id]['training_prepare']:
            if 'нет' in req['request']['original_utterance'].lower():
                res['response']['text'] = 'Ну ладно, попробуй другой режим'
                res['response']['buttons'] = [
                    {
                        'title': 'Тренировка',
                        'hide': True
                    },
                    {
                        'title': 'Игра',
                        'hide': True
                    },
                    {
                        'title': 'Прощай',
                        'hide': True
                    }
                ]

                sessionStorage[user_id]['training_prepare'] = False

            elif 'да' in req['request']['original_utterance'].lower():

                sessionStorage[user_id]['training'] = True

                training_func(res, req, first_try=True)

            else:
                res['response']['text'] = f'Я тебя не понимаю, {sessionStorage[user_id]["first_name"].title()}. ' \
                                          f'Ответь "Да" или "Нет"'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    }
                ]

        # пользователь увидел информацию об игровом режиме
        elif sessionStorage[user_id]['game_mode_prepare']:
            if 'нет' in req['request']['original_utterance'].lower():
                res['response']['text'] = 'Ну ладно, попробуй другой режим'
                res['response']['buttons'] = [
                    {
                        'title': 'Тренировка',
                        'hide': True
                    },
                    {
                        'title': 'Игра',
                        'hide': True
                    },
                    {
                        'title': 'Прощай',
                        'hide': True
                    }
                ]

                sessionStorage[user_id]['game_mode_prepare'] = False

            elif 'да' in req['request']['original_utterance'].lower():

                sessionStorage[user_id]['game_mode'] = True

                game_func(res, req, first_try=True)

            else:
                res['response']['text'] = f'Я тебя не понимаю, {sessionStorage[user_id]["first_name"].title()}. ' \
                                          f'Ответь "Да" или "Нет"'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    }
                ]


def training_func(res, req, first_try=False):
    user_id = req['session']['user_id']

    if first_try:
        word = choice(words)
        sessionStorage[user_id]['now_word'] = word

        res['response']['text'] = f'Какое ударение в слове: {word[1]}'
        res['response']['tts'] = 'Какое ударение в слове?'
        res['response']['buttons'] = make_buttons(word)
    else:
        # выход из тренировочного режима
        if req['request']['original_utterance'].lower() == 'конец':
            res['response']['text'] = f'Твоя статистика за тренировку:\n' \
                                      f'Правильно: {sessionStorage[user_id]["training_good"]} слов\n' \
                                      f'Неправильно: {sessionStorage[user_id]["training_wrong"]} слов\n' \
                                      f'Обязательно попробуй игровой режим \U0001F60E'
            res['response']['buttons'] = [
                {
                    'title': 'Тренировка',
                    'hide': True
                },
                {
                    'title': 'Игра',
                    'hide': True
                },
                {
                    'title': 'Прощай',
                    'hide': True
                }
            ]
            sessionStorage[user_id]['training'] = False
            sessionStorage[user_id]['training_prepare'] = False
            sessionStorage[user_id]["training_good"] = 0
            sessionStorage[user_id]["training_wrong"] = 0

        # верный ответ
        elif req['request']['original_utterance'] == sessionStorage[user_id]['now_word'][0]:
            word = choice(words)
            sessionStorage[user_id]['now_word'] = word
            sessionStorage[user_id]["training_good"] += 1
            res['response']['text'] = f'Верно, молодец! \U0001F929\nКакое ударение в слове: {word[1]}'
            res['response']['tts'] = 'Верно, молодец! Какое ударение в слове?'
            res['response']['buttons'] = make_buttons(word)

        # слово отличается от необходимого
        elif req['request']['original_utterance'].lower() != sessionStorage[user_id]['now_word'][0].lower():
            res['response']['text'] = f'Слово написано неправильно, попробуй ещё раз'
            res['response']['buttons'] = make_buttons(sessionStorage[user_id]['now_word'])

        # несколько ударений
        elif sum([c.isupper() for c in req['request']['original_utterance']]) > 1:
            res['response']['text'] = f'Ты выделил несколько ударений, попробуй ещё раз'
            res['response']['buttons'] = make_buttons(sessionStorage[user_id]['now_word'])

        # ударение не выделено
        elif req['request']['original_utterance'] == sessionStorage[user_id]['now_word'][0].lower():
            res['response']['text'] = f'Ты не выделил ударение, попробуй ещё раз'
            res['response']['buttons'] = make_buttons(sessionStorage[user_id]['now_word'])

        # неправильное ударение
        elif req['request']['original_utterance'] != sessionStorage[user_id]['now_word'][0]:
            word = choice(words)
            sessionStorage[user_id]["training_wrong"] += 1
            res['response']['text'] = f'Неправильно!\U0001F615 Верный ответ: {sessionStorage[user_id]["now_word"][0]}\n' \
                                      f'Какое ударение в слове: {word[1]}'
            res['response']['tts'] = 'Неправильно! Какое ударение в слове?'
            res['response']['buttons'] = make_buttons(word)
            sessionStorage[user_id]['now_word'] = word


def game_func(res, req, first_try=False):
    user_id = req['session']['user_id']

    if first_try:
        word = choice(words)
        sessionStorage[user_id]['now_word'] = word

        res['response']['text'] = f'Какое ударение в слове: {word[1]}'
        res['response']['tts'] = 'Какое ударение в слове?'
        res['response']['buttons'] = make_buttons(word)
    else:
        # выход из игрового режима
        if req['request']['original_utterance'].lower() == 'конец':
            res['response']['text'] = f'Ты верно ответил на {sessionStorage[user_id]["game_mode_good"]} вопросов, молодец'
            res['response']['buttons'] = [
                {
                    'title': 'Тренировка',
                    'hide': True
                },
                {
                    'title': 'Игра',
                    'hide': True
                },
                {
                    'title': 'Прощай',
                    'hide': True
                }
            ]
            sessionStorage[user_id]['game_mode'] = False
            sessionStorage[user_id]['game_mode_prepare'] = False
            sessionStorage[user_id]["game_mode_good"] = 0
            sessionStorage[user_id]["health"] = 3

        # верный ответ
        elif req['request']['original_utterance'] == sessionStorage[user_id]['now_word'][0]:
            word = choice(words)
            sessionStorage[user_id]['now_word'] = word
            sessionStorage[user_id]["game_mode_good"] += 1
            res['response']['text'] = f'Верно, молодец! \U0001F929\nКакое ударение в слове: {word[1]}'
            res['response']['tts'] = 'Верно, молодец! Какое ударение в слове?'
            res['response']['buttons'] = make_buttons(word)

        # слово отличается от необходимого
        elif req['request']['original_utterance'].lower() != sessionStorage[user_id]['now_word'][0].lower():
            res['response']['text'] = f'Слово написано неправильно, попробуй ещё раз'
            res['response']['buttons'] = make_buttons(sessionStorage[user_id]['now_word'])

        # несколько ударений
        elif sum([c.isupper() for c in req['request']['original_utterance']]) > 1:
            res['response']['text'] = f'Ты выделил несколько ударений, попробуй ещё раз'
            res['response']['buttons'] = make_buttons(sessionStorage[user_id]['now_word'])

        # ударение не выделено
        elif req['request']['original_utterance'] == sessionStorage[user_id]['now_word'][0].lower():
            res['response']['text'] = f'Ты не выделил ударение, попробуй ещё раз'
            res['response']['buttons'] = make_buttons(sessionStorage[user_id]['now_word'])

        # неправильное ударение
        elif req['request']['original_utterance'] != sessionStorage[user_id]['now_word'][0]:
            word = choice(words)
            sessionStorage[user_id]['health'] -= 1
            res['response']['text'] = f'Неправильно!\U0001F615\nВерный ответ: {sessionStorage[user_id]["now_word"][0]}\n'\
                                      + 'Осталось попыток: {}\n' \
                                        'Какое ударение в слове: {}'.format(sessionStorage[user_id]["health"] * '\U0001F9E1', word[1])
            res['response']['tts'] = 'Неправильно! Осталось попыток: {}. Какое ударение в слове?'.format(sessionStorage[user_id]["health"])
            res['response']['buttons'] = make_buttons(word)
            sessionStorage[user_id]['now_word'] = word

            if sessionStorage[user_id]["health"] == 0:
                res['response']['text'] = f'Неправильно! Верный ответ: {sessionStorage[user_id]["now_word"][0]}\n' \
                                          f'Попытки закончились. Конец игры!\n' \
                                          f'Ты верно ответил на {sessionStorage[user_id]["game_mode_good"]} вопросов, молодец!'
                res['response']['tts'] = 'Неправильно! Конец игры!'
                sessionStorage[user_id]['game_mode'] = False
                sessionStorage[user_id]['game_mode_prepare'] = False
                sessionStorage[user_id]["game_mode_good"] = 0
                sessionStorage[user_id]["health"] = 3
                res['response']['buttons'] = [
                    {
                        'title': 'Тренировка',
                        'hide': True
                    },
                    {
                        'title': 'Игра',
                        'hide': True
                    },
                    {
                        'title': 'Прощай',
                        'hide': True
                    }
                ]


def make_buttons(word):
    buttons = []
    for i in enumerate(word[1]):
        if i[1] in 'ёуеыаоэяию':
            w_list = list(word[1])
            w_list[i[0]] = w_list[i[0]].capitalize()
            w = ''.join(w_list)
            buttons.append({
                'title': w,
                'hide': True
            })
    buttons.append({
        'title': 'КОНЕЦ',
        'hide': True
    })
    return buttons


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()