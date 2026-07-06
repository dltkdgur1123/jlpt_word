import tempfile
import unittest
from pathlib import Path

from src.cleanup.asset_cleanup import cleanup_generated_assets_for_compilation_range
from src.ops.compilation_sources import (
    build_compilation_source_status,
    ensure_compilation_sources,
)
from src.ops.day_regeneration import (
    build_regeneration_preview,
    classify_generation_day,
)
from src.ops.dashboard_status import (
    build_storage_summary,
    read_log_tail,
)


class OpsHelpersTest(unittest.TestCase):
    def test_build_compilation_source_status_reports_local_and_drive_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            day_root = root / "output" / "day_videos"
            thumb_root = root / "output" / "thumbnails"
            log_data = {
                "N3_DAY_001": {"drive_backed_up": True, "drive_video_file_id": "drive-1"},
                "N3_DAY_002": {"drive_backed_up": False},
                "N3_DAY_003": {"drive_backed_up": True, "drive_video_file_id": "drive-3"},
            }

            (day_root / "N3").mkdir(parents=True)
            (day_root / "N3" / "N3_DAY_001.mp4").write_bytes(b"video")
            thumb_root.mkdir(parents=True)
            (thumb_root / "N3_DAY_001.jpg").write_bytes(b"thumb")

            rows = build_compilation_source_status(
                ["N3"],
                1,
                3,
                day_video_root=day_root,
                thumbnail_root=thumb_root,
                log_data=log_data,
            )

            self.assertEqual(
                rows,
                [
                    {
                        "level": "N3",
                        "day": "001",
                        "video_exists": True,
                        "thumbnail_exists": True,
                        "drive_available": True,
                        "can_restore": False,
                        "status": "ready",
                        "video_path": str(day_root / "N3" / "N3_DAY_001.mp4"),
                    },
                    {
                        "level": "N3",
                        "day": "002",
                        "video_exists": False,
                        "thumbnail_exists": False,
                        "drive_available": False,
                        "can_restore": False,
                        "status": "missing",
                        "video_path": str(day_root / "N3" / "N3_DAY_002.mp4"),
                    },
                    {
                        "level": "N3",
                        "day": "003",
                        "video_exists": False,
                        "thumbnail_exists": False,
                        "drive_available": True,
                        "can_restore": True,
                        "status": "restorable",
                        "video_path": str(day_root / "N3" / "N3_DAY_003.mp4"),
                    },
                ],
            )

    def test_ensure_compilation_sources_restores_only_restorable_missing_days(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            day_root = root / "output" / "day_videos"
            thumb_root = root / "output" / "thumbnails"
            log_data = {
                "N2_DAY_001": {"drive_backed_up": True, "drive_video_file_id": "drive-1"},
                "N2_DAY_002": {"drive_backed_up": True, "drive_video_file_id": "drive-2"},
            }
            restored = []

            (day_root / "N2").mkdir(parents=True)
            (day_root / "N2" / "N2_DAY_001.mp4").write_bytes(b"video")

            def restore_day(level, day, overwrite):
                restored.append((level, day, overwrite))
                return {"upload_key": f"{level}_DAY_{int(day):03d}", "skipped": False}

            result = ensure_compilation_sources(
                ["N2"],
                1,
                2,
                restore_day=restore_day,
                day_video_root=day_root,
                thumbnail_root=thumb_root,
                log_data=log_data,
            )

            self.assertEqual(restored, [("N2", "002", False)])
            self.assertEqual(result["restored_count"], 1)
            self.assertEqual(result["missing_count"], 0)
            self.assertTrue(result["ready"])

    def test_ensure_compilation_sources_raises_when_missing_day_has_no_drive_backup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaises(ValueError) as error:
                ensure_compilation_sources(
                    ["N1"],
                    1,
                    1,
                    restore_day=lambda level, day, overwrite: None,
                    day_video_root=root / "day_videos",
                    thumbnail_root=root / "thumbnails",
                    log_data={},
                )

            self.assertIn("N1 DAY 001", str(error.exception))

    def test_build_storage_summary_counts_files_and_sizes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "output" / "day_videos" / "N1" / "N1_DAY_001.mp4"
            second = root / "assets" / "audio" / "a.mp3"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            first.write_bytes(b"1234")
            second.write_bytes(b"123456")

            rows = build_storage_summary(
                [
                    ("DAY 영상", root / "output" / "day_videos"),
                    ("오디오", root / "assets" / "audio"),
                    ("없는 폴더", root / "missing"),
                ]
            )

            self.assertEqual(
                rows,
                [
                    {"label": "DAY 영상", "path": str(root / "output" / "day_videos"), "exists": True, "file_count": 1, "bytes": 4},
                    {"label": "오디오", "path": str(root / "assets" / "audio"), "exists": True, "file_count": 1, "bytes": 6},
                    {"label": "없는 폴더", "path": str(root / "missing"), "exists": False, "file_count": 0, "bytes": 0},
                ],
            )

    def test_read_log_tail_returns_last_lines_without_loading_missing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            log_path = root / "app.log"
            log_path.write_text("one\ntwo\nthree\n", encoding="utf-8")

            self.assertEqual(read_log_tail(log_path, line_count=2), "two\nthree")
            self.assertEqual(read_log_tail(root / "missing.log", line_count=2), "")

    def test_cleanup_generated_assets_for_compilation_range_deletes_manifest_images(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image_one = root / "assets" / "images" / "img-1.png"
            image_two = root / "assets" / "images" / "img-2.png"
            image_one.parent.mkdir(parents=True)
            image_one.write_bytes(b"one")
            image_two.write_bytes(b"two")

            log_data = {
                "N3_DAY_001": {
                    "asset_manifest": [
                        {"image": str(image_one)},
                        {"image": str(image_two)},
                    ]
                },
                "N3_DAY_002": {
                    "asset_manifest": [
                        {"image": str(image_two)},
                    ]
                },
            }
            updated = []

            def get_entry(key):
                return log_data.get(key)

            def update_entry(key, **updates):
                updated.append((key, updates))

            result = cleanup_generated_assets_for_compilation_range(
                "N3",
                1,
                2,
                get_entry=get_entry,
                update_entry=update_entry,
            )

            self.assertFalse(image_one.exists())
            self.assertFalse(image_two.exists())
            self.assertEqual(len(result["deleted_files"]), 2)
            self.assertEqual(result["deleted_day_count"], 2)
            self.assertEqual(
                updated,
                [
                    ("N3_DAY_001", {"compilation_asset_cleanup_done": True, "compilation_cleaned_asset_count": 2}),
                    ("N3_DAY_002", {"compilation_asset_cleanup_done": True, "compilation_cleaned_asset_count": 0}),
                ],
            )

    def test_cleanup_generated_assets_for_compilation_range_skips_days_without_manifest(self):
        updated = []

        result = cleanup_generated_assets_for_compilation_range(
            "N1",
            1,
            2,
            get_entry=lambda key: None,
            update_entry=lambda key, **updates: updated.append((key, updates)),
        )

        self.assertEqual(result["deleted_files"], [])
        self.assertEqual(result["deleted_day_count"], 0)
        self.assertEqual(updated, [])

    def test_classify_generation_day_distinguishes_history_and_new_generation(self):
        historical = classify_generation_day("N1", 12, next_day=13)
        self.assertEqual(historical["execution_mode"], "regenerate")
        self.assertTrue(historical["is_historical"])
        self.assertEqual(historical["day_text"], "012")

        current_or_future = classify_generation_day("N1", 13, next_day=13)
        self.assertEqual(current_or_future["execution_mode"], "generate")
        self.assertFalse(current_or_future["is_historical"])

        with self.assertRaises(ValueError):
            classify_generation_day("N1", 0, next_day=13)

    def test_build_regeneration_preview_reports_existing_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            day_root = root / "output" / "day_videos"
            thumbnail_root = root / "output" / "thumbnails"
            (day_root / "N2").mkdir(parents=True)
            thumbnail_root.mkdir(parents=True)
            (day_root / "N2" / "N2_DAY_007.mp4").write_bytes(b"video")

            preview = build_regeneration_preview(
                "N2",
                7,
                day_video_root=day_root,
                thumbnail_root=thumbnail_root,
            )

            self.assertEqual(preview["level"], "N2")
            self.assertEqual(preview["day"], "007")
            self.assertTrue(preview["video_exists"])
            self.assertFalse(preview["thumbnail_exists"])

if __name__ == "__main__":
    unittest.main()
