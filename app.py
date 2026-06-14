"""
app.py — Chronicles of Eldervale Web Server
Flask backend that serves the game UI and handles player actions.
"""

from flask import Flask, render_template, request, jsonify, session
import os
import json
from dotenv import load_dotenv
from agents.game_master import GameMasterAgent
from tools.game_tools import load_state, save_state, get_party_status, INITIAL_STATE
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Global game master instance
gm = GameMasterAgent()


@app.route("/")
def index():
    return render_template("game.html")


@app.route("/api/start", methods=["POST"])
def start_game():
    """Start a new game or load existing."""
    try:
        data = request.json
        new_game = data.get("new_game", False)

        if new_game:
            state = INITIAL_STATE.copy()
            state["session_start"] = datetime.now().isoformat()
            save_state(state)

        state = load_state()

        if state["turn_count"] == 0:
            opening = gm.get_opening_scene()
            state = load_state()
            state["turn_count"] = 1
            save_state(state)
            return jsonify({
                "success": True,
                "message": opening,
                "dice": None,
                "state": get_state_summary(state),
                "is_opening": True
            })
        else:
            return jsonify({
                "success": True,
                "message": f"Welcome back to Eldervale. You are in {state['location']}. The Centennial is {state['days_until_centennial']} days away.",
                "dice": None,
                "state": get_state_summary(state),
                "is_opening": False
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/action", methods=["POST"])
def player_action():
    """Process a player action through the multi-agent system."""
    try:
        data = request.json
        player_input = data.get("action", "").strip()

        if not player_input:
            return jsonify({"success": False, "error": "No action provided"}), 400

        narration, dice_result = gm.process_turn(player_input)
        state = load_state()

        return jsonify({
            "success": True,
            "message": narration,
            "dice": dice_result,
            "state": get_state_summary(state)
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/state", methods=["GET"])
def get_state():
    """Get current game state."""
    try:
        state = load_state()
        return jsonify(get_state_summary(state))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_state_summary(state):
    """Extract relevant state for the UI."""
    party = []
    for role, member in state["party"].items():
        hp = member["health"]
        max_hp = member["max_health"]
        icons = {"warrior": "⚔️", "mage": "🔮", "rogue": "🗡️", "healer": "💚"}
        party.append({
            "role": role,
            "name": member["name"],
            "hp": hp,
            "max_hp": max_hp,
            "status": member["status"],
            "icon": icons.get(role, "👤"),
            "hp_pct": int((hp / max_hp) * 100)
        })

    return {
        "location": state["location"],
        "time": state["time_of_day"],
        "days_left": state["days_until_centennial"],
        "turn": state["turn_count"],
        "party": party,
        "rival_trust": state["rival"]["trust_level"],
        "flags": state["world_flags"]
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)
