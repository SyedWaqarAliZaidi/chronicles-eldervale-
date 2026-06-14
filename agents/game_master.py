"""
game_master.py — The Game Master Agent
The orchestrator. Receives player input, queries Foundry IQ,
dispatches to character agents, resolves dice, narrates the scene.
This is the heart of the multi-agent system.
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

from tools.foundry_iq import query_foundry_iq, format_lore_for_agent
from tools.game_tools import (
    load_state, save_state, add_to_history,
    resolve_check, roll_combat_attack, get_party_status
)
from agents.agents import get_all_agents, MageAgent

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

GAME_MASTER_SYSTEM = """You are the Game Master of Chronicles of Eldervale, a dark fantasy RPG.

YOUR THREE ROLES:
1. NARRATOR: Describe scenes cinematically. Make the world feel real and atmospheric.
2. WORLD BUILDER: Maintain consistency. What's true stays true.
3. ORCHESTRATOR: Coordinate character agents. Weave their responses into the narrative.

YOUR STYLE:
- Cinematic and atmospheric. Use sensory details (sound, smell, light).
- Present tense for scene descriptions.
- Second person for player actions: "You enter the chapel..."
- Give the player meaningful choices, not just description.
- When agents respond, weave their voices naturally into the scene.

GAME RULES YOU ENFORCE:
- Call for dice rolls when outcomes are uncertain
- Track day/night cycle (affects Moonstone Wraith spawns)
- Apply magic surge rules in the Ashfields (35% surge chance)
- Respect what Foundry IQ tells you about the world — cite it, don't contradict it

YOUR RESPONSE FORMAT:
Always end your narration with 2-3 player choices or a clear prompt for what they do next.
Keep narration to 3-5 paragraphs maximum.

MOST IMPORTANT RULE:
You are the final voice. Character agents give you their reactions — you synthesize everything 
into one coherent, atmospheric scene response. Make it feel like a real tabletop RPG session."""


class GameMasterAgent:
    """
    The Game Master — orchestrates the full multi-agent RPG loop.
    
    Per turn:
    1. Analyze player input
    2. Query Foundry IQ for relevant lore
    3. Determine which agents should react
    4. Collect agent responses
    5. Resolve any dice checks
    6. Narrate the final scene
    7. Update world state
    """
    
    def __init__(self):
        self.agents = get_all_agents()
        self.mage = self.agents["mage"]  # Mage has special Foundry IQ access
    
    def analyze_action(self, player_input: str, state: dict) -> dict:
        """
        Analyze what type of action the player is taking.
        Returns a plan for how to handle this turn.
        """
        analysis_prompt = f"""Analyze this player action in one JSON response:

Player action: "{player_input}"
Current location: {state['location']}
Time of day: {state['time_of_day']}
In combat: {state['combat']['in_combat']}

Return ONLY valid JSON with these fields:
{{
  "action_type": "exploration|combat|dialogue|investigation|travel|rest",
  "requires_dice_roll": true/false,
  "check_type": "Stealth|Arcana|Attack|Perception|Persuasion|Athletics|null",
  "difficulty": 8-20,
  "agents_to_involve": ["warrior", "mage", "rogue", "healer", "rival"],
  "foundry_iq_query": "what to search in the knowledge base",
  "involves_magic": true/false,
  "time_passes": "none|hour|halfday|day"
}}

agents_to_involve: pick 1-3 most relevant agents. Only include rival if they're nearby.
foundry_iq_query: what lore would be relevant to retrieve for this scene."""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a JSON-only response system. Return only valid JSON."},
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=400,
            temperature=0.3
        )
        
        try:
            text = response.choices[0].message.content.strip()
            # Clean up markdown code blocks if present
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except:
            # Fallback plan
            return {
                "action_type": "exploration",
                "requires_dice_roll": False,
                "check_type": None,
                "difficulty": 12,
                "agents_to_involve": ["warrior", "mage"],
                "foundry_iq_query": player_input,
                "involves_magic": False,
                "time_passes": "none"
            }
    
    def query_world_knowledge(self, query: str) -> str:
        """Query Foundry IQ for relevant world lore."""
        results = query_foundry_iq(query, top=3)
        return format_lore_for_agent(results)
    
    def collect_agent_responses(
        self,
        agents_to_involve: list[str],
        situation: str,
        lore_context: str,
        state: dict
    ) -> dict[str, str]:
        """
        Dispatch to relevant character agents and collect their responses.
        This is the multi-agent coordination step.
        """
        responses = {}
        
        party_context = f"""
