"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user_1 = User.signup("test1", "email1@email.com", "password", None)
        user_1_id = 1111
        user_1.id = user_1_id

        user_2 = User.signup("test2", "email2@email.com", "password", None)
        user_2_id = 2222
        user_2.id = user_2_id

        db.session.commit()

        user_1 = User.query.get(user_1_id)
        user_2 = User.query.get(user_2_id)

        self.user_1 = user_1
        self.user_1_id = user_1_id

        self.user_2 = user_2
        self.user_2_id = user_2_id

        self.client = app.test_client()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_user_model(self):
        """Does basic model work?"""

        u = User(email="test@test.com", username="testuser", password="HASHED_PASSWORD")

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


def test_follows(self):

    self.user_1.following.append(self.user_2)
    db.session.commit()

    self.assertEqual(len(self.user_2.following), 0)
    self.assertEqual(len(self.user_2.following), 1)
    self.assertEqual(len(self.user_1.following), 0)
    self.assertEqual(len(self.user_1.following), 1)

    self.assertEqual(self.user_2.followers[0].id, self.user_1.id)
    self.assertEqual(self.user_1.followers[0].id, self.user_2.id)


def test_following(self):

    self.user_1.following.append(self.user_2)
    db.session.commit()

    self.assertTrue(self.user_1.is_following(self.user_2))
    self.assertFalse(self.user_2.is_following(self.user_1))


def test_followed_by(self):
    self.user_1.following.append(self.user_2)
    db.session.commit()

    self.assertTrue(self.user_1.is_followed_by(self.user_2))
    self.assertFalse(self.user_2.is_followed_by(self.user_1))


def test_correct_signup(self):
    test_user = User.signup("testermctest", "mctest@tester.com", "password", None)
    user_id = 12345
    user_test_id = user_id
    db.session.commit()

    test_user = User.query.get(user_id)

    self.assertIsNotNone(test_user)
    self.assertEqual(test_user.username, "testermctest")
    self.assertEqual(test_user.email, "mctest@tester.com")
    self.assertNotEqual(test_user.password, "password")
    self.assertTrue(test_user.password.startswith("$2b$"))
