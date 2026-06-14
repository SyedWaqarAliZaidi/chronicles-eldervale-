"""
main.py — Chronicles of Eldervale
Main game loop with rich terminal UI.
Run this to start playing.
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.rule import Rule
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from agents.game_master import GameMasterAgent
from tools.game_tools import load_state, get_party_status, save_state, INITIAL_STATE
from datetime import datetime

console = Console() if RICH_AVAILABLE else None


# ============================================================
# DISPLAY HELPERS
# ============================================================

def print_banner():
    """Print the game title banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║          CHRONICLES OF ELDERVALE                             ║
║          A Multi-Agent Fantasy RPG                           ║
║          Powered by Microsoft Foundry IQ + Groq              ║
╚═══════════════════════════════════════════════════════════════╝
"""
    if RICH_AVAILABLE:
        console.print(Panel(
            "[bold yellow]CHRONICLES OF ELDERVALE[/bold yellow]\n"
            "[dim]A Multi-Agent Fantasy RPG[/dim]\n"
            "[dim cyan]Powered by Microsoft Foundry IQ[/dim cyan]",
            border_style="yellow",
            expand=False
        ))
    else:
        print(banner)


def print_scene(narration: str):
    """Print the GM's narration with formatting."""
    if RICH_AVAILABLE:
        console.print()
        console.print(Rule("[yellow]◆ GAME MASTER ◆[/yellow]", style="yellow"))
        console.print()
        console.print(narration, style="white")
        console.print()
    else:
        print("\n" + "="*60)
        print("GAME MASTER:")
        print("="*60)
        print(narration)
        print()


def print_dice_result(dice_result: dict):
    """Print dice roll result with formatting."""
    if not dice_result:
        return
    
    result_colors = {
        "critical_success": "bold green",
        "success": "green",
        "partial": "yellow",
        "failure": "red",
        "critical_failure": "bold red"
    }
    
    color = result_colors.get(dice_result["result"], "white")
    
    if RICH_AVAILABLE:
        console.print()
        console.print(Rule("[cyan]◆ DICE ROLL ◆[/cyan]", style="cyan"))
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row("[dim]Actor[/dim]", dice_result["actor"])
        table.add_row("[dim]Check[/dim]", dice_result["check"])
        table.add_row("[dim]Roll[/dim]", f"d20 → {dice_result['roll']} + {dice_result['modifier']} = {dice_result['total']}")
        table.add_row("[dim]Difficulty[/dim]", str(dice_result["difficulty"]))
        table.add_row("[dim]Result[/dim]", f"[{color}]{dice_result['result'].upper().replace('_', ' ')}[/{color}]")
        
        console.print(table)
        
        if dice_result.get("natural_20"):
            console.print("[bold green]⚡ NATURAL 20! Critical Success![/bold green]")
        elif dice_result.get("natural_1"):
            console.print("[bold red]💀 NATURAL 1! Critical Failure![/bold red]")
        console.print()
    else:
        print(f"\n[DICE] {dice_result['actor']} | {dice_result['check']}")
        print(f"Roll: {dice_result['roll']} + {dice_result['modifier']} = {dice_result['total']} vs DC {dice_result['difficulty']}")
        print(f"Result: {dice_result['result'].upper()}")
        print()


def print_party_status(state: dict):
    """Print party status panel."""
    if RICH_AVAILABLE:
        console.print()
        console.print(Rule("[magenta]◆ PARTY STATUS ◆[/magenta]", style="magenta"))
        
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Character", style="bold")
        table.add_column("HP", justify="center")
        table.add_column("Status")
        table.add_column("Role")
        
        roles = {"warrior": "⚔️  Warrior", "mage": "🔮 Mage", "rogue": "🗡️  Rogue", "healer": "💚 Healer"}
        
        for role, member in state["party"].items():
            hp = member["health"]
            max_hp = member["max_health"]
            hp_pct = hp / max_hp
            
            if hp_pct > 0.6:
                hp_color = "green"
            elif hp_pct > 0.3:
                hp_color = "yellow"
            else:
                hp_color = "red"
            
            table.add_row(
                member["name"],
                f"[{hp_color}]{hp}/{max_hp}[/{hp_color}]",
                member["status"],
                roles.get(role, role)
            )
        
        console.print(table)
        console.print(f"\n[cyan]📍 Location:[/cyan] {state['location']}")
        console.print(f"[cyan]🌙 Time:[/cyan] {state['time_of_day'].capitalize()}")
        console.print(f"[cyan]⏳ Days until Centennial:[/cyan] [yellow]{state['days_until_centennial']}[/yellow]")
        console.print()
    else:
        print(get_party_status(state))


def print_help():
    """Print available commands."""
    if RICH_AVAILABLE:
        console.print(Panel(
            "[bold]COMMANDS[/bold]\n"
            "[cyan]/status[/cyan]    — Show party health and world state\n"
            "[cyan]/state[/cyan]     — Show full game state JSON\n"
            "[cyan]/new[/cyan]       — Start a new game (resets everything)\n"
            "[cyan]/help[/cyan]      — Show this help\n"
            "[cyan]/quit[/cyan]      — Save and exit\n\n"
            "[bold]TIPS[/bold]\n"
            "• Type your actions naturally: 'I search the room for hidden doors'\n"
            "• Ask about lore: 'Lyra, what do you know about the Moonlit Gate?'\n"
            "• Talk to party: 'I ask Bran what he thinks about the gate'\n"
            "• Combat: 'I attack the wraith with my sword'",
            title="[yellow]Help[/yellow]",
            border_style="dim"
        ))
    else:
        print("\nCOMMANDS: /status, /state, /new, /help, /quit")
        print("Type your actions naturally to play.\n")


