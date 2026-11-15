"""The profile generator, offline: no request reaches GitHub."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import update_profile as up  # noqa: E402


def repo(name, stars=0, topics=(), description="Does a thing. More text.", **extra):
    return {
        "name": name,
        "html_url": f"https://github.com/ComfyAssets/{name}",
        "stargazers_count": stars,
        "topics": list(topics),
        "description": description,
        "default_branch": "main",
        "fork": False,
        "archived": False,
        "private": False,
        **extra,
    }


class TestRender(unittest.TestCase):
    def test_nodes_and_tools_are_split_by_topic_and_ordered_by_stars(self):
        block = up.render(
            [
                repo("Small", 1, [up.NODE_TOPIC]),
                repo("Big", 50, [up.NODE_TOPIC]),
                repo("App", 9),
            ],
            {},
        )
        nodes, tools = block.split("## Tools and apps")
        self.assertLess(nodes.index("[**Big**]"), nodes.index("[**Small**]"))
        self.assertIn("[**App**]", tools)
        self.assertNotIn("App", nodes)

    def test_a_section_without_repositories_is_left_out(self):
        self.assertNotIn("Tools and apps", up.render([repo("A", topics=[up.NODE_TOPIC])], {}))
        self.assertNotIn("custom nodes", up.render([repo("A")], {}))

    def test_banners_only_for_custom_nodes_that_have_one(self):
        block = up.render([repo("A", 2, [up.NODE_TOPIC]), repo("B", 1, [up.NODE_TOPIC])], {"A": "https://x/a.webp"})
        self.assertIn('<img src="https://x/a.webp" alt="A" width="100%">', block)
        self.assertEqual(block.count("<img"), 1)

    def test_rows_use_the_first_sentence_and_escape_pipes(self):
        self.assertEqual(up.first_sentence("One | two.  Three."), "One \\| two.")
        self.assertEqual(up.first_sentence("No full stop"), "No full stop")
        self.assertEqual(up.first_sentence(None), "")


class TestUpdated(unittest.TestCase):
    def test_only_the_marked_block_changes(self):
        readme = f"intro\n{up.START}\nold\n{up.END}\nfooter\n"
        self.assertEqual(up.updated(readme, "new"), f"intro\n{up.START}\nnew\n{up.END}\nfooter\n")

    def test_missing_or_doubled_markers_stop_the_run(self):
        for readme in ("no markers", f"{up.END}{up.START}", f"{up.START}{up.END}{up.START}{up.END}"):
            with self.assertRaises(SystemExit):
                up.updated(readme, "x")


class TestListing(unittest.TestCase):
    def test_forks_archived_private_hidden_and_this_repo_are_left_out(self):
        pages = [
            [
                repo("Keep"),
                repo("Fork", fork=True),
                repo("Old", archived=True),
                repo("Secret", private=True),
                repo("Hidden", topics=[up.HIDE_TOPIC]),
                repo(".github"),
            ]
        ]
        original = up.get
        up.get = lambda path: pages.pop(0) if pages else []
        try:
            self.assertEqual([r["name"] for r in up.listed_repositories()], ["Keep"])
        finally:
            up.get = original


if __name__ == "__main__":
    unittest.main()
