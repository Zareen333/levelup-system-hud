"""Main orchestrator for LevelUp HUD supporting Player Registration, Add Quest Modals, Voice & Text commands, and JSON auto-save."""

import sys
from pathlib import Path

import pygame

from data_loader import QuestLoader
from system_core import Player, Quest
from system_hud import SystemHUD
from system_listener import VoiceListener
from system_voice import SystemVoice


def main() -> None:
    """Initialize LevelUp HUD application and run main event loop."""
    pygame.init()
    pygame.display.set_caption("LevelUp — Solo Leveling System HUD")

    # Command line argument mode selection
    initial_mode = "desktop"
    if len(sys.argv) > 1 and "mobile" in sys.argv[1].lower():
        initial_mode = "mobile"

    hud = SystemHUD(mode=initial_mode)
    screen = pygame.display.set_mode((hud.width, hud.height))
    clock = pygame.time.Clock()

    # Subsystem Initializations
    voice = SystemVoice(rate=160, volume=1.0)
    listener = VoiceListener()

    quests_filepath = Path("data/quests.json")
    quests = QuestLoader.load_quests(quests_filepath)
    player = Player(name="Sung Jin-Woo", level=1, xp=0)

    # State Machine: 'REGISTRATION', 'HUD', 'ADD_QUEST_MODAL'
    app_state = "REGISTRATION"
    voice.speak_async("System initialized. Please enter your Hunter name to proceed.")

    def toggle_viewport_mode() -> None:
        """Switch between Desktop (1024x768) and Mobile (450x850) HUD modes."""
        nonlocal screen
        new_mode = "mobile" if hud.mode == "desktop" else "desktop"
        hud.set_mode(new_mode)
        screen = pygame.display.set_mode((hud.width, hud.height))
        hud.set_feedback(f"Switched layout to {new_mode.upper()} view mode.")
        voice.speak_async(f"Viewport layout updated to {new_mode} mode.")

    def save_quests_state() -> None:
        """Helper to write current quest state back to JSON file."""
        QuestLoader.save_quests(quests, quests_filepath)

    def process_command(cmd_type: str, arg: any = None) -> None:
        """Unified command execution pipeline."""
        if cmd_type == "toggle_mode":
            toggle_viewport_mode()

        elif cmd_type == "levelup":
            required_xp = player.xp_to_next_level - player.xp
            leveled_up = player.gain_xp(required_xp)
            if leveled_up:
                voice.speak_async(f"Manual override: Level increased to Level {player.level}.")
                hud.trigger_level_up()
                hud.set_feedback(f"Level Up triggered! Reached Level {player.level}.")

        elif cmd_type == "complete_index":
            idx = int(arg)
            if 0 <= idx < len(quests):
                q = quests[idx]
                if not q.is_completed:
                    leveled_up = q.complete(player, voice=voice)
                    save_quests_state()
                    if leveled_up:
                        hud.trigger_level_up()
                    hud.set_feedback(f"Completed: '{q.title}' (+{q.xp_reward} XP). Saved.")
                else:
                    hud.set_feedback(f"Quest [{idx + 1}] is already completed.", is_error=True)

        elif cmd_type == "complete_keyword":
            kw = str(arg).lower()
            matched = False
            for idx, q in enumerate(quests):
                if (kw in q.title.lower() or kw in q.category.lower()) and not q.is_completed:
                    leveled_up = q.complete(player, voice=voice)
                    save_quests_state()
                    if leveled_up:
                        hud.trigger_level_up()
                    hud.set_feedback(f"Completed: '{q.title}' (+{q.xp_reward} XP). Saved.")
                    matched = True
                    break
            if not matched:
                hud.set_feedback(f"No incomplete quest matching '{arg}' found.", is_error=True)

        elif cmd_type == "addquest":
            if isinstance(arg, dict):
                title = arg.get("title", "New Assignment").strip() or "New Assignment"
                xp = int(arg.get("xp", 50))
                cat = arg.get("category", "General").strip() or "General"

                new_q = Quest(f"Q{len(quests)+1}", title, xp, cat)
                quests.append(new_q)
                save_quests_state()

                hud.set_feedback(f"Added quest: '{title}' (+{xp} XP). Saved.")
                voice.speak_async(f"New quest added: {title}.")

    def parse_typed_text(text: str) -> None:
        """Parse raw command line text typed into the text console."""
        clean = text.strip()
        if not clean:
            return

        if clean.startswith("/"):
            clean = clean[1:]

        parts = clean.split(maxsplit=1)
        action = parts[0].lower()
        param = parts[1] if len(parts) > 1 else ""

        if action in ("complete", "done", "finish"):
            if param.isdigit():
                process_command("complete_index", int(param) - 1)
            elif param:
                process_command("complete_keyword", param)
            else:
                hud.set_feedback("Specify quest number or title to complete.", is_error=True)

        elif action in ("levelup", "level", "lvl"):
            process_command("levelup")

        elif action in ("mode", "toggle", "mobile", "desktop"):
            process_command("toggle_mode")

        elif action in ("add", "addquest") and param:
            tokens = [t.strip() for t in param.split("|")]
            title = tokens[0] if len(tokens) > 0 else "New Quest"
            xp = int(tokens[1]) if len(tokens) > 1 and tokens[1].isdigit() else 50
            cat = tokens[2] if len(tokens) > 2 else "General"
            process_command("addquest", {"title": title, "xp": xp, "category": cat})

        elif action in ("exit", "quit"):
            sys.exit(0)

        else:
            process_command("complete_keyword", clean)

    def submit_add_quest_modal() -> None:
        """Process modal submission for creating a new quest."""
        nonlocal app_state
        title = hud.add_quest_title.strip() or "New Assignment"
        try:
            xp = int(hud.add_quest_xp.strip())
        except ValueError:
            xp = 50
        cat = hud.add_quest_category.strip() or "General"

        process_command("addquest", {"title": title, "xp": xp, "category": cat})
        app_state = "HUD"

    running = True
    while running:
        clock.tick(60)

        # Process Voice Commands if in HUD state
        if app_state == "HUD":
            voice_cmd = listener.get_command()
            if voice_cmd:
                cmd_name, cmd_arg = voice_cmd
                hud.set_feedback(f"Voice Command: '{listener.last_heard}'")
                process_command(cmd_name, cmd_arg)

        # Pygame Event Loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos = event.pos
                    hitboxes = hud.hitboxes

                    if app_state == "REGISTRATION":
                        if hitboxes["reg_confirm"].collidepoint(pos) or hitboxes["reg_input"].collidepoint(pos):
                            player.name = hud.reg_name_text.strip() or "Sung Jin-Woo"
                            app_state = "HUD"
                            voice.speak_async(f"Welcome, Hunter {player.name}. System HUD online.")
                            hud.set_feedback(f"Welcome, Hunter {player.name}. Ready for assignments.")

                    elif app_state == "ADD_QUEST_MODAL":
                        if hitboxes["modal_title_input"].collidepoint(pos):
                            hud.add_quest_field_focus = 0
                        elif hitboxes["modal_xp_input"].collidepoint(pos):
                            hud.add_quest_field_focus = 1
                        elif hitboxes["modal_cat_input"].collidepoint(pos):
                            hud.add_quest_field_focus = 2
                        elif hitboxes["modal_save"].collidepoint(pos):
                            submit_add_quest_modal()
                        elif hitboxes["modal_cancel"].collidepoint(pos):
                            app_state = "HUD"

                    elif app_state == "HUD":
                        if hitboxes["mode_button"].collidepoint(pos):
                            toggle_viewport_mode()

                        elif hitboxes["add_quest_button"].collidepoint(pos):
                            hud.add_quest_title = ""
                            hud.add_quest_xp = "50"
                            hud.add_quest_category = "General"
                            hud.add_quest_field_focus = 0
                            app_state = "ADD_QUEST_MODAL"

                        elif hitboxes["input_bar"].collidepoint(pos):
                            hud.input_focused = True

                        elif hitboxes["send_button"].collidepoint(pos):
                            parse_typed_text(hud.command_text)
                            hud.command_text = ""
                            hud.input_focused = False

                        else:
                            hud.input_focused = False
                            for card_rect, q_idx in hitboxes["quest_cards"]:
                                if card_rect.collidepoint(pos):
                                    process_command("complete_index", q_idx)
                                    break

            elif event.type == pygame.KEYDOWN:
                if app_state == "REGISTRATION":
                    if event.key == pygame.K_RETURN:
                        player.name = hud.reg_name_text.strip() or "Sung Jin-Woo"
                        app_state = "HUD"
                        voice.speak_async(f"Welcome, Hunter {player.name}. System HUD online.")
                        hud.set_feedback(f"Welcome, Hunter {player.name}. Ready for assignments.")
                    elif event.key == pygame.K_BACKSPACE:
                        hud.reg_name_text = hud.reg_name_text[:-1]
                    else:
                        if len(event.unicode) > 0 and event.unicode.isprintable():
                            hud.reg_name_text += event.unicode

                elif app_state == "ADD_QUEST_MODAL":
                    if event.key == pygame.K_ESCAPE:
                        app_state = "HUD"
                    elif event.key == pygame.K_TAB:
                        hud.add_quest_field_focus = (hud.add_quest_field_focus + 1) % 3
                    elif event.key == pygame.K_RETURN:
                        submit_add_quest_modal()
                    elif event.key == pygame.K_BACKSPACE:
                        if hud.add_quest_field_focus == 0:
                            hud.add_quest_title = hud.add_quest_title[:-1]
                        elif hud.add_quest_field_focus == 1:
                            hud.add_quest_xp = hud.add_quest_xp[:-1]
                        elif hud.add_quest_field_focus == 2:
                            hud.add_quest_category = hud.add_quest_category[:-1]
                    else:
                        if len(event.unicode) > 0 and event.unicode.isprintable():
                            if hud.add_quest_field_focus == 0:
                                hud.add_quest_title += event.unicode
                            elif hud.add_quest_field_focus == 1 and event.unicode.isdigit():
                                hud.add_quest_xp += event.unicode
                            elif hud.add_quest_field_focus == 2:
                                hud.add_quest_category += event.unicode

                elif app_state == "HUD":
                    if hud.input_focused:
                        if event.key == pygame.K_RETURN:
                            parse_typed_text(hud.command_text)
                            hud.command_text = ""
                            hud.input_focused = False
                        elif event.key == pygame.K_BACKSPACE:
                            hud.command_text = hud.command_text[:-1]
                        elif event.key == pygame.K_ESCAPE:
                            hud.input_focused = False
                        else:
                            if len(event.unicode) > 0 and event.unicode.isprintable():
                                hud.command_text += event.unicode
                    else:
                        if event.key in (pygame.K_q, pygame.K_ESCAPE):
                            running = False
                            break
                        elif event.key == pygame.K_m:
                            toggle_viewport_mode()
                        elif event.key == pygame.K_l:
                            process_command("levelup")
                        elif event.key == pygame.K_SLASH or event.key == pygame.K_RETURN:
                            hud.input_focused = True
                        elif pygame.K_1 <= event.key <= pygame.K_9:
                            process_command("complete_index", event.key - pygame.K_1)

        # Render Frame
        try:
            hud.render(
                screen,
                player,
                quests,
                mic_status=listener.status_message,
                app_state=app_state,
            )
            pygame.display.flip()
        except Exception as render_err:
            pass

    # Clean Exit
    listener.stop()
    voice.stop()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