def print_loading(message: str = "The Game Master considers..."):
    """Show loading indicator."""
    if RICH_AVAILABLE:
        console.print(f"\n[dim italic]{message}[/dim italic]")
    else:
        print(f"\n{message}")


# ============================================================
# MAIN GAME LOOP
# ============================================================

def new_game():
    """Reset to a fresh game state."""
    state = INITIAL_STATE.copy()
    state["session_start"] = datetime.now().isoformat()
    save_state(state)
    
    if os.path.exists("game_state.json"):
        if RICH_AVAILABLE:
            console.print("[yellow]Previous save cleared. Starting fresh...[/yellow]")
        else:
            print("Previous save cleared. Starting fresh...")


def main():
    """Main game loop."""
    print_banner()
    
    # Check for required environment variables
    missing = []
    if not os.getenv("GROQ_API_KEY"):
        missing.append("GROQ_API_KEY")
    if not os.getenv("AZURE_SEARCH_ENDPOINT"):
        missing.append("AZURE_SEARCH_ENDPOINT")
    if not os.getenv("AZURE_SEARCH_KEY"):
        missing.append("AZURE_SEARCH_KEY")
    
    if missing:
        if RICH_AVAILABLE:
            console.print(f"[red]Missing environment variables: {', '.join(missing)}[/red]")
            console.print("[yellow]Create a .env file from .env.example and fill in your keys.[/yellow]")
        else:
            print(f"Missing: {', '.join(missing)}")
            print("Create .env from .env.example")
        sys.exit(1)
    
    if RICH_AVAILABLE:
        console.print("\n[dim]Initializing Foundry IQ knowledge base connection...[/dim]")
        console.print("[dim]Loading character agents...[/dim]")
        console.print("[green]✓ All systems ready.[/green]\n")
    else:
        print("\nInitializing...")
    
    # Initialize Game Master
    gm = GameMasterAgent()
    
    # Load or create game state
    state = load_state()
    
    # Check if this is a new game
    if state["turn_count"] == 0:
        if RICH_AVAILABLE:
            console.print("[dim italic]Generating opening scene from Foundry IQ world knowledge...[/dim italic]\n")
        
        opening = gm.get_opening_scene()
        print_scene(opening)
        add_to_history = True
    else:
        if RICH_AVAILABLE:
            console.print(f"[green]Resuming game... Turn {state['turn_count']}[/green]")
        print_party_status(state)
    
    # Main loop
    if RICH_AVAILABLE:
        console.print("[dim]Type [bold]/help[/bold] for commands or describe your action to play.[/dim]\n")
    else:
        print("Type /help for commands. Describe your action to play.\n")
    
    while True:
        try:
            # Get player input
            if RICH_AVAILABLE:
                console.print(Rule(style="dim"))
                player_input = console.input("[bold green]> Your action:[/bold green] ").strip()
            else:
                player_input = input("\n> Your action: ").strip()
            
            if not player_input:
                continue
            
            # Handle commands
            if player_input.lower() == "/quit":
                if RICH_AVAILABLE:
                    console.print("\n[yellow]Game saved. Until next time, adventurer.[/yellow]")
                else:
                    print("\nGame saved. Until next time.")
                break
            
            elif player_input.lower() == "/help":
                print_help()
                continue
            
            elif player_input.lower() == "/status":
                state = load_state()
                print_party_status(state)
                continue
            
            elif player_input.lower() == "/state":
                state = load_state()
                if RICH_AVAILABLE:
                    console.print_json(json.dumps(state, indent=2))
                else:
                    print(json.dumps(state, indent=2))
                continue
            
            elif player_input.lower() == "/new":
                confirm = input("Start a new game? This will erase your save. (yes/no): ")
                if confirm.lower() == "yes":
                    new_game()
                    gm = GameMasterAgent()
                    state = load_state()
                    opening = gm.get_opening_scene()
                    print_scene(opening)
                continue
            
            # Process the player's action through the full multi-agent loop
            print_loading()
            
            narration, dice_result = gm.process_turn(player_input)
            
            # Display dice result first if there was one
            if dice_result:
                print_dice_result(dice_result)
            
            # Display the GM's narration
            print_scene(narration)
            
            # Refresh state display
            state = load_state()
        
        except KeyboardInterrupt:
            if RICH_AVAILABLE:
                console.print("\n\n[yellow]Game paused. Progress saved.[/yellow]")
            else:
                print("\n\nGame paused. Progress saved.")
            break
        
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Error: {e}[/red]")
                console.print("[dim]The Game Master recovers... Try a different action.[/dim]")
            else:
                print(f"Error: {e}")
                print("Try a different action.")


if __name__ == "__main__":
    main()
