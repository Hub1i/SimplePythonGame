Space Survivor
Space Survivor is a 2D top-down shooter game built using Python and Pygame, designed to run in a browser via Pyodide. You play as the last survivor on a derelict space station, fighting enemies, collecting resources, and upgrading your character to survive increasingly difficult challenges, including boss encounters.
Features

Dynamic Gameplay: Move with WASD, aim and shoot with the mouse, and interact with items (E) and chests (Q).
Progression System: Gain experience by defeating enemies, level up, and choose upgrades like increased damage, speed, or health regeneration.
Inventory Management: Collect weapons and items, switch between weapons (1-3 or mouse scroll), and manage ammo.
Procedural Map: A randomly generated map with walls and open spaces for exploration.
Enemies and Bosses: Fight drones, tanks, and periodic bosses with unique attack patterns.
Visual and Audio Effects: Particle effects for explosions and sound effects for shooting, pickups, and explosions.

Requirements

Python 3.8+ (for local development)
Pygame library
NumPy library
A modern web browser (for Pyodide deployment)
Pyodide environment (to run in the browser)

Installation

Clone the Repository:
git clone <repository-url>
cd space-survivor


Install Dependencies (for local development):
pip install pygame numpy


Run the Game Locally:
python main.py


Browser Deployment:

Ensure the game is hosted in a Pyodide-compatible environment.
The game uses Pyodide to run Python code in the browser, with no local file I/O or network calls.



Controls

WASD: Move the player.
Mouse: Aim and shoot (left-click).
E: Pick up items.
Q: Open chests.
1-3 or Mouse Scroll: Switch weapons.
ESC: Pause the game.
SPACE: Start the game from the title screen.
R: Restart after game over.

Gameplay

Objective: Survive waves of enemies, collect resources, and defeat bosses every 5 levels.
Items and Chests: Pick up health packs, ammo, and weapons from items or chests scattered across the map.
Upgrades: Choose from random upgrades upon leveling up to enhance your character's abilities.
Minimap: Located in the bottom-right corner, showing player, enemies, chests, and walls.
Game Over: If your health reaches zero, press R to restart.

Technical Notes

Pyodide Compatibility: The game is structured to run in a browser using Pyodide, with an asyncio-based game loop to prevent infinite loops. It checks for platform.system() == "Emscripten" to handle browser execution.
Sound Effects: Generated using NumPy arrays for explosion, shot, and pickup sounds, compatible with Pygame's sndarray module in Pyodide (2D arrays for stereo, no dtype keyword).
Performance: The game maintains a 60 FPS target, with a camera system for smooth map navigation and a minimap for situational awareness.
Pathfinding: Enemies use A* pathfinding to navigate around walls, with periodic path updates to balance performance.

Limitations

No local file I/O or network calls due to Pyodide restrictions.
Sound generation is limited to NumPy-based waveforms for compatibility.
The game is single-player with no multiplayer support.
Boss encounters are triggered every 5 levels, with no final "Core" boss implemented yet.

Future Improvements

Add more weapon types and enemy behaviors.
Implement a final boss ("Core") to complete the story.
Enhance map generation with rooms and corridors.
Add visual sprites for entities instead of colored rectangles.
Include more upgrade options and balance existing ones.

Contributing
Contributions are welcome! Please fork the repository, make your changes, and submit a pull request. Ensure any new features are compatible with Pyodide for browser execution.
License
This project is licensed under the MIT License. See the LICENSE file for details.
