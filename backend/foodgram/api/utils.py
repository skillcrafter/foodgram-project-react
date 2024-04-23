from django.conf.global_settings import DEFAULT_FROM_EMAIL
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound

def send_message_to_user(username, recipient_email, confirmation_code):
    send_mail(
        subject='Код подтверждения Foodgram',
        message=f'Здравствуйте, {username} \n\n'
                f'Вы получили это сообщение, '
                f'так как на адрес электронной почты: \n'
                f' {recipient_email}\n'
                f'происходит регистрация на сайте "Foodgram". \n  \n'
                f'Ваш код подтверждения : {confirmation_code} \n \n'
                f'Если Вы не пытались зарегистрироваться - \n'
                f'просто не отвечайте на данное сообщение и \n'
                f'не производите никаких действий',
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=(recipient_email,),
    )


def make_confirmation_code(data):
    # print('!!!!!!!!!!!!!!!! Для создания кода поступило: ', data)
    confirmation_code = default_token_generator.make_token(data)
    return confirmation_code


def get_object_or_400(model, *args, **kwargs):
    try:
        return get_object_or_404(model, *args, **kwargs)
    except model.DoesNotExist:
        raise NotFound(detail="Object not found", code=400)
