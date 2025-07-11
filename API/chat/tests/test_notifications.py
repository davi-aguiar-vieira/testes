from django.test import TestCase
from django.core import mail
from django.contrib.auth import get_user_model
from chat.models import Message, ChatRoom

User = get_user_model()

class NotificationTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="testuser1", email="test1@example.com", password="password123")
        self.user2 = User.objects.create_user(username="testuser2", email="test2@example.com", password="password123")
        self.chatroom = ChatRoom.objects.create(participant_1=self.user1, participant_2=self.user2)

    def test_email_notification_sent_for_new_messages(self):
        Message.objects.create(room=self.chatroom, sender=self.user2, content="Hello user1!")
        Message.objects.create(room=self.chatroom, sender=self.user2, content="How are you?")

        from chat.tasks import send_new_message_notifications
        send_new_message_notifications()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test1@example.com"])
        self.assertIn("Você tem novas mensagens (2)", mail.outbox[0].subject)
        self.assertIn("Você tem 2 novas mensagens não lidas.", mail.outbox[0].body)

    def test_no_email_sent_if_no_new_messages(self):
        from chat.tasks import send_new_message_notifications
        send_new_message_notifications()

        self.assertEqual(len(mail.outbox), 0)
