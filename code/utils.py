# Utils for bot


def get_zno(data, handler_data):

    for j in data:
        for i in j:
            if i['callback_data'] == handler_data:
                subject = i['text']
                return subject


def validate_grade(grade):

    try:
        grade = float(grade)
        
        if (grade >= 100 and grade <= 200) or grade == 0:

            return True

        else:
            raise ValueError

    except ValueError:

        return False


def result_generation(info):
    n = '\n• '
    if info.get('result') == 'additional':
        return f'''
На жаль у вас немає оцiнки з одного з додаткових предметiв:
*•{n.join(info['data'])}*{n.split('•')[0]}
Додайте оцiнку в меню та спробуйте ще раз.'''

    if info['data']['budget'] and info['data']['contract']:
        return f'''
                Ви можете вступити *за бюджетом* до:
• {n.join(info['data']['budget'])} \n*За контрактом* до\
 усiх, де проходите за бюджетом, а також до: 
{n.join(info['data']['contract'])}'''
    elif info['data']['contract'] and not info['data']['budget']:

        return f'''
                Ви можете вступити *лише за контрактом* до:
• {n.join(info['data']['contract'])}'''

    elif info['data']['budget'] and not info['data']['contract']:

        return f'''
                Ви можете вступити *за бюджетом та за контрактом* до:
• {n.join(info['data']['budget'])}'''

    else:
        return 'Нажаль у вас *недостатньо балiв*\
 щоб поступити за цiєю спецiальнiстю'

default_znos = [
"Українська мова та література",
"Українська мова",
"Історія України",
"Іноземна мова",
"Математика",
"Біологія",
"Фізика",
"Хімія",
"Середній бал документа про освіту"]