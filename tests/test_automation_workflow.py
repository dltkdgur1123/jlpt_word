import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from src.ops.automation_workflow import (
    AUTOMATION_LEVELS,
    build_publish_schedule,
    collect_pending_upload_entries,
    evaluate_generation_readiness,
)
from src.notifications.telegram_notifier import (
    build_generation_summary_message,
    build_upload_summary_message,
)


class AutomationWorkflowTest(unittest.TestCase):
    def test_automation_levels_include_jlpt_and_business(self):
        self.assertEqual(AUTOMATION_LEVELS, ["N1", "N2", "N3", "N4", "N5", "BUSINESS"])

    def test_evaluate_generation_readiness_detects_exhausted_jlpt_level(self):
        result = evaluate_generation_readiness(
            "N3",
            {"remaining_vocab": 4, "remaining_grammar": 2},
        )

        self.assertFalse(result["ready"])
        self.assertEqual(result["reason"], "insufficient_vocab")

    def test_evaluate_generation_readiness_detects_ready_business_level(self):
        result = evaluate_generation_readiness(
            "BUSINESS",
            {"remaining_vocab": 3, "remaining_phrases": 4},
        )

        self.assertTrue(result["ready"])
        self.assertEqual(result["reason"], "ready")

    def test_build_publish_schedule_starts_next_day_after_latest_reserved_video(self):
        latest_publish_at = "2026-07-06T09:00:00+00:00"

        slots = build_publish_schedule(
            count=4,
            latest_publish_at=latest_publish_at,
            now_kst=datetime(2026, 7, 6, 7, 0, tzinfo=ZoneInfo("Asia/Seoul")),
        )

        self.assertEqual(
            slots,
            [
                "2026-07-06T23:00:00+00:00",
                "2026-07-07T09:00:00+00:00",
                "2026-07-07T23:00:00+00:00",
                "2026-07-08T09:00:00+00:00",
            ],
        )

    def test_build_publish_schedule_uses_tomorrow_when_no_latest_schedule_exists(self):
        slots = build_publish_schedule(
            count=2,
            latest_publish_at=None,
            now_kst=datetime(2026, 7, 6, 7, 0, tzinfo=ZoneInfo("Asia/Seoul")),
        )

        self.assertEqual(
            slots,
            [
                "2026-07-06T23:00:00+00:00",
                "2026-07-07T09:00:00+00:00",
            ],
        )

    def test_collect_pending_upload_entries_returns_generated_not_uploaded_items(self):
        rows = collect_pending_upload_entries(
            {
                "N1_DAY_001": {"level": "N1", "day": "001", "generated": True, "uploaded": False, "updated_at": "2026-07-06T00:00:00+00:00"},
                "N2_DAY_001": {"level": "N2", "day": "001", "generated": True, "uploaded": True, "updated_at": "2026-07-06T01:00:00+00:00"},
                "BUSINESS_DAY_019": {"level": "BUSINESS", "day": "019", "generated": True, "uploaded": False, "updated_at": "2026-07-06T02:00:00+00:00"},
                "N4_DAY_010": {"level": "N4", "day": "010", "generated": False, "uploaded": False, "updated_at": "2026-07-06T03:00:00+00:00"},
            }
        )

        self.assertEqual(
            rows,
            [
                {"upload_key": "N1_DAY_001", "level": "N1", "day": "001", "generated": True, "uploaded": False, "updated_at": "2026-07-06T00:00:00+00:00"},
                {"upload_key": "BUSINESS_DAY_019", "level": "BUSINESS", "day": "019", "generated": True, "uploaded": False, "updated_at": "2026-07-06T02:00:00+00:00"},
            ],
        )



    def test_build_generation_summary_message_keeps_success_short_and_failure_detailed(self):
        message = build_generation_summary_message(
            [
                {"level": "N1", "status": "generated", "day": "057"},
                {"level": "N2", "status": "skipped", "reason": "insufficient_grammar"},
                {"level": "N3", "status": "failed", "reason": "drive token expired"},
            ],
            backlog_ready_count=1,
        )

        self.assertIn("?? ??? ??", message)
        self.assertIn("?? 1", message)
        self.assertIn("?? 1", message)
        self.assertIn("?? 1", message)
        self.assertIn("N3", message)
        self.assertIn("drive token expired", message)

    def test_build_upload_summary_message_lists_reserved_slots_and_failures(self):
        message = build_upload_summary_message(
            [
                {"level": "N1", "day": "057", "status": "uploaded", "publish_at": "2026-07-06T23:00:00+00:00"},
                {"level": "N2", "day": "056", "status": "deferred", "reason": "quota_backoff", "publish_at": "2026-07-07T09:00:00+00:00"},
            ],
            backlog_count=3,
        )

        self.assertIn("??? ??? ??", message)
        self.assertIn("?? 1", message)
        self.assertIn("?? 1", message)
        self.assertIn("?? ??? 3", message)
        self.assertIn("N2 DAY 056", message)
        self.assertIn("quota_backoff", message)

if __name__ == "__main__":
    unittest.main()
