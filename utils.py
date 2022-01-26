#Utils for bot


def get_zno(data,handler_data):

    for j in data:
        for i in j:
            if i['callback_data'] == handler_data:
                subject = i['text']
                return subject