<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0D1117,50:6366F1,100:8B5CF6&height=180&section=header&text=Chronicles%20of%20Eldervale&fontSize=34&fontColor=A78BFA&animation=fadeIn&fontAlignY=40&desc=Multi-Agent%20Fantasy%20RPG%20powered%20by%20Microsoft%20Foundry%20IQ&descAlignY=62&descSize=15&descColor=C4B5FD" width="100%"/>

> *The moon shattered 100 years ago. Six AI agents hold the truth. The Centennial is 12 days away.*

[![Microsoft Foundry IQ](https://img.shields.io/badge/Microsoft_Foundry_IQ-6366F1?style=for-the-badge&logo=microsoftazure&logoColor=white)](https://ai.azure.com)
[![Reasoning Agents](https://img.shields.io/badge/Track-Reasoning_Agents-8B5CF6?style=for-the-badge&logo=target&logoColor=white)](#)
[![Groq](https://img.shields.io/badge/LLM-Groq_LLaMA_3.3-A78BFA?style=for-the-badge&logo=lightning&logoColor=white)](https://groq.com)
[![Python](https://img.shields.io/badge/Python_3.10+-0D1117?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

</div>

<br/>

## `$ hackathon --submission`

| | |
|---|---|
| **Event** | Agents League Hackathon — Microsoft |
| **Track** | Reasoning Agents (Challenge B — Role Play Game System) |
| **IQ Layer** | Foundry IQ (Azure AI Search — grounded world lore retrieval) |

<br/>

## `$ what --is-this`

Chronicles of Eldervale is a **multi-agent fantasy RPG** where each character in the game is a separate AI agent with its own personality, memory, and reasoning capabilities. Players explore a dark fantasy world through natural language — typing actions and watching six AI agents collaborate to narrate the story.

This is not a chatbot. It is a **coordinated multi-agent reasoning system** disguised as a game.

<br/>

## `$ cat agents.md`

<div align="center">

| Agent | Role | Special Ability |
|:---|:---|:---|
| 🎭 **Game Master** | Orchestrator + Narrator | Queries Foundry IQ, dispatches agents, resolves dice, narrates scenes |
| ⚔️ **Bran Ironvale** | Warrior | Tactical assessment, combat, protection |
| 🔮 **Lyra Vey** | Mage | Foundry IQ lore retrieval, magical analysis |
| 🗡️ **Zara Dusk** | Rogue | Stealth, scouting, hidden information *(secret: Grey Fingers agent)* |
| 💚 **Finn Ashroot** | Healer | Ethical reasoning, Silver Root Order lore |
| 😈 **Kael Thorn** | Rival | Dynamic trust system, antagonist/ally *(secret: caused The Sundering)* |

</div>

<br/>

## `$ trace --reasoning-flow`

Every player turn triggers a **7-step reasoning pipeline**:

```
1. Player types an action
        ↓
2. Game Master analyzes action type
   (exploration / combat / dialogue / investigation)
        ↓
3. Game Master queries Foundry IQ
   → Retrieves grounded world lore (no hallucination)
        ↓
4. Game Master selects 2-3 relevant agents
        ↓
5. Selected agents respond in-character
   (Mage uses Foundry IQ for magical lore)
        ↓
6. Dice resolver runs if action uncertain
   (d20 roll + modifier vs difficulty class)
        ↓
7. Game Master synthesizes everything
   → Narrates final scene with citations from lore
```

<br/>

## `$ cat foundry-iq-integration.md`

Foundry IQ is the **knowledge backbone** of the entire game. Instead of agents hallucinating world details, they retrieve grounded, cited answers from the knowledge base.

**Knowledge base contains 24 lore chunks across:**

| File | Contents |
|:---|:---|
| `world_overview.md` | The Sundering, geography, magic system |
| `locations.md` | Moonlit Gate, Thornwall Village, Ashfields, Underpaths |
| `characters.md` | All agent profiles, motivations, secrets |
| `quests_factions_bestiary_rules.md` | Quests, factions, monsters, game mechanics |

**How agents use it:**

```python
# Mage agent queries Foundry IQ before answering
lore_results = query_foundry_iq("Moonlit Gate ancient magic", top=3)
# Returns cited, grounded lore — never invented
response = mage.respond(situation, lore_context=lore_results)
```

| Without Foundry IQ | With Foundry IQ |
|:---|:---|
| Agents invent inconsistent lore | Agents cite consistent, grounded world knowledge |

<br/>

## `$ tree --architecture`

```
┌────────────────────────────────────────────────────────────┐
│                Player (Browser)                         │
│              Chronicles of Eldervale UI                 │
└────────────────────────┬─────────────────────────────────-─┘
                          │ HTTP
┌────────────────────────▼────────────────────────────────-──┐
│                Flask Web Server                         │
│                    app.py                                │
└────────────────────────┬─────────────────────────────────-─┘
                          │
┌────────────────────────▼────────────────────────────────-──┐
│              Game Master Agent                           │
│           agents/game_master.py                          │
│  • Analyzes player input                                  │
│  • Queries Foundry IQ                                     │
│  • Dispatches to character agents                         │
│  • Resolves dice rolls                                    │
│  • Narrates final scene                                   │
└──┬──────────┬──────────┬─────────┬─────────┬───────────-──┘
   │         │         │         │         │
┌──▼──┐  ┌──▼──┐  ┌───▼──┐  ┌───▼──┐  ┌───▼───┐
│Bran │  │Lyra │  │ Zara │  │ Finn │  │ Kael  │
│⚔️   │  │🔮   │  │ 🗡️   │  │ 💚   │  │ 😈    │
└──┬──┘  └──┬──┘  └───┬──┘  └──┬───┘  └───┬───┘
   │        │ Foundry IQ Query │          │
   └────────┴──────────┬─────────┴───────────┘
                       │
        ┌──────────────▼──────────────────┐
        │      Microsoft Foundry IQ        │
        │  Azure AI Search — eldervale-lore │
        │  • 24 grounded lore chunks        │
        │  • Semantic search configuration  │
        │  • Cited, permission-aware retrieval│
        └──────────────────────────────────────┘
                       │
        ┌──────────────▼──────────────────┐
        │      Groq LLaMA 3.3 70B          │
        │   (LLM backbone for all agents)  │
        └──────────────────────────────────────┘
```

<br/>

## `$ ls features/`

- **Typing animation** — story appears letter by letter like a real RPG
- **Character highlighting** — agent cards glow when that character speaks
- **Dice rolling** — animated d20 with visual success/failure results
- **Clickable action buttons** — suggested next actions appear after each scene
- **World state tracking** — HP bars, location, time, discoveries panel
- **Persistent game state** — saves to JSON between sessions
- **12-day countdown** — urgency mechanic toward the Centennial
- **Dynamic rival trust** — Kael's behavior changes based on player choices

<br/>

## `$ setup --run`

#### Prerequisites
- Python 3.10+
- Groq API key (free): https://console.groq.com
- Azure account with AI Search resource (free tier)

#### Installation

```bash
git clone https://github.com/SyedWaqarAliZaidi/chronicles-eldervale-.git
cd chronicles-eldervale-

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

#### Configuration

```bash
cp .env.example .env
# Edit .env with your actual keys
```

Required values in `.env`:
```
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your_admin_key
AZURE_SEARCH_INDEX=eldervale-lore
```

#### Upload Lore to Foundry IQ

```bash
python setup_foundry_iq.py
```

This creates the Azure AI Search index with semantic configuration and uploads all 24 world lore chunks.

#### Run The Game

```bash
python app.py
```

Open `http://localhost:5000` and click **Begin Adventure**.

<br/>

## `$ tree --project-structure`

```
chronicles-eldervale/
├── agents/
│   ├── agents.py          # All 5 character agents
│   └── game_master.py     # Orchestrator — the brain
├── tools/
│   ├── foundry_iq.py      # Azure AI Search integration
│   └── game_tools.py      # Dice roller + state manager
├── data/                  # Synthetic world lore (Foundry IQ source)
│   ├── world_overview.md
│   ├── locations.md
│   ├── characters.md
│   └── quests_factions_bestiary_rules.md
├── templates/
│   └── game.html          # Full dark fantasy web UI
├── app.py                 # Flask web server
├── main.py                # Terminal version
├── setup_foundry_iq.py    # Foundry IQ setup script
└── requirements.txt
```

<br/>

## `$ cat tech-stack.md`

<div align="center">

| Component | Technology |
|:---|:---|
| LLM Backend | Groq — LLaMA 3.3 70B Versatile |
| Knowledge Base | Microsoft Foundry IQ (Azure AI Search) |
| Web Framework | Flask |
| Frontend | Vanilla HTML/CSS/JS |
| State Management | JSON file persistence |
| Agent Framework | Custom Python multi-agent orchestration |

</div>

<br/>

## `$ cat security-notes.md`

- All data is **synthetic** — no real PII, customer data, or confidential information
- API keys stored in `.env` (never committed — see `.gitignore`)
- World lore documents are entirely fictional
- No real employee, customer, or organizational data used anywhere

<br/>

## `$ cat synthetic-data.md`

All game content is synthetic and fictional:

- **World:** Eldervale (original fictional setting)
- **Characters:** Bran, Lyra, Zara, Finn, Kael (entirely invented)
- **Lore:** The Sundering, Starwell Relic, Moonlit Gate (original fiction)
- **No:** real names, real locations, real organizations, real events

<br/>

<div align="center">

*Built for the Agents League Hackathon — Microsoft, June 2026*
*Track: Reasoning Agents | Challenge B: Role Play Game System*
*IQ Layer: Foundry IQ (Azure AI Search)*

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:8B5CF6,50:6366F1,100:0D1117&height=100&section=footer" width="100%"/>

</div>
