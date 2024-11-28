import json
import random
from helper import (
    load_world, save_world
)
from together import Together

class FantasyGameMaster:
    def __init__(self, api_key, world_path, output_path):
        self.client = Together(api_key=api_key)
        self.world_path = world_path
        self.output_path = output_path
        self.world = load_world(world_path)
        self.system_prompt = """You are an AI Game master. Your job is to create a 
        start to an adventure based on the world, kingdom, town, and character 
        a player is playing as. 
        Instructions:
        - Use 2-4 sentences.
        - Write in second person. For example: "You are Jack."
        - Write in present tense. For example: "You stand at..."
        - First, describe the character and their backstory.
        - Then describe where they start and what they see around them."""
        self.inventory_prompt = """You are an AI Game Assistant. \
        Your job is to detect changes to a player's \
        inventory based on the most recent story and game state.
        If a player picks up, or gains an item add it to the inventory \
        with a positive change_amount.
        If a player loses an item remove it from their inventory \
        with a negative change_amount.
        Given a player name, inventory and story, return a list of json update
        of the player's inventory in the following form.
        Only take items that it's clear the player (you) lost.
        Only give items that it's clear the player gained. 
        Don't make any other item updates.
        If no items were changed return {"itemUpdates": []}
        and nothing else.

        Response must be in Valid JSON
        Don't add items that were already added in the inventory

        Inventory Updates:
        {
            "itemUpdates": [
                {"name": <ITEM NAME>, 
                "change_amount": <CHANGE AMOUNT>}...
            ]
        }
        """

    def detect_inventory_changes(self, inventory, output):
        messages = [
            {"role": "system", "content": self.inventory_prompt},
            {"role": "user", "content": f"Current Inventory: {str(inventory)}"},
            {"role": "user", "content": f"Recent Story: {output}"},
            {"role": "user", "content": "Inventory Updates"},
        ]
        chat_completion = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            temperature=0.0,
            messages=messages,
        )
        response = chat_completion.choices[0].message.content
        return json.loads(response).get("itemUpdates", [])

    def update_inventory(self, inventory, item_updates):
        update_msg = ""

        for update in item_updates:
            name = update["name"]
            change_amount = update["change_amount"]

            if change_amount > 0:
                inventory[name] = inventory.get(name, 0) + change_amount
                update_msg += f"\nInventory: {name} +{change_amount}"
            elif change_amount < 0:
                if name in inventory:
                    inventory[name] += change_amount
                    update_msg += f"\nInventory: {name} {change_amount}"
                if inventory.get(name, 0) <= 0:
                    inventory.pop(name, None)

        return update_msg

    def process_inventory_updates(self, game_state, output):
        item_updates = self.detect_inventory_changes(game_state["inventory"], output)
        return self.update_inventory(game_state["inventory"], item_updates)

    def select_kingdom_town_character(self):
        """
        Dynamically select a kingdom, town, and character from the world.
        """
        kingdoms = self.world.get('kingdoms', {})
        if not kingdoms:
            raise ValueError("No kingdoms found in the world.")

        # Select a kingdom
        kingdom_name = input(f"Available Kingdoms: {list(kingdoms.keys())}\nSelect a kingdom: ") or random.choice(list(kingdoms.keys()))
        kingdom = kingdoms.get(kingdom_name)
        if not kingdom:
            raise ValueError(f"Kingdom '{kingdom_name}' not found in the world.")

        # Select a town
        towns = kingdom.get('towns', {})
        if not towns:
            raise ValueError(f"No towns found in the kingdom '{kingdom_name}'.")
        
        town_name = input(f"Available Towns in {kingdom_name}: {list(towns.keys())}\nSelect a town: ") or random.choice(list(towns.keys()))
        town = towns.get(town_name)
        if not town:
            raise ValueError(f"Town '{town_name}' not found in the kingdom '{kingdom_name}'.")

        # Select a character
        npcs = town.get('npcs', {})
        if not npcs:
            raise ValueError(f"No NPCs found in the town '{town_name}'.")
        
        character_name = input(f"Available Characters in {town_name}: {list(npcs.keys())}\nSelect a character: ") or random.choice(list(npcs.keys()))
        character = npcs.get(character_name)
        if not character:
            raise ValueError(f"Character '{character_name}' not found in the town '{town_name}'.")

        return kingdom, town, character

    def initialize_game(self):
        """
        Initialize the game setup with dynamic selection.
        """
        kingdom, town, character = self.select_kingdom_town_character()

        # Generate the starting adventure
        world_info = f"""
        World: {self.world['description']}
        Kingdom: {kingdom}
        Town: {town}
        Your Character: {character}
        """

        model_output = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            temperature=1.0,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": world_info + '\nYour Start:'}
            ],
        )

        start = model_output.choices[0].message.content

        # Update world with the starting point and save it
        self.world['start'] = start
        save_world(self.world, self.output_path)

        return {
            "world": self.world['description'],
            "kingdom": kingdom['description'],
            "town": town['description'],
            "character": character['description'],
            "start": start,
        }
