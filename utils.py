# Utils for bot


def get_zno(data, handler_data):

    for j in data:
        for i in j:
            if i['callback_data'] == handler_data:
                subject = i['text']
                return subject


def result_generation(info):
    n = '\n• '
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
        return 'Нажаль ви *не можете вступити* за цiєю спецiальнiстю'
