"""Core domain models and player progression logic for LevelUp."""

from typing import Dict, Optional, Any


class Player:
    """Represents the player state, statistics, and XP progression."""

    def __init__(
        self,
        name: str = "Sung Jin-Woo",
        level: int = 1,
        xp: int = 0,
        xp_to_next_level: int = 100,
        stats: Optional[Dict[str, int]] = None,
    ) -> None:
        """Initialize a new Player instance.

        Args:
            name: Player display name.
            level: Initial player level.
            xp: Current experience points.
            xp_to_next_level: XP required for the next level.
            stats: Custom stat dictionary or default values.
        """
        self.name: str = name
        self.level: int = level
        self.xp: int = xp
        self.xp_to_next_level: int = xp_to_next_level

        if stats is not None:
            self.stats: Dict[str, int] = stats.copy()
        else:
            self.stats = {
                "STRENGTH": 10,
                "AGILITY": 10,
                "INTELLIGENCE": 10,
                "AVAILABLE_POINTS": 0,
            }

    def gain_xp(self, amount: int) -> bool:
        """Add experience points and process multi-level rollovers.

        Args:
            amount: Non-negative XP value to add.

        Returns:
            True if one or more level-ups occurred, False otherwise.
        """
        if amount <= 0:
            return False

        self.xp += amount
        leveled_up: bool = False

        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.xp_to_next_level = int(round(self.xp_to_next_level * 1.5))
            self.stats["AVAILABLE_POINTS"] += 3
            leveled_up = True

        return leveled_up


class Quest:
    """Represents a quest task with associated XP rewards and completion state."""

    def __init__(
        self,
        quest_id: str,
        title: str,
        xp_reward: int,
        category: str,
        is_completed: bool = False,
    ) -> None:
        """Initialize a new Quest instance.

        Args:
            quest_id: Unique identifier for the quest.
            title: Descriptive quest title.
            xp_reward: Experience points granted upon completion.
            category: Quest classification (e.g. Physical, Intellect, Coding).
            is_completed: Current completion state.
        """
        self.quest_id: str = quest_id
        self.title: str = title
        self.xp_reward: int = xp_reward
        self.category: str = category
        self.is_completed: bool = is_completed

    def complete(self, player: Player, voice: Optional[Any] = None) -> bool:
        """Mark the quest as completed and award XP to the player.

        Args:
            player: Target Player object.
            voice: Optional SystemVoice instance for spoken audio notifications.

        Returns:
            True if a level-up occurred, False otherwise.
        """
        if self.is_completed:
            return False

        self.is_completed = True
        leveled_up: bool = player.gain_xp(self.xp_reward)

        if voice is not None:
            voice.speak_async(
                f"Quest completed: {self.title}. Granted {self.xp_reward} experience points."
            )
            if leveled_up:
                voice.speak_async(
                    f"Warning: Player level increased to Level {player.level}. 3 stat points allocated."
                )

        return leveled_up
