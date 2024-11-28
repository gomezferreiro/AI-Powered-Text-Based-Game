
# Usage
from fantasy_game_master import FantasyGameMaster
from fantasy_world_generator import FantasyWorldGenerator
from helper import get_game_state, get_together_api_key, is_safe, run_action, start_game

world_json_path = './GeneratedWorld.json'

def main_loop(message, history):
    # Retrieve the game state with predefined inventory
    game_state = get_game_state(
        inventory={
            "cloth pants": 1,
            "cloth shirt": 1,
            "goggles": 1,
            "leather bound journal": 1,
            "gold": 5,
        }
    )

    output = run_action(message, history, game_state)
    
    # Check if the output is safe
    if not is_safe(output):
        return "Invalid Output"

    # Detect and update inventory
    game_master = FantasyGameMaster(api_key=get_together_api_key(), world_path=world_json_path, output_path=world_json_path)
    update_msg = game_master.process_inventory_updates(game_state, output)
    output += update_msg

    return output

if __name__ == "__main__":
    api_key = get_together_api_key()
    
    generator = FantasyWorldGenerator(api_key=api_key)
    generator.generate(world_json_path)

    game_master = FantasyGameMaster(api_key, world_json_path, world_json_path)
    game_master.initialize_game()

    start_game(main_loop, True)