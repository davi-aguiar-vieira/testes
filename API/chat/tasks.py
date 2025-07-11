from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from chat.models import Message, ChatRoom
from django.conf import settings

User = get_user_model()

@shared_task
def send_new_message_notifications():
    users = User.objects.all()

    for user in users:
        new_messages_count = 0
        chatrooms_as_p1 = ChatRoom.objects.filter(participant_1=user)
        chatrooms_as_p2 = ChatRoom.objects.filter(participant_2=user)

        all_chatrooms = list(set(list(chatrooms_as_p1) + list(chatrooms_as_p2)))

        for chatroom in all_chatrooms:
            other_participant = None
            if chatroom.participant_1 == user:
                other_participant = chatroom.participant_2
            elif chatroom.participant_2 == user:
                other_participant = chatroom.participant_1

            if other_participant:
                new_messages_count += Message.objects.filter(room=chatroom, sender=other_participant).count()

        if new_messages_count > 0:
            subject = f'Você tem novas mensagens ({new_messages_count})'
            message = f'Você tem {new_messages_count} novas mensagens não lidas. Acesse o AcheiUnB para visualizá-las.'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [user.email]
            try:
                send_mail(subject, message, from_email, recipient_list)
            except Exception as e:
                print(f"Erro ao enviar e-mail para {user.email}: {e}")
