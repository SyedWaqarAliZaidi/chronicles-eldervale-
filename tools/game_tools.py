"""
tools.py — Game Tools
Dice rolling, state management, combat resolution.
These are the tools agents call during gameplay.
"""

import random
import json
import os
from datetime import datetime


# ============================================================
# DICE ROLLER
# ============================================================

def roll_dice(sides: int = 20, modifier: int = 0) -> dict:
    """
    Roll a dice and return structured result.
    
    Args:
        sides: Number of sides (d4, d6, d8, d10, d12, d20)
        modifier: Bonus/penalty to add to the roll
    
    Returns:
        Structured roll result
    """
    roll = random.randint(1, sides)
    total = roll + modifier
    
    return {
        "dice": f"d{sides}",
        "roll": roll,
        "modifier": modifier,
        "total": total,
        "natural_20": roll == 20 and sides == 20,
        "natural_1": roll == 1 and sides == 20
    }


def resolve_check(
    actor: str,
    check_type: str,
    modifier: int = 0,
    difficulty: int = 12
) -> dict:
    """
    Resolve an ability/skill check with full structured output.
    
    Args:
        actor: Character making the check
        check_type: Type of check (Stealth, Arcana, Attack, etc.)
        modifier: Character's bonus for this check
        difficulty: DC (Difficulty Class) to beat
    
    Returns:
        Full roll result with success/failure/partial outcome
    """
    roll_result = roll_dice(20, modifier)
    total = roll_result["total"]
    
    if total >= difficulty + 5:
        result = "critical_success"
        consequence_hint = "Exceptional outcome beyond what was attempted."
    elif total >= difficulty:
        result = "success"
        consequence_hint = "The action succeeds as intended."
    elif total >= difficulty - 3:
        result = "partial"
        consequence_hint = "Succeeds but with a complication or cost."
    else:
        result = "failure"
        consequence_hint = "The action fails."
    
    # Critical hits and fumbles
    if roll_result["natural_20"]:
        result = "critical_success"
        consequence_hint = "Natural 20 — exceptional success!"
    elif roll_result["natural_1"]:
        result = "critical_failure"
        consequence_hint = "Natural 1 — something goes wrong beyond just failing."
    
    return {
        "actor": actor,
        "check": check_type,
        "roll": roll_result["roll"],
        "modifier": modifier,
        "total": total,
        "difficulty": difficulty,
        "result": result,
        "consequence_hint": consequence_hint,
        "natural_20": roll_result["natural_20"],
        "natural_1": roll_result["natural_1"]
    }


def roll_combat_attack(
    attacker: str,
    target: str,
    attack_modifier: int,
    target_defense: int,
    damage_dice: int = 6,
    damage_modifier: int = 0
) -> dict:
    """Resolve a full combat attack."""
    attack_roll = resolve_check(attacker, "Attack", attack_modifier, target_defense)
    
    damage = 0
    if attack_roll["result"] in ["success", "critical_success"]:
        damage_roll = roll_dice(damage_dice, damage_modifier)
        damage = damage_roll["total"]
        if attack_roll["result"] == "critical_success":
            # Critical hit — roll damage twice
            damage += roll_dice(damage_dice)["roll"]
    
    return {
        **attack_roll,
        "target": target,
        "damage": damage,
        "hit": damage > 0
    }


# ============================================================
# GAME STATE MANAGER
# ============================================================

STATE_FILE = "game_state.json"

