from together import Together
from helper import get_together_api_key, save_world

class FantasyWorldGenerator:
    def __init__(self, api_key):
        self.client = Together(api_key=api_key)
        self.system_prompt = """
        Your job is to help create interesting fantasy worlds that players would love to play in.
        Instructions:
        - Only generate in plain text without formatting.
        - Use simple clear language without being flowery.
        - You must stay below 3-5 sentences for each description.
        """

    def create_prompt(self, template, **kwargs):
        return template.format(**kwargs)

    def generate_world(self):
        world_prompt = """
        Generate a creative description for a unique fantasy world with an
        interesting concept around cities built on the backs of massive beasts.

        Output content in the form:
        World Name: <WORLD NAME>
        World Description: <WORLD DESCRIPTION>

        World Name:
        """
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": world_prompt}
            ],
        )
        world_output = response.choices[0].message.content.strip()
        return {
            "name": world_output.split('\n')[0].replace('World Name: ', '').strip(),
            "description": '\n'.join(world_output.split('\n')[1:]).replace('World Description:', '').strip()
        }

    def generate_kingdoms(self, world):
        kingdom_prompt = self.create_prompt(
            """
            Create 3 different kingdoms for a fantasy world.
            For each kingdom generate a description based on the world it's in. 
            Describe important leaders, cultures, history of the kingdom.

            Output content in the form:
            Kingdom 1 Name: <KINGDOM NAME>
            Kingdom 1 Description: <KINGDOM DESCRIPTION>
            Kingdom 2 Name: <KINGDOM NAME>
            Kingdom 2 Description: <KINGDOM DESCRIPTION>
            Kingdom 3 Name: <KINGDOM NAME>
            Kingdom 3 Description: <KINGDOM DESCRIPTION>

            World Name: {name}
            World Description: {description}

            Kingdom 1
            """,
            name=world["name"],
            description=world["description"],
        )
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": kingdom_prompt}
            ],
        )
        kingdoms_output = response.choices[0].message.content.strip()
        kingdoms = {}
        for block in kingdoms_output.split('\n\n'):
            lines = block.strip().split('\n')
            name = lines[0].replace('Name: ', '').strip()
            description = lines[1].replace('Description: ', '').strip()
            kingdoms[name] = {"name": name, "description": description, "towns": {}}
        return kingdoms

    def generate_towns(self, world, kingdom):
        town_prompt = self.create_prompt(
            """
            Create 3 different towns for a fantasy kingdom and world.
            Describe the region it's in, important places of the town, 
            and interesting history about it.

            Output content in the form:
            Town 1 Name: <TOWN NAME>
            Town 1 Description: <TOWN DESCRIPTION>
            Town 2 Name: <TOWN NAME>
            Town 2 Description: <TOWN DESCRIPTION>
            Town 3 Name: <TOWN NAME>
            Town 3 Description: <TOWN DESCRIPTION>

            World Name: {world_name}
            World Description: {world_description}
            Kingdom Name: {kingdom_name}
            Kingdom Description: {kingdom_description}

            Town 1 Name:
            """,
            world_name=world["name"],
            world_description=world["description"],
            kingdom_name=kingdom["name"],
            kingdom_description=kingdom["description"],
        )
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": town_prompt}
            ],
        )
        towns_output = response.choices[0].message.content.strip()
        towns = {}
        for block in towns_output.split('\n\n'):
            lines = block.strip().split('\n')
            name = lines[0].replace('Name: ', '').strip()
            description = lines[1].replace('Description: ', '').strip()
            towns[name] = {"name": name, "description": description}
        return towns

    def generate_npcs(self, world, kingdom, town):
        npc_prompt = self.create_prompt(
            """
            Create 3 different characters based on the world, kingdom 
            and town they're in. Describe the character's appearance and 
            profession, as well as their deeper pains and desires.

            Output content in the form:
            Character 1 Name: <CHARACTER NAME>
            Character 1 Description: <CHARACTER DESCRIPTION>
            Character 2 Name: <CHARACTER NAME>
            Character 2 Description: <CHARACTER DESCRIPTION>
            Character 3 Name: <CHARACTER NAME>
            Character 3 Description: <CHARACTER DESCRIPTION>

            World Name: {world_name}
            World Description: {world_description}
            Kingdom Name: {kingdom_name}
            Kingdom Description: {kingdom_description}
            Town Name: {town_name}
            Town Description: {town_description}

            Character 1 Name:
            """,
            world_name=world["name"],
            world_description=world["description"],
            kingdom_name=kingdom["name"],
            kingdom_description=kingdom["description"],
            town_name=town["name"],
            town_description=town["description"],
        )
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": npc_prompt}
            ],
        )
        npcs_output = response.choices[0].message.content.strip()
        npcs = {}
        for block in npcs_output.split('\n\n'):
            lines = block.strip().split('\n')
            name = lines[0].replace('Name: ', '').strip()
            description = lines[1].replace('Description: ', '').strip()
            npcs[name] = {"name": name, "description": description}
        return npcs

    def generate(self, output_path):
        world = self.generate_world()
        world["kingdoms"] = self.generate_kingdoms(world)

        for kingdom in world["kingdoms"].values():
            kingdom["towns"] = self.generate_towns(world, kingdom)
            for town in kingdom["towns"].values():
                town["npcs"] = self.generate_npcs(world, kingdom, town)

        save_world(world, output_path)

# Usage
if __name__ == "__main__":
    api_key = get_together_api_key()
    generator = FantasyWorldGenerator(api_key=api_key)
    generator.generate('./GeneratedWorld.json')
