import  base64
import  unittest

from    os2datascanner.engine2.pipeline import (
        explorer, processor, matcher, tagger, exporter)
from    os2datascanner.engine2.model.core import Source
from    os2datascanner.engine2.rules.regex import RegexRule
from    os2datascanner.engine2.rules.logical import OrRule

data = """Hwæt! wē Gār-Dena in gēar-dagum
þēod-cyninga þrym gefrūnon,
hū ðā æþeling as ell en fremedon.
Oft Scyld Scēfing sceaþena þrēatum,
monegum mǣgþum meodo-setla oftēah."""
data_url = "data:text/plain;base64,{0}".format(
       base64.encodebytes(data.encode("utf-8")).decode("ascii"))

rule = OrRule(
        RegexRule("Æthelred the Unready"),
        RegexRule("Scyld S(.*)g"),
        RegexRule("Professor James Moriarty"))

expected_matches = [
    {
        "rule": {
            "type": "regex",
            "expression": "Æthelred the Unready"
        },
        "matches": None
    },
    {
        "rule": {
            "type": "regex",
            "expression": "Scyld S(.*)g"
        },
        "matches": [
            {
                "offset": 98,
                "match": "Scyld Scēfing"
            }
        ]
    }
]


class StopHandling(Exception):
    pass


def handle_message(body, channel):
    if channel == "os2ds_scan_specs":
        return explorer.message_received_raw(body, channel,
                "os2ds_conversions", "os2ds_problems")
    elif channel == "os2ds_conversions":
        return processor.message_received_raw(body, channel,
                "os2ds_representations", "os2ds_scan_specs")
    elif channel == "os2ds_representations":
        return matcher.message_received_raw(body, channel,
                "os2ds_matches", "os2ds_handles", "os2ds_conversions")
    elif channel == "os2ds_handles":
        return tagger.message_received_raw(body, channel,
                "os2ds_metadata")
    elif channel in ("os2ds_matches", "os2ds_metadata", "os2ds_problems",):
        return exporter.message_received_raw(body, channel,
                False, "os2ds_results")
    else:
        return None


class Engine2PipelineTests(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.unhandled = []

    def run_pipeline(self):
        while self.messages:
            (body, channel), self.messages = self.messages[0], self.messages[1:]
            generator = handle_message(body, channel)
            if generator:
                for channel, body in generator:
                    self.messages.append((body, channel,))
            else:
                self.unhandled.append((body, channel,))

    def test_simple_regex_match(self):
        print(Source.from_url(data_url).to_json_object())
        obj = {
            "scan_tag": "integration_test",
            "source": Source.from_url(data_url).to_json_object(),
            "rule": rule.to_json_object()
        }

        self.messages.append((obj, "os2ds_scan_specs",))
        self.run_pipeline()

        self.assertEqual(
                len(self.unhandled),
                2)
        results = {body["origin"]: body for body, _ in self.unhandled}

        self.assertTrue(
                results["os2ds_matches"]["matched"],
                "RegexRule match failed")
        self.assertEqual(
                results["os2ds_matches"]["matches"],
                expected_matches,
                "RegexRule match did not produce expected result")
