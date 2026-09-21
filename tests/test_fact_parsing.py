import unittest

from backend.fact import _parse_fact_list_response, FactList


class FakeResponse:
    def __init__(self, text="", parsed=None):
        self.text = text
        self.parsed = parsed


class TestFactParsing(unittest.TestCase):
    def test_parse_when_response_is_json_text(self):
        payload = '{"facts": ["A", "B", "C", "D"]}'
        result = _parse_fact_list_response(FakeResponse(text=payload))
        self.assertIsInstance(result, FactList)
        self.assertEqual(len(result.facts), 4)

    def test_parse_when_response_is_fenced_json(self):
        payload = '```json\n{"facts": ["One", "Two", "Three", "Four"]}\n```'
        result = _parse_fact_list_response(FakeResponse(text=payload))
        self.assertEqual(result.facts, ["One", "Two", "Three", "Four"])

    def test_parse_when_response_is_parsed_object(self):
        result = _parse_fact_list_response(FakeResponse(parsed={"facts": ["X", "Y", "Z", "Q"]}))
        self.assertEqual(result.facts, ["X", "Y", "Z", "Q"])


if __name__ == "__main__":
    unittest.main()