Current location: {state['location']}
Time: {state['time_of_day']}
Party status: All party members present and healthy.
World flags: {json.dumps(state['world_flags'], indent=2)}
Rival trust level: {state['rival']['trust_level']}

Recent history:
{self._format_history(state)}
"""
        
        for agent_role in agents_to_involve:
            if agent_role not in self.agents:
                continue
            
            agent = self.agents[agent_role]
            
            # Mage gets special Foundry IQ access for magic analysis
            if agent_role == "mage" and "magic" in situation.lower():
                response = self.mage.analyze_magic(situation, party_context)
            else:
                full_context = f"{party_context}\n\nLORE FROM ARCHIVES:\n{lore_context}"
                response = agent.respond(situation, full_context)
            
            responses[agent.name] = response
        
        return responses
    
    def resolve_dice_if_needed(self, plan: dict, player_input: str, state: dict) -> dict | None:
        """Roll dice if the action requires it."""
        if not plan["requires_dice_roll"]:
            return None
        
        # Determine who's rolling and what modifier
        check_type = plan["check_type"]
        difficulty = plan["difficulty"]
        
        # Figure out which party member is doing the action
        actor = "Player"
        modifier = 2  # Default moderate competence
        
        if "stealth" in player_input.lower() or "sneak" in player_input.lower():
            actor = "Zara Dusk"
            modifier = 4  # Rogue is good at stealth
        elif "magic" in player_input.lower() or "spell" in player_input.lower() or "arcane" in player_input.lower():
            actor = "Lyra Vey"
            modifier = 5  # Mage is good at arcana
            # Apply magic surge in Ashfields
            if "ashfield" in state["location"].lower():
                import random
                if random.randint(1, 20) <= 7:
                    modifier -= 3  # Surge reduces effective roll
        elif "attack" in player_input.lower() or "fight" in player_input.lower() or "strike" in player_input.lower():
            actor = "Bran Ironvale"
            modifier = 4  # Warrior is good at combat
        elif "heal" in player_input.lower() or "tend" in player_input.lower():
            actor = "Finn Ashroot"
            modifier = 4  # Healer is good at medicine
        
        return resolve_check(actor, check_type, modifier, difficulty)
    
    def narrate_scene(
        self,
        player_input: str,
        plan: dict,
        lore_context: str,
        agent_responses: dict[str, str],
        dice_result: dict | None,
        state: dict
    ) -> str:
        """
        The Game Master synthesizes everything into the final scene narration.
        This is the money shot — the output the player actually sees.
        """
        # Format agent responses for the GM prompt
        agent_voices = ""
        for character_name, response in agent_responses.items():
            agent_voices += f"\n{character_name}: \"{response}\"\n"
        
        # Format dice result
        dice_text = ""
        if dice_result:
            dice_text = f"""
DICE RESULT:
{json.dumps(dice_result, indent=2)}
"""
        
        narration_prompt = f"""You are the Game Master. Narrate the scene for this player action.

PLAYER ACTION: "{player_input}"

CURRENT STATE:
- Location: {state['location']}
- Time: {state['time_of_day']}
- Days until Centennial: {state['days_until_centennial']}
- Active quest: {state['active_quest']}

RELEVANT WORLD LORE (from Foundry IQ):
{lore_context}

PARTY REACTIONS (weave these naturally into your narration):
{agent_voices}

{dice_text}

INSTRUCTIONS:
1. Write an atmospheric scene narration (3-4 paragraphs)
2. Naturally incorporate the character voices where they fit
3. If there was a dice roll, narrate the outcome based on the result
4. Reference the lore context where relevant — this grounds the world
5. End with 2-3 clear options for what the player can do next

