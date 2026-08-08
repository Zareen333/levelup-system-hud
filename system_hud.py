"""Pygame HUD renderer supporting Desktop/Mobile views, Registration modal, Add Quest form, and touch hitboxes."""

import math
import time
from typing import Dict, List, Optional, Tuple, Union

import pygame

from system_core import Player, Quest

# Color Definitions
COLOR_BG = (26, 11, 46)          # Deep Violet #1A0B2E
COLOR_PANEL_FILL = (17, 6, 32)   # Translucent Glass Panel
COLOR_CYAN = (0, 229, 255)       # Neon Cyan #00E5FF
COLOR_BLUE = (0, 85, 255)        # Electric Blue #0055FF
COLOR_LIGHT_CYAN = (128, 245, 255)
COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_MUTED = (140, 155, 180)
COLOR_GOLD = (255, 215, 0)
COLOR_GREEN = (0, 255, 157)
COLOR_DARK_BORDER = (40, 25, 70)
COLOR_INPUT_BG = (12, 6, 24)


class SystemHUD:
    """Renders AR HUD layouts, registration screens, quest creation modals, and touch hitboxes."""

    def __init__(self, mode: str = "desktop") -> None:
        """Initialize HUD renderer with view mode.

        Args:
            mode: 'desktop' (1024x768) or 'mobile' (450x850).
        """
        self.mode: str = mode
        self.width: int = 1024 if mode == "desktop" else 450
        self.height: int = 768 if mode == "desktop" else 850

        if not pygame.font.get_init():
            pygame.font.init()

        # Scalable fonts
        self.font_title = self._create_font(size=24 if mode == "desktop" else 18, bold=True)
        self.font_header = self._create_font(size=18 if mode == "desktop" else 15, bold=True)
        self.font_body = self._create_font(size=15 if mode == "desktop" else 13, bold=False)
        self.font_bold = self._create_font(size=15 if mode == "desktop" else 13, bold=True)
        self.font_small = self._create_font(size=12 if mode == "desktop" else 11, bold=False)
        self.font_popup = self._create_font(size=36 if mode == "desktop" else 26, bold=True)

        # Animation states
        self.displayed_xp_ratio: float = 0.0
        self.level_up_start_time: float = 0.0
        self.level_up_duration: float = 3.0
        self.is_level_up_active: bool = False

        # Console Bar & Registration State
        self.command_text: str = ""
        self.reg_name_text: str = "Sung Jin-Woo"
        self.feedback_message: str = "System ready. Type or speak commands."
        self.feedback_is_error: bool = False
        self.input_focused: bool = False

        # Add Quest Form Modal States
        self.add_quest_active: bool = False
        self.add_quest_field_focus: int = 0  # 0: Title, 1: XP, 2: Category
        self.add_quest_title: str = ""
        self.add_quest_xp: str = "50"
        self.add_quest_category: str = "General"

        # Interactive Hitboxes
        self.hitboxes: Dict[str, Any] = {}

    def _create_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        """Helper to create scalable fonts with system fallback options."""
        preferred_fonts = ["Consolas", "Segoe UI", "Trebuchet MS", "Arial"]
        for font_name in preferred_fonts:
            try:
                font = pygame.font.SysFont(font_name, size, bold=bold)
                if font:
                    return font
            except Exception:
                continue
        return pygame.font.Font(None, size)

    def set_mode(self, mode: str) -> None:
        """Switch HUD resolution mode between 'desktop' and 'mobile'."""
        self.mode = mode
        self.width = 1024 if mode == "desktop" else 450
        self.height = 768 if mode == "desktop" else 850
        self.font_title = self._create_font(size=24 if mode == "desktop" else 18, bold=True)
        self.font_header = self._create_font(size=18 if mode == "desktop" else 15, bold=True)
        self.font_body = self._create_font(size=15 if mode == "desktop" else 13, bold=False)
        self.font_bold = self._create_font(size=15 if mode == "desktop" else 13, bold=True)
        self.font_small = self._create_font(size=12 if mode == "desktop" else 11, bold=False)
        self.font_popup = self._create_font(size=36 if mode == "desktop" else 26, bold=True)

    def trigger_level_up(self) -> None:
        """Activate the Level Up overlay popup for 3 seconds."""
        self.level_up_start_time = time.time()
        self.is_level_up_active = True

    def set_feedback(self, msg: str, is_error: bool = False) -> None:
        """Set user status line in command bar."""
        self.feedback_message = msg
        self.feedback_is_error = is_error

    def _draw_glass_panel(
        self,
        surface: pygame.Surface,
        rect: Tuple[int, int, int, int],
        border_color: Tuple[int, int, int] = COLOR_CYAN,
        fill_alpha: int = 210,
        glow: bool = True,
    ) -> None:
        """Draw glassmorphic translucent panel."""
        x, y, w, h = rect
        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        panel_surf.fill((*COLOR_PANEL_FILL, fill_alpha))
        surface.blit(panel_surf, (x, y))

        if glow:
            glow_surf = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surf, (*border_color, 40), (0, 0, w + 6, h + 6), width=3, border_radius=6
            )
            surface.blit(glow_surf, (x - 3, y - 3))

        pygame.draw.rect(surface, border_color, (x, y, w, h), width=2, border_radius=4)

        tick_len = 10
        pygame.draw.line(surface, COLOR_WHITE, (x, y), (x + tick_len, y), 2)
        pygame.draw.line(surface, COLOR_WHITE, (x, y), (x, y + tick_len), 2)
        pygame.draw.line(surface, COLOR_WHITE, (x + w, y), (x + w - tick_len, y), 2)
        pygame.draw.line(surface, COLOR_WHITE, (x + w, y), (x + w, y + tick_len), 2)

    def render(
        self,
        surface: pygame.Surface,
        player: Player,
        quests: List[Quest],
        mic_status: str = "OFF",
        app_state: str = "HUD",
        force_level_up_active: bool = False,
    ) -> Dict[str, Any]:
        """Render HUD frame and return hitboxes.

        Args:
            surface: Main display surface.
            player: Player state.
            quests: List of Quest objects.
            mic_status: Spoken mic status line.
            app_state: 'REGISTRATION', 'HUD', or 'ADD_QUEST_MODAL'.
            force_level_up_active: Override level up banner.

        Returns:
            Dictionary of interactive hitboxes.
        """
        surface.fill(COLOR_BG)
        self.hitboxes = {
            "mode_button": pygame.Rect(0, 0, 0, 0),
            "add_quest_button": pygame.Rect(0, 0, 0, 0),
            "quest_cards": [],
            "input_bar": pygame.Rect(0, 0, 0, 0),
            "send_button": pygame.Rect(0, 0, 0, 0),
            "reg_input": pygame.Rect(0, 0, 0, 0),
            "reg_confirm": pygame.Rect(0, 0, 0, 0),
            "modal_title_input": pygame.Rect(0, 0, 0, 0),
            "modal_xp_input": pygame.Rect(0, 0, 0, 0),
            "modal_cat_input": pygame.Rect(0, 0, 0, 0),
            "modal_save": pygame.Rect(0, 0, 0, 0),
            "modal_cancel": pygame.Rect(0, 0, 0, 0),
        }

        # Grid lines
        grid_step = 40 if self.mode == "desktop" else 30
        for gx in range(0, self.width, grid_step):
            pygame.draw.line(surface, (35, 18, 62), (gx, 0), (gx, self.height), 1)
        for gy in range(0, self.height, grid_step):
            pygame.draw.line(surface, (35, 18, 62), (0, gy), (self.width, gy), 1)

        # Base Layout
        if self.mode == "desktop":
            self._render_desktop_layout(surface, player, quests, mic_status)
        else:
            self._render_mobile_layout(surface, player, quests, mic_status)

        # Modal Overlays
        if app_state == "REGISTRATION":
            self._render_registration_modal(surface)
        elif app_state == "ADD_QUEST_MODAL":
            self._render_add_quest_modal(surface)

        # Level Up Banner
        now = time.time()
        time_elapsed = now - self.level_up_start_time
        popup_active = force_level_up_active or (
            self.is_level_up_active and time_elapsed < self.level_up_duration
        )

        if popup_active and app_state == "HUD":
            self._render_level_up_popup(surface, player, time_elapsed)
        else:
            self.is_level_up_active = False

        return self.hitboxes

    def _render_desktop_layout(
        self, surface: pygame.Surface, player: Player, quests: List[Quest], mic_status: str
    ) -> None:
        """Render Widescreen Desktop 1024x768 HUD."""
        self._draw_glass_panel(surface, (30, 20, 964, 165), border_color=COLOR_CYAN)

        # Header Title
        title_txt = self.font_title.render("SYSTEM — PLAYER STATUS", True, COLOR_CYAN)
        surface.blit(title_txt, (50, 32))

        # Mode Button Hitbox
        mode_btn_rect = pygame.Rect(800, 32, 170, 30)
        self.hitboxes["mode_button"] = mode_btn_rect
        pygame.draw.rect(surface, (40, 20, 75), mode_btn_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_GOLD, mode_btn_rect, width=1, border_radius=4)
        surface.blit(self.font_bold.render("📱 MOBILE VIEW", True, COLOR_GOLD), (815, 38))

        # Add Quest Button Hitbox
        add_btn_rect = pygame.Rect(630, 32, 155, 30)
        self.hitboxes["add_quest_button"] = add_btn_rect
        pygame.draw.rect(surface, (10, 60, 40), add_btn_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_GREEN, add_btn_rect, width=1, border_radius=4)
        surface.blit(self.font_bold.render("+ ADD QUEST", True, COLOR_GREEN), (650, 38))

        # Level & Mic status
        surface.blit(self.font_header.render(f"LVL {player.level}", True, COLOR_GOLD), (530, 35))
        mic_clr = COLOR_GREEN if "LISTENING" in mic_status else (COLOR_CYAN if "HEARD" in mic_status else COLOR_TEXT_MUTED)
        surface.blit(self.font_small.render(f"VOICE: {mic_status}", True, mic_clr), (370, 38))

        # Name & Stats
        surface.blit(self.font_body.render(f"PLAYER: {player.name.upper()}", True, COLOR_WHITE), (50, 68))
        str_v, agi_v, int_v, pts_v = (
            player.stats.get("STRENGTH", 10),
            player.stats.get("AGILITY", 10),
            player.stats.get("INTELLIGENCE", 10),
            player.stats.get("AVAILABLE_POINTS", 0),
        )
        stats_str = f"STR: {str_v}  |  AGI: {agi_v}  |  INT: {int_v}"
        surface.blit(self.font_bold.render(stats_str, True, COLOR_LIGHT_CYAN), (50, 92))

        if pts_v > 0:
            surface.blit(self.font_bold.render(f"[ +{pts_v} STAT POINTS ]", True, COLOR_GOLD), (450, 92))

        # XP Bar
        target_ratio = min(1.0, max(0.0, player.xp / float(player.xp_to_next_level)))
        self.displayed_xp_ratio += (target_ratio - self.displayed_xp_ratio) * 0.12

        bar_x, bar_y, bar_w, bar_h = 50, 140, 924, 20
        xp_str = f"XP: {player.xp} / {player.xp_to_next_level} ({int(target_ratio * 100)}%)"
        surface.blit(self.font_small.render(xp_str, True, COLOR_WHITE), (bar_x, bar_y - 16))
        pygame.draw.rect(surface, (15, 8, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        pygame.draw.rect(surface, COLOR_BLUE, (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=4)

        fill_w = max(0, int(bar_w * self.displayed_xp_ratio))
        if fill_w > 0:
            pygame.draw.rect(surface, COLOR_CYAN, (bar_x, bar_y, fill_w, bar_h), border_radius=4)

        # Quest Log Panel
        self._draw_glass_panel(surface, (30, 200, 964, 460), border_color=COLOR_BLUE)
        surface.blit(self.font_title.render("QUEST LOG — DAILY ASSIGNMENTS", True, COLOR_CYAN), (50, 215))

        quest_cards_hitboxes: List[Tuple[pygame.Rect, int]] = []
        card_y = 255
        for idx, quest in enumerate(quests):
            if idx >= 6:
                break
            card_rect = pygame.Rect(50, card_y, 924, 60)
            quest_cards_hitboxes.append((card_rect, idx))

            card_bg = (10, 5, 25) if not quest.is_completed else (8, 12, 18)
            pygame.draw.rect(surface, card_bg, card_rect, border_radius=4)
            b_clr = COLOR_CYAN if not quest.is_completed else COLOR_DARK_BORDER
            pygame.draw.rect(surface, b_clr, card_rect, width=1, border_radius=4)

            surface.blit(self.font_bold.render(f"[{idx + 1}]", True, COLOR_GOLD), (65, card_y + 18))
            t_clr = COLOR_WHITE if not quest.is_completed else COLOR_TEXT_MUTED
            surface.blit(self.font_body.render(quest.title, True, t_clr), (115, card_y + 18))

            if quest.is_completed:
                surface.blit(self.font_bold.render("✓ COMPLETED", True, COLOR_GREEN), (790, card_y + 18))
            else:
                surface.blit(self.font_bold.render(f"+{quest.xp_reward} XP", True, COLOR_GOLD), (810, card_y + 18))

            card_y += 68

        self.hitboxes["quest_cards"] = quest_cards_hitboxes
        self._render_command_console(surface, rect=(30, 675, 964, 75))

    def _render_mobile_layout(
        self, surface: pygame.Surface, player: Player, quests: List[Quest], mic_status: str
    ) -> None:
        """Render Portrait Mobile 450x850 HUD."""
        self._draw_glass_panel(surface, (15, 15, 420, 185), border_color=COLOR_CYAN)

        surface.blit(self.font_title.render("SYSTEM HUD", True, COLOR_CYAN), (30, 23))

        # Header Buttons
        mode_btn_rect = pygame.Rect(300, 20, 120, 28)
        self.hitboxes["mode_button"] = mode_btn_rect
        pygame.draw.rect(surface, (40, 20, 75), mode_btn_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_GOLD, mode_btn_rect, width=1, border_radius=4)
        surface.blit(self.font_bold.render("💻 DESKTOP", True, COLOR_GOLD), (310, 25))

        add_btn_rect = pygame.Rect(175, 20, 115, 28)
        self.hitboxes["add_quest_button"] = add_btn_rect
        pygame.draw.rect(surface, (10, 60, 40), add_btn_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_GREEN, add_btn_rect, width=1, border_radius=4)
        surface.blit(self.font_bold.render("+ QUEST", True, COLOR_GREEN), (190, 25))

        surface.blit(self.font_header.render(f"LVL {player.level}", True, COLOR_GOLD), (30, 48))
        mic_clr = COLOR_GREEN if "LISTENING" in mic_status else (COLOR_CYAN if "HEARD" in mic_status else COLOR_TEXT_MUTED)
        surface.blit(self.font_small.render(f"MIC: {mic_status}", True, mic_clr), (120, 50))

        surface.blit(self.font_body.render(f"PLAYER: {player.name.upper()}", True, COLOR_WHITE), (30, 72))
        str_v, agi_v, int_v, pts_v = (
            player.stats.get("STRENGTH", 10),
            player.stats.get("AGILITY", 10),
            player.stats.get("INTELLIGENCE", 10),
            player.stats.get("AVAILABLE_POINTS", 0),
        )
        surface.blit(
            self.font_small.render(f"STR: {str_v}  AGI: {agi_v}  INT: {int_v}", True, COLOR_LIGHT_CYAN),
            (30, 95),
        )

        if pts_v > 0:
            surface.blit(self.font_bold.render(f"[ +{pts_v} PTS AVAILABLE ]", True, COLOR_GOLD), (230, 95))

        # XP Bar
        target_ratio = min(1.0, max(0.0, player.xp / float(player.xp_to_next_level)))
        self.displayed_xp_ratio += (target_ratio - self.displayed_xp_ratio) * 0.12

        bar_x, bar_y, bar_w, bar_h = 30, 148, 390, 18
        xp_str = f"XP: {player.xp}/{player.xp_to_next_level} ({int(target_ratio * 100)}%)"
        surface.blit(self.font_small.render(xp_str, True, COLOR_WHITE), (bar_x, bar_y - 15))
        pygame.draw.rect(surface, (15, 8, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        pygame.draw.rect(surface, COLOR_BLUE, (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=4)

        fill_w = max(0, int(bar_w * self.displayed_xp_ratio))
        if fill_w > 0:
            pygame.draw.rect(surface, COLOR_CYAN, (bar_x, bar_y, fill_w, bar_h), border_radius=4)

        # Quests Panel
        self._draw_glass_panel(surface, (15, 210, 420, 525), border_color=COLOR_BLUE)
        surface.blit(self.font_title.render("DAILY QUESTS", True, COLOR_CYAN), (30, 222))

        quest_cards_hitboxes: List[Tuple[pygame.Rect, int]] = []
        card_y = 255
        for idx, quest in enumerate(quests):
            if idx >= 7:
                break
            card_rect = pygame.Rect(30, card_y, 390, 60)
            quest_cards_hitboxes.append((card_rect, idx))

            card_bg = (10, 5, 25) if not quest.is_completed else (8, 12, 18)
            pygame.draw.rect(surface, card_bg, card_rect, border_radius=4)
            b_clr = COLOR_CYAN if not quest.is_completed else COLOR_DARK_BORDER
            pygame.draw.rect(surface, b_clr, card_rect, width=1, border_radius=4)

            surface.blit(self.font_bold.render(f"[{idx + 1}]", True, COLOR_GOLD), (40, card_y + 12))
            t_clr = COLOR_WHITE if not quest.is_completed else COLOR_TEXT_MUTED
            surface.blit(self.font_body.render(quest.title[:26], True, t_clr), (75, card_y + 12))

            if quest.is_completed:
                surface.blit(self.font_bold.render("✓ COMPLETED", True, COLOR_GREEN), (75, card_y + 34))
            else:
                surface.blit(
                    self.font_small.render(f"+{quest.xp_reward} XP  [{quest.category}]", True, COLOR_GOLD),
                    (75, card_y + 34),
                )

            card_y += 66

        self.hitboxes["quest_cards"] = quest_cards_hitboxes
        self._render_command_console(surface, rect=(15, 745, 420, 90))

    def _render_command_console(
        self, surface: pygame.Surface, rect: Tuple[int, int, int, int]
    ) -> None:
        """Render command input bar."""
        x, y, w, h = rect
        self._draw_glass_panel(surface, rect, border_color=COLOR_CYAN, glow=False)

        fb_clr = COLOR_GOLD if not self.feedback_is_error else (255, 80, 80)
        surface.blit(self.font_small.render(f"STATUS: {self.feedback_message}", True, fb_clr), (x + 15, y + 8))

        input_rect = pygame.Rect(x + 15, y + 30, w - 100, 34 if self.mode == "desktop" else 42)
        self.hitboxes["input_bar"] = input_rect

        border_c = COLOR_CYAN if self.input_focused else COLOR_DARK_BORDER
        pygame.draw.rect(surface, COLOR_INPUT_BG, input_rect, border_radius=4)
        pygame.draw.rect(surface, border_c, input_rect, width=1, border_radius=4)

        cursor = "│" if (int(time.time() * 2) % 2 == 0 and self.input_focused) else ""
        surface.blit(self.font_body.render(f"> {self.command_text}{cursor}", True, COLOR_WHITE), (x + 25, y + 36))

        send_rect = pygame.Rect(x + w - 75, y + 30, 60, 34 if self.mode == "desktop" else 42)
        self.hitboxes["send_button"] = send_rect
        pygame.draw.rect(surface, COLOR_BLUE, send_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_CYAN, send_rect, width=1, border_radius=4)
        surface.blit(self.font_bold.render("SEND", True, COLOR_WHITE), (x + w - 63, y + 38))

    def _render_registration_modal(self, surface: pygame.Surface) -> None:
        """Render Startup Player Registration Dialog."""
        w, h = (520, 260) if self.mode == "desktop" else (380, 260)
        x = (self.width - w) // 2
        y = (self.height - h) // 2

        dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 200))
        surface.blit(dim_surf, (0, 0))

        pop_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pop_surf.fill((20, 10, 40, 245))
        surface.blit(pop_surf, (x, y))

        pygame.draw.rect(surface, COLOR_CYAN, (x, y, w, h), width=3, border_radius=8)

        t_txt = self.font_title.render("HUNTER REGISTRATION", True, COLOR_GOLD)
        surface.blit(t_txt, (x + (w - t_txt.get_width()) // 2, y + 25))

        sub_txt = self.font_body.render("Enter your name to sync with System HUD:", True, COLOR_WHITE)
        surface.blit(sub_txt, (x + 40, y + 75))

        # Input Box
        reg_input = pygame.Rect(x + 40, y + 115, w - 80, 40)
        self.hitboxes["reg_input"] = reg_input
        pygame.draw.rect(surface, COLOR_INPUT_BG, reg_input, border_radius=4)
        pygame.draw.rect(surface, COLOR_CYAN, reg_input, width=2, border_radius=4)

        cursor = "│" if (int(time.time() * 2) % 2 == 0) else ""
        surface.blit(self.font_bold.render(f"{self.reg_name_text}{cursor}", True, COLOR_CYAN), (x + 55, y + 125))

        # Confirm Button
        confirm_btn = pygame.Rect(x + (w - 160) // 2, y + 180, 160, 42)
        self.hitboxes["reg_confirm"] = confirm_btn
        pygame.draw.rect(surface, COLOR_BLUE, confirm_btn, border_radius=6)
        pygame.draw.rect(surface, COLOR_CYAN, confirm_btn, width=2, border_radius=6)
        surface.blit(self.font_bold.render("REGISTER ▶", True, COLOR_WHITE), (x + (w - 160) // 2 + 25, y + 192))

    def _render_add_quest_modal(self, surface: pygame.Surface) -> None:
        """Render Add Quest Form Modal."""
        w, h = (600, 360) if self.mode == "desktop" else (400, 380)
        x = (self.width - w) // 2
        y = (self.height - h) // 2

        dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 190))
        surface.blit(dim_surf, (0, 0))

        pop_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pop_surf.fill((18, 8, 36, 245))
        surface.blit(pop_surf, (x, y))
        pygame.draw.rect(surface, COLOR_GREEN, (x, y, w, h), width=3, border_radius=8)

        t_txt = self.font_title.render("NEW ASSIGNMENT — ADD QUEST", True, COLOR_GREEN)
        surface.blit(t_txt, (x + (w - t_txt.get_width()) // 2, y + 20))

        # Field 1: Title
        surface.blit(self.font_bold.render("QUEST TITLE:", True, COLOR_WHITE), (x + 35, y + 65))
        title_rect = pygame.Rect(x + 35, y + 90, w - 70, 36)
        self.hitboxes["modal_title_input"] = title_rect
        f1_b = COLOR_GREEN if self.add_quest_field_focus == 0 else COLOR_DARK_BORDER
        pygame.draw.rect(surface, COLOR_INPUT_BG, title_rect, border_radius=4)
        pygame.draw.rect(surface, f1_b, title_rect, width=1, border_radius=4)
        c1 = "│" if (self.add_quest_field_focus == 0 and int(time.time() * 2) % 2 == 0) else ""
        surface.blit(self.font_body.render(f"{self.add_quest_title}{c1}", True, COLOR_WHITE), (x + 45, y + 98))

        # Field 2: XP
        surface.blit(self.font_bold.render("XP REWARD:", True, COLOR_WHITE), (x + 35, y + 140))
        xp_rect = pygame.Rect(x + 35, y + 165, (w - 90) // 2, 36)
        self.hitboxes["modal_xp_input"] = xp_rect
        f2_b = COLOR_GREEN if self.add_quest_field_focus == 1 else COLOR_DARK_BORDER
        pygame.draw.rect(surface, COLOR_INPUT_BG, xp_rect, border_radius=4)
        pygame.draw.rect(surface, f2_b, xp_rect, width=1, border_radius=4)
        c2 = "│" if (self.add_quest_field_focus == 1 and int(time.time() * 2) % 2 == 0) else ""
        surface.blit(self.font_body.render(f"{self.add_quest_xp}{c2}", True, COLOR_GOLD), (x + 45, y + 173))

        # Field 3: Category
        surface.blit(self.font_bold.render("CATEGORY:", True, COLOR_WHITE), (x + w // 2 + 10, y + 140))
        cat_rect = pygame.Rect(x + w // 2 + 10, y + 165, (w - 90) // 2, 36)
        self.hitboxes["modal_cat_input"] = cat_rect
        f3_b = COLOR_GREEN if self.add_quest_field_focus == 2 else COLOR_DARK_BORDER
        pygame.draw.rect(surface, COLOR_INPUT_BG, cat_rect, border_radius=4)
        pygame.draw.rect(surface, f3_b, cat_rect, width=1, border_radius=4)
        c3 = "│" if (self.add_quest_field_focus == 2 and int(time.time() * 2) % 2 == 0) else ""
        surface.blit(self.font_body.render(f"{self.add_quest_category}{c3}", True, COLOR_LIGHT_CYAN), (x + w // 2 + 20, y + 173))

        # Save / Cancel Buttons
        save_btn = pygame.Rect(x + 50, y + h - 65, 200 if self.mode == "desktop" else 130, 42)
        self.hitboxes["modal_save"] = save_btn
        pygame.draw.rect(surface, (10, 80, 40), save_btn, border_radius=6)
        pygame.draw.rect(surface, COLOR_GREEN, save_btn, width=2, border_radius=6)
        surface.blit(self.font_bold.render("SAVE QUEST ✓", True, COLOR_WHITE), (x + 70, y + h - 53))

        cancel_btn = pygame.Rect(x + w - (250 if self.mode == "desktop" else 180), y + h - 65, 200 if self.mode == "desktop" else 130, 42)
        self.hitboxes["modal_cancel"] = cancel_btn
        pygame.draw.rect(surface, (70, 20, 30), cancel_btn, border_radius=6)
        pygame.draw.rect(surface, (255, 80, 80), cancel_btn, width=2, border_radius=6)
        surface.blit(self.font_bold.render("CANCEL ✕", True, COLOR_WHITE), (x + w - (230 if self.mode == "desktop" else 160), y + h - 53))

    def _render_level_up_popup(
        self, surface: pygame.Surface, player: Player, elapsed_time: float
    ) -> None:
        """Render Level Up overlay banner."""
        w = 550 if self.mode == "desktop" else 380
        h = 220 if self.mode == "desktop" else 200
        x = (self.width - w) // 2
        y = (self.height - h) // 2

        dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 160))
        surface.blit(dim_surf, (0, 0))

        pulse = math.sin(elapsed_time * 8.0) * 0.5 + 0.5
        glow_color = (
            int(COLOR_GOLD[0] * (0.7 + 0.3 * pulse)),
            int(COLOR_GOLD[1] * (0.7 + 0.3 * pulse)),
            int(COLOR_CYAN[2] * (0.7 + 0.3 * pulse)),
        )

        pop_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pop_surf.fill((20, 10, 40, 240))
        surface.blit(pop_surf, (x, y))

        pygame.draw.rect(surface, glow_color, (x, y, w, h), width=4, border_radius=8)

        title_txt = self.font_popup.render("LEVEL UP!", True, COLOR_GOLD)
        surface.blit(title_txt, (x + (w - title_txt.get_width()) // 2, y + 25))

        lvl_txt = self.font_header.render(f"PLAYER LEVEL INCREASED TO {player.level}", True, COLOR_WHITE)
        surface.blit(lvl_txt, (x + (w - lvl_txt.get_width()) // 2, y + 85))

        sub_txt = self.font_bold.render("+3 STAT POINTS UNLOCKED", True, COLOR_CYAN)
        surface.blit(sub_txt, (x + (w - sub_txt.get_width()) // 2, y + 120))
