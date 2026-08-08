"""Automated unit test suite for LevelUp persistence, registration, and progression engine."""

import json
import unittest
from pathlib import Path

from data_loader import QuestLoader
from system_core import Player, Quest
from system_hud import SystemHUD
from system_listener import VoiceListener


class TestPlayerProgression(unittest.TestCase):
    """Test player level-up and XP rollover mechanics."""

    def setUp(self) -> None:
        self.player = Player(name="TestPlayer", level=1, xp=0, xp_to_next_level=100)

    def test_single_level_up(self) -> None:
        leveled_up = self.player.gain_xp(100)
        self.assertTrue(leveled_up)
        self.assertEqual(self.player.level, 2)
        self.assertEqual(self.player.xp, 0)

    def test_multi_level_rollover(self) -> None:
        leveled_up = self.player.gain_xp(500)
        self.assertTrue(leveled_up)
        self.assertEqual(self.player.level, 4)
        self.assertEqual(self.player.xp, 25)


class TestQuestPersistence(unittest.TestCase):
    """Test saving and loading custom quests to JSON file."""

    def test_save_and_load_quests(self) -> None:
        test_file = Path("tmp_save_test.json")
        try:
            sample_quests = [
                Quest("Q1", "Test Pushups", 50, "Physical"),
                Quest("Q2", "Test Reading", 75, "Intellect", is_completed=True),
            ]
            saved = QuestLoader.save_quests(sample_quests, test_file)
            self.assertTrue(saved)

            loaded = QuestLoader.load_quests(test_file)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0].title, "Test Pushups")
            self.assertTrue(loaded[1].is_completed)
        finally:
            if test_file.exists():
                test_file.unlink()


class TestVoiceIntentParsing(unittest.TestCase):
    """Test voice listener intent recognition parsing."""

    def setUp(self) -> None:
        self.listener = VoiceListener()

    def tearDown(self) -> None:
        self.listener.stop()

    def test_intent_level_up(self) -> None:
        res = self.listener.parse_intent("System level up please")
        self.assertEqual(res, ("levelup", None))

    def test_intent_complete_index(self) -> None:
        res = self.listener.parse_intent("complete quest 1")
        self.assertEqual(res, ("complete_index", 0))


if __name__ == "__main__":
    unittest.main()