Begin narrating now:"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": GAME_MASTER_SYSTEM},
                {"role": "user", "content": narration_prompt}
            ],
            max_tokens=800,
            temperature=0.85
        )
        
        return response.choices[0].message.content.strip()
    
    def process_turn(self, player_input: str) -> tuple[str, dict]:
        """
        MAIN ENTRY POINT — Process one complete player turn.
        
        This is the full multi-agent reasoning loop:
        1. Load state
        2. Analyze action
        3. Query Foundry IQ
        4. Collect agent responses
        5. Resolve dice
        6. Narrate scene
        7. Update state
        
        Returns: (narration, dice_result_if_any)
        """
        # Step 1: Load game state
        state = load_state()
        
        # Step 2: Analyze what type of action this is
        plan = self.analyze_action(player_input, state)
        
        # Step 3: Query Foundry IQ for relevant world lore
        lore_context = self.query_world_knowledge(plan["foundry_iq_query"])
        
        # Step 4: Collect character agent responses
        agent_responses = self.collect_agent_responses(
            plan["agents_to_involve"],
            player_input,
            lore_context,
            state
        )
        
        # Step 5: Resolve dice if needed
        dice_result = self.resolve_dice_if_needed(plan, player_input, state)
        
        # Step 6: Narrate the final scene
        narration = self.narrate_scene(
            player_input,
            plan,
            lore_context,
            agent_responses,
            dice_result,
            state
        )
        
        # Step 7: Update state
        self._update_state_from_action(plan, player_input, state)
        add_to_history(state, player_input, narration)
        
        return narration, dice_result
    
    def get_opening_scene(self) -> str:
        """Generate the opening narration for a new game."""
        state = load_state()
        lore = self.query_world_knowledge("Thornwall Village Eldervale Sundering overview")
        
        opening_prompt = f"""Generate an atmospheric opening scene for Chronicles of Eldervale.

WORLD LORE (from Foundry IQ):
{lore}

The player has just arrived in Thornwall Village with their party (Bran, Lyra, Zara, Finn).
It is evening. The three moon shards glow in the sky.
Their mission: reach the Moonlit Gate and retrieve the Starwell Relic.
They have 12 days until the Centennial.

Write a cinematic opening (3-4 paragraphs) that:
1. Sets the atmosphere of the world (broken moon, ashfields in the distance)  
2. Introduces the party briefly
3. Gives the player their first choice of what to do in Thornwall

Begin:"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": GAME_MASTER_SYSTEM},
                {"role": "user", "content": opening_prompt}
            ],
            max_tokens=600,
            temperature=0.9
        )
        
        return response.choices[0].message.content.strip()
    
    def _format_history(self, state: dict) -> str:
        """Format recent history for agent context."""
        if not state["history"]:
            return "No history yet — game just started."
        
        lines = []
        for entry in state["history"][-3:]:  # Last 3 turns
            lines.append(f"Turn {entry['turn']}: Player: {entry['player'][:80]}...")
        return "\n".join(lines)
    
    def _update_state_from_action(self, plan: dict, player_input: str, state: dict) -> None:
        """Update world state based on what happened this turn."""
        # Advance time
        time_map = {
            "hour": {"morning": "afternoon", "afternoon": "evening", "evening": "night", "night": "morning"},
            "halfday": {"morning": "evening", "afternoon": "night", "evening": "morning", "night": "afternoon"},
            "day": {"morning": "morning", "afternoon": "afternoon", "evening": "evening", "night": "night"}
        }
        
        if plan["time_passes"] in time_map:
            current = state["time_of_day"]
            state["time_of_day"] = time_map[plan["time_passes"]].get(current, current)
            if plan["time_passes"] == "day":
                state["days_until_centennial"] = max(0, state["days_until_centennial"] - 1)
        
        # Auto-detect world flag updates from player input
        player_lower = player_input.lower()
        
        if "sigil" in player_lower or "eye symbol" in player_lower:
            state["world_flags"]["gate_sigil_discovered"] = True
        
        if "journal" in player_lower and "aldren" in player_lower:
            state["world_flags"]["aldrens_journal_found"] = True
        
        save_state(state)
