import unittest
from src.llm.json_repair import repair_and_parse_json


class JSONRepairTestCase(unittest.TestCase):
    def test_clean_json_passes(self):
        raw = '{"working_title": "Plan A", "research_objective": "Test objective"}'
        parsed = repair_and_parse_json(raw)
        self.assertEqual(parsed["working_title"], "Plan A")

    def test_markdown_code_fences_stripped(self):
        raw = """```json
        {
            "working_title": "Plan B",
            "research_objective": "Objective B"
        }
        ```"""
        parsed = repair_and_parse_json(raw)
        self.assertEqual(parsed["working_title"], "Plan B")

    def test_trailing_commas_fixed(self):
        raw = """{
            "working_title": "Plan C",
            "candidate_hypotheses": ["H1", "H2",],
            "research_objective": "Objective C",
        }"""
        parsed = repair_and_parse_json(raw)
        self.assertEqual(parsed["working_title"], "Plan C")
        self.assertEqual(parsed["candidate_hypotheses"], ["H1", "H2"])

    def test_unescaped_newlines_in_strings_repaired(self):
        raw = '{\n"working_title": "Plan D",\n"research_objective": "Line 1\nLine 2\nLine 3"\n}'
        parsed = repair_and_parse_json(raw)
        self.assertEqual(parsed["working_title"], "Plan D")
        self.assertIn("Line 1", parsed["research_objective"])

    def test_preamble_and_postamble_stripped(self):
        raw = """Here is the generated plan:
        {
            "working_title": "Plan E",
            "research_objective": "Objective E"
        }
        Hope this helps!"""
        parsed = repair_and_parse_json(raw)
        self.assertEqual(parsed["working_title"], "Plan E")


if __name__ == "__main__":
    unittest.main()
