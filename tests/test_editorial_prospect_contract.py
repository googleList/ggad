import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data/editorial-prospects-2026-10-31.json"


class EditorialProspectContractTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FILE.read_text(encoding="utf-8"))

    def test_research_does_not_authorize_outreach(self):
        auth = self.data["authorization"]
        self.assertTrue(auth["research"])
        self.assertTrue(auth["localDrafts"])
        for action in ("sendMessages", "createProfiles", "uploadDrafts", "acceptAgreements", "purchaseLinks"):
            self.assertIs(auth[action], False)
        self.assertTrue(all(c["readyForContact"] is False for c in self.data["candidates"]))

    def test_candidates_use_distinct_official_source_domains(self):
        candidates = self.data["candidates"]
        self.assertEqual(len({c["id"] for c in candidates}), 4)
        for candidate in candidates:
            self.assertTrue(candidate["sources"])
            for source in candidate["sources"]:
                self.assertEqual(urlparse(source).hostname, candidate["officialDomain"])
        self.assertTrue(any("home.blog" in c["url"] for c in self.data["excludedDiscoveries"]))

    def test_unknown_outcomes_are_not_zeroed_or_credited(self):
        metrics = self.data["metrics"]
        self.assertIs(metrics["newGscRead"], False)
        for name in ("liveExternalLinkCount", "newAcquiredLinks", "referralVisits", "organicVisits"):
            self.assertIsNone(metrics[name])
        self.assertIn("No verified Hong Kong", self.data["marketGap"])

    def test_conditional_pitch_preserves_exclusivity_and_human_gates(self):
        candidate = self.data["candidates"][0]
        self.assertEqual(candidate["id"], "ecomcrew")
        self.assertEqual(len(candidate["proposedTitles"]), 3)
        self.assertEqual(len(candidate["proposedOutline"]), 7)
        gates = " ".join(candidate["requiredBeforeSubmission"])
        self.assertIn("human practitioner", gates)
        self.assertIn("exclusive unpublished", gates)
        draft = (ROOT / "reports/authority/2026-10-31-editorial/drafts.md").read_text(encoding="utf-8")
        self.assertIn("AI-assisted", draft)
        self.assertIn("no send before owner approves", draft)
