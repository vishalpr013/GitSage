"""Shared test fixtures for git-sage."""

import pytest


SAMPLE_DIFF = """\
diff --git a/src/auth.py b/src/auth.py
index abc1234..def5678 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,5 +10,11 @@ class AuthService:
     def __init__(self):
         self.db = Database()
 
+    def login(self, username, password):
+        user = self.db.find_user(username)
+        if user.password == password:
+            return {"token": "abc123", "user": user}
+        return None
+
     def logout(self):
         pass
"""

SAMPLE_DIFF_WITH_SECRET = """diff --git a/config.py b/config.py
index abc1234..def5678 100644
--- a/config.py
+++ b/config.py
@@ -1,3 +1,5 @@
 import os
 
-API_KEY = os.getenv("API_KEY")
+API_KEY = "sk-1234567890abcdef"
+DB_PASSWORD = "admin123"
+SECRET = os.getenv("SECRET")
"""

EMPTY_DIFF = ""


@pytest.fixture
def sample_diff():
    """A sample diff with a potential bug (plaintext password comparison)."""
    return SAMPLE_DIFF


@pytest.fixture
def sample_diff_with_secret():
    """A sample diff with hardcoded secrets."""
    return SAMPLE_DIFF_WITH_SECRET


@pytest.fixture
def empty_diff():
    """An empty diff."""
    return EMPTY_DIFF
