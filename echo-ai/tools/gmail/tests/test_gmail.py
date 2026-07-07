import unittest
import os
import shutil
from tools.gmail.gmail_service import GmailService
from tools.gmail.gmail_utils import extract_email, format_subject, clean_html, save_attachment

class TestGmailService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = os.path.abspath("uploads/test_gmail_temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.service = GmailService()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_utils(self):
        self.assertEqual(extract_email("John Doe <john@example.com>"), "john@example.com")
        self.assertEqual(extract_email("simple@example.com"), "simple@example.com")
        
        self.assertEqual(format_subject("Hello"), "Re: Hello")
        self.assertEqual(format_subject("Re: Hello"), "Re: Hello")
        self.assertEqual(format_subject("re: Hello"), "re: Hello")
        
        self.assertEqual(clean_html("<p>Hello <b>World</b></p>"), "Hello World")
        
        # Test save attachment (base64url for "hello")
        path = save_attachment("aGVsbG8=", "test.txt", self.temp_dir)
        self.assertTrue(os.path.exists(path))
        with open(path, "r") as f:
            self.assertEqual(f.read(), "hello")

    def test_service_mock_read(self):
        # Service defaults to mock client in test mode
        emails = self.service.read_emails(limit=2)
        self.assertEqual(len(emails), 2)
        self.assertEqual(emails[0].id, "msg123")
        self.assertTrue(emails[0].is_unread)

    def test_service_mock_get(self):
        email_msg = self.service.get_email("msg123")
        self.assertEqual(email_msg.id, "msg123")
        self.assertEqual(email_msg.subject, "Mock Subject msg123")

    def test_service_mock_send_reply(self):
        from tools.gmail.gmail_models import EmailRequest, ReplyRequest
        
        send_res = self.service.send_email(EmailRequest(
            recipient="test@example.com",
            subject="Test",
            body="Test body"
        ))
        self.assertEqual(send_res["message_id"], "msg_sent_999")
        
        reply_res = self.service.reply_email("msg123", ReplyRequest(body="Reply text"))
        self.assertEqual(reply_res["message_id"], "msg_sent_999")

if __name__ == "__main__":
    unittest.main()
