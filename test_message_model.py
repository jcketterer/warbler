import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from sqlalchemy import exc

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"

from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Testing views from messages"""

    def setUp(self):

        db.drop_all()
        db.create_all()

        self.user_id = 85250

        user = User.signup("tester", "tester@tester.com", "password", None)

        user.id = self.user_id

        self.user = User.query.get(self.user_id)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()

        return res

    def test_message_model(self):

        m = Message(text="test text", user_id=self.user_id)

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, "test text")

    def test_message_likes(self):
        m1 = Message(text="test text", user_id=self.user_id)

        m2 = Message(text="More tests for the testing tester", user_id=self.user_id)

        user = User.signup("onemoretestiswear", "iswear@test.com", "password", None)
        user_id = 85258
        user.id = user_id

        db.session.add_all([m1, m2, user])
        db.session.commit()

        user.likes.append(m1)

        db.session.commit()

        like = Likes.query.filter(Likes.user_id == user_id).all()

        self.assertEqual(len(like), 1)
        self.assertEqual(like[0].message_id, m1.id)
