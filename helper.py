# Add your utilities or helper functions to this file.

import os
import random
from dotenv import load_dotenv, find_dotenv
import json
import gradio as gr
from together import Together


# these expect to find a .env file at the directory above the lesson.                                                         
# the format for that file is (without the comment)                                                                           
# API_KEYNAME=AStringThatIsTheLongAPIKeyFromSomeService                                                                                                                                     
def load_env():
    _ = load_dotenv(find_dotenv())

def save_world(world, filename):
    with open(filename, 'w+') as f:
        json.dump(world, f)

def load_world(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def get_together_api_key():
     load_env()
     together_api_key = os.getenv("TOGETHER_AI_API_KEY")
     return together_api_key

def get_game_state(inventory={}):
    world = load_world('./GeneratedWorld.json')
    # Select a kingdom
    kingdoms = world.get('kingdoms', {})
    if not kingdoms:
        raise ValueError("No kingdoms found in the world.")
    kingdom_name = random.choice(list(kingdoms.keys()))
    kingdom = kingdoms[kingdom_name]

    # Select a town
    towns = kingdom.get('towns', {})
    if not towns:
        raise ValueError(f"No towns found in the kingdom '{kingdom_name}'.")
    town_name = random.choice(list(towns.keys()))
    town = towns[town_name]

    # Select a character
    npcs = town.get('npcs', {})
    if not npcs:
        raise ValueError(f"No NPCs found in the town '{town_name}'.")
    character_name = random.choice(list(npcs.keys()))
    character = npcs[character_name]

    start = world['start']

    game_state = {
        "world": world['description'],
        "kingdom": kingdom['description'],
        "town": town['description'],
        "character": character['description'],
        "start": start,
        "inventory": inventory
    }
    return game_state

def run_action(message, history, game_state):
    
    if(message == 'start game'):
        return game_state['start']
        
    system_prompt = """You are an AI Game master. Your job is to write what \
happens next in a player's adventure game.\
Instructions: \
You must on only write 1-3 sentences in response. \
Always write in second person present tense. \
Ex. (You look north and see...)
Don't let the player use items they don't have in their inventory.
"""
    
    world_info = f"""
World: {game_state['world']}
Kingdom: {game_state['kingdom']}
Town: {game_state['town']}
Your Character:  {game_state['character']}
Inventory: {json.dumps(game_state['inventory'])}"""


    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": world_info}
    ]

    for action in history:
        messages.append({"role": "assistant", "content": action[0]})
        messages.append({"role": "user", "content": action[1]})
           
    messages.append({"role": "user", "content": message})
    client = Together(api_key=get_together_api_key())
    model_output = client.chat.completions.create(
        model="meta-llama/Llama-3-70b-chat-hf",
        messages=messages
    )
    
    result = model_output.choices[0].message.content
    return result

def start_game(main_loop, share=False):
    demo = gr.ChatInterface(
        main_loop,
        chatbot=gr.Chatbot(height=250, placeholder="Type 'start game' to begin"),
        textbox=gr.Textbox(placeholder="What do you do next?", container=False, scale=7),
        title="AI RPG",
        # description="Ask Yes Man any question",
        theme="soft",
        examples=["start game", "Look around", "Continue the story"],
        cache_examples=False,
        retry_btn=None,
        undo_btn=None,
        clear_btn=None,
                           )
    demo.launch(share=share, server_name="0.0.0.0")


everyone_content_policy = {
    "policy": """O1: Violence and Hate.
Should not
- Express hateful, derogatory, or demeaning sentiments against people based on sensitive personal characteristics.
- Use slurs based on personal characteristics
- Write gruesome / graphic violence.
Can
- Write tame fantasy violence
O2: Sexual Content.
Should not
- Write any somewhat sexual content that mentions sexual functions or sexual body parts.
- Write any content that would be inappropriate for kids.
Can
- Write romantic content (including kissing, flirting etc...)
O3: Self-Harm.
Should not
- Encourage people to harm themselves.
- Romanticize or condone self-harm or suicide.
- Write story depicting suicide.
O4: Profanity.
Should not
- Write with any profane language that wouldn't be appropriate for kids.
Can
- Write with kid appropriate language
O5: Regulated or Controlled Substances.
Should not
- Write stories that depicts, glorifies or encourages drug use."""
}

def is_safe(message):
    # Build the prompt with embedded values
    prompt = f"""[INST] Task: Check if there is unsafe content in 'user' messages in conversations according to our safety policy with the below categories.
    
    <BEGIN UNSAFE CONTENT CATEGORIES>
    {everyone_content_policy['policy']}
    <END UNSAFE CONTENT CATEGORIES>
    
    <BEGIN CONVERSATION>
    user: {message}
    
    Provide your safety assessment for user in the above conversation:
    - First line must read 'safe' or 'unsafe'.
    - If unsafe, a second line must include a comma-separated list of violated categories. [/INST]"""
    
    client = Together(api_key=get_together_api_key())

    response = client.completions.create(
        model="Meta-Llama/LlamaGuard-2-8b",
        prompt=prompt,
    )
    result = response.choices[0].text
    return result.strip() == 'safe'

def main_loop(message, history, model="meta-llama/Llama-3-70b-chat-hf"):
    return run_action(message, history, model)