import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import rental_pref_service as service


class RentalPreferenceServiceTests(unittest.TestCase):
    def test_save_preference_writes_listing_metadata(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)

            result = service.save_preference(
                repo,
                {
                    "url": "https://example.test/listing/1",
                    "pref": "like",
                    "listing": {
                        "rank": 7,
                        "title": "测试房源",
                        "community": "测试小区",
                        "rent": 3000,
                    },
                },
            )

            data = json.loads((repo / "rental_preferences.json").read_text(encoding="utf-8"))
            saved = data["preferences"]["https://example.test/listing/1"]
            self.assertEqual(result["preference_count"], 1)
            self.assertEqual(saved["pref"], "like")
            self.assertEqual(saved["rank"], 7)
            self.assertEqual(saved["title"], "测试房源")
            self.assertIn("updated_at", saved)

    def test_save_preference_removes_entry_when_pref_is_empty(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            service.save_preference(repo, {"url": "https://example.test/listing/1", "pref": "dislike"})

            result = service.save_preference(repo, {"url": "https://example.test/listing/1", "pref": ""})

            data = json.loads((repo / "rental_preferences.json").read_text(encoding="utf-8"))
            self.assertEqual(result["preference_count"], 0)
            self.assertNotIn("https://example.test/listing/1", data["preferences"])

    def test_save_preference_rejects_unknown_pref(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)

            with self.assertRaises(service.BadRequest):
                service.save_preference(repo, {"url": "https://example.test/listing/1", "pref": "maybe"})

    def test_save_preferences_bulk_writes_multiple_entries_in_one_file_update(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)

            result = service.save_preferences_bulk(
                repo,
                {
                    "preferences": [
                        {
                            "url": "https://example.test/listing/1",
                            "pref": "like",
                            "listing": {"rank": 1, "title": "A"},
                        },
                        {
                            "url": "https://example.test/listing/2",
                            "pref": "dislike",
                            "listing": {"rank": 2, "title": "B"},
                        },
                    ]
                },
            )

            data = json.loads((repo / "rental_preferences.json").read_text(encoding="utf-8"))
            self.assertEqual(result["preference_count"], 2)
            self.assertEqual(data["preferences"]["https://example.test/listing/1"]["pref"], "like")
            self.assertEqual(data["preferences"]["https://example.test/listing/2"]["pref"], "dislike")

    def test_git_commit_and_push_adds_file_commits_and_pushes_current_branch(self):
        calls = []

        def runner(args, cwd):
            calls.append(args)
            if args[:3] == ["git", "status", "--porcelain"]:
                return subprocess.CompletedProcess(args, 0, stdout=" M rental_preferences.json\n", stderr="")
            if args[:3] == ["git", "branch", "--show-current"]:
                return subprocess.CompletedProcess(args, 0, stdout="main\n", stderr="")
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        result = service.git_commit_and_push(Path("repo"), "Update rental preferences", runner=runner)

        self.assertEqual(result["status"], "pushed")
        self.assertEqual(calls[0], ["git", "status", "--porcelain", "--", "rental_preferences.json"])
        self.assertIn(["git", "add", "rental_preferences.json"], calls)
        self.assertIn(["git", "commit", "-m", "Update rental preferences"], calls)
        self.assertIn(["git", "push", "origin", "main"], calls)

    def test_git_commit_and_push_skips_when_file_is_unchanged(self):
        calls = []

        def runner(args, cwd):
            calls.append(args)
            if args[:3] == ["git", "branch", "--show-current"]:
                return subprocess.CompletedProcess(args, 0, stdout="main\n", stderr="")
            if args[:3] == ["git", "rev-list", "--count"]:
                return subprocess.CompletedProcess(args, 0, stdout="0\n", stderr="")
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        result = service.git_commit_and_push(Path("repo"), "Update rental preferences", runner=runner)

        self.assertEqual(result["status"], "unchanged")
        self.assertEqual(
            calls,
            [
                ["git", "status", "--porcelain", "--", "rental_preferences.json"],
                ["git", "branch", "--show-current"],
                ["git", "rev-list", "--count", "origin/main..HEAD"],
            ],
        )

    def test_git_commit_and_push_pushes_when_file_unchanged_but_branch_is_ahead(self):
        calls = []

        def runner(args, cwd):
            calls.append(args)
            if args[:3] == ["git", "status", "--porcelain"]:
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if args[:3] == ["git", "branch", "--show-current"]:
                return subprocess.CompletedProcess(args, 0, stdout="main\n", stderr="")
            if args[:3] == ["git", "rev-list", "--count"]:
                return subprocess.CompletedProcess(args, 0, stdout="3\n", stderr="")
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        result = service.git_commit_and_push(Path("repo"), "Update rental preferences", runner=runner)

        self.assertEqual(result["status"], "pushed")
        self.assertIn(["git", "push", "origin", "main"], calls)


if __name__ == "__main__":
    unittest.main()
