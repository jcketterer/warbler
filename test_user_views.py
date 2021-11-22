import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config["WTF_CSRF_ENABLED"] = False


class MessageViewTestCase(TestCase):
    """Test Vies for messages"""

    def setUp(self):

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(
            username="testuser",
            email="testuser@example.com",
            password="testuser",
            image_url=None,
        )

        self.testuser_id = 8877
        self.testuser.id = self.testuser_id

        self.user1 = User.signup("135", "test1@test.com", "password", None)
        self.user1_id = 999
        self.user1.id = self.user1_id

        self.user2 = User.signup("246", "test2@test.com", "password", None)
        self.user2_id = 888
        self.user2.id = self.user2_id

        self.user3 = User.signup("579", "test3@test.com", "password", None)

        self.user4 = User.signup("testeruser", "test4@test.com", "password", None)

        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_index(self):

        with self.client as c:
            res = c.get("/users")

            self.assertIn("@testuser", str(res.data))
            self.assertIn("@135", str(res.data))
            self.assertIn("@246", str(res.data))
            self.assertIn("@579", str(res.data))
            self.assertIn("@testeruser", str(res.data))

    def test_user_search(self):
        with self.client as c:
            res = c.get("/users?q=test")

            self.assertIn("@testuser", str(res.data))
            self.assertIn("@testeruser", str(res.data))
            self.assertNotIn("@135", str(res.data))
            self.assertNotIn("@246", str(res.data))
            self.assertNotIn("@579", str(res.data))

    def test_user_show(self):
        with self.client as c:
            res = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(res.status_code, 200)

            self.assertIn("@testuser", str(res.data))

    def setup_likes(self):
        m1 = Message(text="test message one", user_id=self.testuser_id)
        m2 = Message(text="test message two", user_id=self.testuser_id)
        m3 = Message(id=4321, text="test message three", user_id=self.user1_id)

        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser_id, message_id=4321)

        db.session.add(l1)
        db.session.commit()

    def test_user_show_with_likes(self):
        self.setup_likes()

        with self.client as c:
            res = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(res.status_code, 200)

            self.assertIn("@testuser", str(res.data))
            soup = BeautifulSoup(str(res.data), "html.parser")
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            self.assertIn("2", found[0].text)
            self.assertIn("0", found[1].text)
            self.assertIn("0", found[2].text)
            self.assertIn("1", found[3].text)

    def test_like_added(self):
        m = Message(id=1988, text="like this please", user_id=self.user1_id)

        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            res = c.post("/messages/1988/like", follow_redirects=True)

            self.assertEqual(res.status_code, 200)

            likes = Likes.query.filter(Likes.message_id == 1988).all()

            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)

    def test_like_removed(self):

        self.setup_likes()

        m = Message.query.filter(Message.text == "test message three").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.testuser_id)

        like = Likes.query.filter(
            Likes.user_id == self.testuser_id and Likes.message_id == m.id
        ).one()

        self.assertIsNotNone(like)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            res = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            likes = Likes.query.filter(Likes.message_id == m.id).all()
            self.assertEqual(len(likes), 0)

    def test_unathenticated_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text == "test message three").one()

        self.assertIsNotNone(m)

        count_like = Likes.query.count()

        with self.client as c:
            res = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            self.assertIn("Access unauthorized", str(res.data))

            self.assertEqual(count_like, Likes.query.count())

    def setup_followers(self):
        f1 = Follows(
            user_being_followed_id=self.user1_id, user_following_id=self.testuser_id
        )
        f2 = Follows(
            user_being_followed_id=self.user2_id, user_following_id=self.testuser_id
        )
        f3 = Follows(
            user_being_followed_id=self.testuser_id, user_following_id=self.user1_id
        )

        db.session.add_all([f1, f2, f3])
        db.session.commit()

    def test_user_show_with_follows(self):

        self.setup_followers()

        with self.client as c:
            res = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(res.status_code, 200)

            self.assertIn("@testuser", str(res.data))
            soup = BeautifulSoup(str(res.data), "html.parser")
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            self.assertIn("0", found[0].text)
            self.assertIn("2", found[1].text)
            self.assertIn("1", found[2].text)
            self.assertIn("0", found[3].text)

    def test_show_following(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            res = c.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(res.status_code, 200)

            self.assertIn("@135", str(res.data))
            self.assertIn("@246", str(res.data))

            self.assertNotIn("@579", str(res.data))
            self.assertNotIn("@testeruser", str(res.data))

    def test_show_followers(self):

        self.setup_followers()
        with self.client as c:

            res = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertNotIn("@135", str(res.data))
            self.assertIn("Access unauthorized", str(res.data))

    def test_unauthed_followers_page(self):

        self.setup_followers()
        with self.client as c:

            res = c.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertNotIn("@135", str(res.data))
            self.assertIn("Access unauthorized", str(res.data))