INITIAL_STATE = {
    "campaign": "Chronicles of Eldervale",
    "session_start": None,
    "turn_count": 0,
    "location": "Thornwall Village",
    "active_quest": "The Starwell Relic",
    "time_of_day": "evening",
    "days_until_centennial": 12,
    "party": {
        "warrior": {
            "name": "Bran Ironvale",
            "health": 28,
            "max_health": 28,
            "status": "healthy",
            "inventory": ["longsword", "shield", "torch", "rations x3"]
        },
        "mage": {
            "name": "Lyra Vey",
            "health": 14,
            "max_health": 14,
            "status": "healthy",
            "inventory": ["crystal focus", "spellbook", "dampening rings x2", "rations x3"]
        },
        "rogue": {
            "name": "Zara Dusk",
            "health": 18,
            "max_health": 18,
            "status": "healthy",
            "inventory": ["twin daggers", "shortbow", "arrows x20", "lockpicks", "rations x3"]
        },
        "healer": {
            "name": "Finn Ashroot",
            "health": 20,
            "max_health": 20,
            "status": "healthy",
            "inventory": ["wooden staff", "healing herbs x5", "Silver Root archives", "rations x3"]
        }
    },
    "rival": {
        "name": "Kael Thorn",
        "trust_level": "neutral",
        "last_seen": "unknown",
        "known_location": None
    },
    "world_flags": {
        "gate_sigil_discovered": False,
        "aldrens_journal_found": False,
        "three_truths_known": False,
        "gate_opened": False,
        "sundering_truth_revealed": False,
        "zaras_secret_revealed": False,
        "kaels_secret_revealed": False,
        "grey_fingers_encountered": False
    },
    "quest_log": {
        "main_quest_stage": 1,
        "side_quests_active": [],
        "completed": []
    },
    "combat": {
        "in_combat": False,
        "enemies": [],
        "round": 0
    },
    "history": []
}


def load_state() -> dict:
    """Load game state from file, or create fresh state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    else:
        state = INITIAL_STATE.copy()
        state["session_start"] = datetime.now().isoformat()
        save_state(state)
        return state


def save_state(state: dict) -> None:
    """Save game state to file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def update_state(key_path: str, value) -> dict:
    """
    Update a specific field in game state using dot notation.
    Example: update_state("world_flags.gate_opened", True)
    """
    state = load_state()
    keys = key_path.split(".")
    
    target = state
    for key in keys[:-1]:
        target = target[key]
    target[keys[-1]] = value
    
    save_state(state)
    return state


def get_party_status(state: dict) -> str:
    """Format party health status for display."""
    lines = ["=== PARTY STATUS ==="]
    for role, member in state["party"].items():
        hp = member["health"]
        max_hp = member["max_health"]
        hp_bar = "█" * (hp // 3) + "░" * ((max_hp - hp) // 3)
        status = member["status"]
        lines.append(f"{member['name']:15} HP: {hp:2}/{max_hp:2} [{hp_bar}] {status}")
    lines.append(f"\nLocation: {state['location']}")
    lines.append(f"Time: {state['time_of_day'].capitalize()}")
    lines.append(f"Days until Centennial: {state['days_until_centennial']}")
    return "\n".join(lines)


def add_to_history(state: dict, player_action: str, gm_response: str) -> dict:
    """Add a turn to the session history."""
    state["history"].append({
        "turn": state["turn_count"],
        "player": player_action,
        "gm": gm_response[:200] + "..." if len(gm_response) > 200 else gm_response
    })
    # Keep only last 10 turns in memory to avoid token bloat
    if len(state["history"]) > 10:
        state["history"] = state["history"][-10:]
    state["turn_count"] += 1
    save_state(state)
    return state


def heal_party_member(state: dict, role: str, amount: int) -> dict:
    """Heal a party member."""
    member = state["party"][role]
    old_hp = member["health"]
    member["health"] = min(member["health"] + amount, member["max_health"])
    member["status"] = "healthy" if member["health"] > 5 else "wounded"
    save_state(state)
    return member["health"] - old_hp  # Return actual amount healed


def damage_party_member(state: dict, role: str, amount: int) -> dict:
    """Apply damage to a party member."""
    member = state["party"][role]
    member["health"] = max(0, member["health"] - amount)
    if member["health"] == 0:
        member["status"] = "unconscious"
    elif member["health"] <= 5:
        member["status"] = "wounded"
    save_state(state)
    return member
