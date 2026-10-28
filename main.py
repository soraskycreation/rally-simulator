import pygame
import sys
from scenes.menu import MainMenu
from scenes.editor import TrackEditor
from scenes.loading import LoadingScreen
from scenes.race import RaceScene

pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Pixel Rally Simulator")
clock = pygame.time.Clock()

# Start game on a 2.0-second Initial Startup Loading Sequence
current_scene = LoadingScreen(screen, target_action="STARTUP", min_duration=2.0)

running = True
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Only quit whole app on ESC if not in TrackEditor (with editing active) or RaceScene
                if not (isinstance(current_scene, TrackEditor) and current_scene.editing_name) and not isinstance(current_scene, RaceScene):
                    running = False

    # Scene Management Router
    if isinstance(current_scene, LoadingScreen):
        res = current_scene.update()
        if res and res.get("action") == "LOADING_COMPLETE":
            if res["target_action"] == "STARTUP":
                current_scene = MainMenu(screen)
            elif res["target_action"] == "EDIT":
                current_scene = TrackEditor(screen, slot_id=res["slot_id"])
            elif res["target_action"] == "RACE":
                # Launch Race Scene after loading
                current_scene = RaceScene(screen, slot_id=res["slot_id"])

    elif isinstance(current_scene, MainMenu):
        res = current_scene.handle_events(events)
        if res and res.get("action") == "START_LOAD":
            current_scene = LoadingScreen(screen, target_action=res["target_action"], slot_id=res["slot_id"], min_duration=0.8)

    elif isinstance(current_scene, TrackEditor):
        res = current_scene.handle_events(events)
        if res:
            if res["action"] == "MENU":
                current_scene = MainMenu(screen)
            elif res["action"] == "RACE":
                current_scene = LoadingScreen(screen, target_action="RACE", slot_id=res["slot_id"], min_duration=0.8)
        else:
            current_scene.update()

    elif isinstance(current_scene, RaceScene):
        res = current_scene.handle_events(events)
        if res:
            if res["action"] == "EDITOR":
                current_scene = TrackEditor(screen, slot_id=res["slot_id"])
            elif res["action"] == "MENU":
                current_scene = MainMenu(screen)
        else:
            current_scene.update()

    # Render Active Scene
    current_scene.draw()
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()