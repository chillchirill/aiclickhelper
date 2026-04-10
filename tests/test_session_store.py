import json
import shutil
import unittest
from pathlib import Path

from aiclickhelper.config import AppConfig
from aiclickhelper.models import ChatMessage, Speaker
from aiclickhelper.session_store import SessionStore


class SessionStoreTests(unittest.TestCase):
    def test_saves_session_as_json_safe_payload(self):
        tmp = Path("tests/.tmp-session-store")
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))

        config = AppConfig(data_root=tmp)
        store = SessionStore(config)
        session = store.create_session()
        session.history.append(ChatMessage.create(Speaker.USER, "hello"))
        store.save_session(session)

        payload = json.loads(store.session_file(session).read_text(encoding="utf-8"))
        self.assertEqual(payload["state"], "idle")
        self.assertEqual(payload["history"][0]["speaker"], "user")


if __name__ == "__main__":
    unittest.main()
