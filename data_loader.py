"""Data loader utility for safely reading and saving quest data with fallback handling."""

import csv
import json
import logging
from pathlib import Path
from typing import List, Union

from system_core import Quest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QuestLoader")


class QuestLoader:
    """Handles loading and saving quest definitions from JSON or CSV files with robust fallbacks."""

    @staticmethod
    def get_default_quests() -> List[Quest]:
        """Provide default fallback quests in case file loading fails.

        Returns:
            List of default Quest instances.
        """
        return [
            Quest(
                quest_id="Q1",
                title="Complete 50 Pushups",
                xp_reward=50,
                category="Physical",
            ),
            Quest(
                quest_id="Q2",
                title="Study Python Data Structures for 1 Hour",
                xp_reward=75,
                category="Intellect",
            ),
            Quest(
                quest_id="Q3",
                title="Build Module 3 of AR Project",
                xp_reward=100,
                category="Coding",
            ),
        ]

    @classmethod
    def load_quests(cls, filepath: Union[str, Path] = "data/quests.json") -> List[Quest]:
        """Load quests from JSON or CSV file.

        Args:
            filepath: Target file path to read quests from.

        Returns:
            List of loaded Quest objects, or default fallback quests on error.
        """
        path = Path(filepath)

        if not path.exists():
            logger.warning(
                "Quest file '%s' not found. Using default fallback quests.", path
            )
            return cls.get_default_quests()

        try:
            if path.suffix.lower() == ".csv":
                return cls._load_csv(path)
            else:
                return cls._load_json(path)
        except (json.JSONDecodeError, KeyError, ValueError, csv.Error) as err:
            logger.error(
                "Failed to parse quest file '%s' due to error: %s. Using default fallback quests.",
                path,
                err,
            )
            return cls.get_default_quests()
        except Exception as err:
            logger.error(
                "Unexpected error reading quest file '%s': %s. Using fallback quests.",
                path,
                err,
            )
            return cls.get_default_quests()

    @classmethod
    def save_quests(
        cls, quests: List[Quest], filepath: Union[str, Path] = "data/quests.json"
    ) -> bool:
        """Save current list of quests back to JSON data file.

        Args:
            quests: List of Quest objects to save.
            filepath: Target JSON file path.

        Returns:
            True if saved successfully, False otherwise.
        """
        path = Path(filepath)

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            data = [
                {
                    "id": q.quest_id,
                    "title": q.title,
                    "xp": q.xp_reward,
                    "category": q.category,
                    "is_completed": q.is_completed,
                }
                for q in quests
            ]
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info("Successfully saved %d quests to '%s'.", len(quests), path)
            return True
        except Exception as err:
            logger.error("Failed to save quests to '%s': %s", path, err)
            return False

    @staticmethod
    def _load_json(path: Path) -> List[Quest]:
        """Parse quests from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("JSON root element must be a list of quest objects.")

        quests: List[Quest] = []
        for index, item in enumerate(data):
            q_id = str(item.get("id", f"Q{index + 1}"))
            title = str(item.get("title", f"Quest #{index + 1}"))
            xp = int(item.get("xp", 50))
            category = str(item.get("category", "General"))
            is_completed = bool(item.get("is_completed", False))

            quests.append(
                Quest(
                    quest_id=q_id,
                    title=title,
                    xp_reward=xp,
                    category=category,
                    is_completed=is_completed,
                )
            )

        return quests if quests else QuestLoader.get_default_quests()

    @staticmethod
    def _load_csv(path: Path) -> List[Quest]:
        """Parse quests from a CSV file."""
        quests: List[Quest] = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for index, row in enumerate(reader):
                q_id = str(row.get("id", f"Q{index + 1}"))
                title = str(row.get("title", f"Quest #{index + 1}"))
                xp = int(row.get("xp", 50))
                category = str(row.get("category", "General"))
                is_completed = str(row.get("is_completed", "false")).lower() in (
                    "true",
                    "1",
                    "yes",
                )

                quests.append(
                    Quest(
                        quest_id=q_id,
                        title=title,
                        xp_reward=xp,
                        category=category,
                        is_completed=is_completed,
                    )
                )

        return quests if quests else QuestLoader.get_default_quests()
