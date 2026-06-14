"""
foundry_iq.py — Foundry IQ Knowledge Base Integration
Uses Azure AI Search as the Foundry IQ backbone.
Agents query this to retrieve grounded world lore instead of hallucinating.
"""

import os
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX", "eldervale-lore")


def get_search_client() -> SearchClient:
    """Initialize Azure AI Search client (Foundry IQ backbone)."""
    return SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY)
    )


def query_foundry_iq(query: str, top: int = 3) -> list[dict]:
    """
    Query Foundry IQ knowledge base for relevant world lore.
    
    This is what agents call instead of hallucinating.
    Returns cited, grounded results from the knowledge base.
    
    Args:
        query: Natural language query about the world
        top: Number of results to return
    
    Returns:
        List of knowledge chunks with content and metadata
    """
    try:
        client = get_search_client()
        results = client.search(
            search_text=query,
            top=top,
            include_total_count=True
        )
        
        knowledge = []
        for result in results:
            knowledge.append({
                "content": result.get("content", ""),
                "source": result.get("source", "Eldervale Archives"),
                "tags": result.get("tags", ""),
                "score": result.get("@search.score", 0)
            })
        
        return knowledge
    
    except Exception as e:
        # Fallback: return empty if search fails
        print(f"[Foundry IQ] Search error: {e}")
        return []


def format_lore_for_agent(knowledge: list[dict]) -> str:
    """
    Format retrieved knowledge into a string for agent context.
    Includes citations so agents can reference the source.
    """
    if not knowledge:
        return "No specific lore found in the archives for this query."
    
    formatted = "=== FOUNDRY IQ KNOWLEDGE BASE RESULTS ===\n"
    for i, item in enumerate(knowledge, 1):
        formatted += f"\n[Source {i}: {item['source']}]\n"
        formatted += f"{item['content']}\n"
        formatted += "---\n"
    
    return formatted


def search_character(character_name: str) -> str:
    """Query Foundry IQ specifically for a character profile."""
    results = query_foundry_iq(f"character profile {character_name}", top=2)
    return format_lore_for_agent(results)


def search_location(location_name: str) -> str:
    """Query Foundry IQ specifically for a location."""
    results = query_foundry_iq(f"location {location_name}", top=2)
    return format_lore_for_agent(results)


def search_rules(rule_query: str) -> str:
    """Query Foundry IQ for game rules and mechanics."""
    results = query_foundry_iq(f"rules mechanics {rule_query}", top=2)
    return format_lore_for_agent(results)


def search_creature(creature_name: str) -> str:
    """Query Foundry IQ for bestiary entries."""
    results = query_foundry_iq(f"creature monster {creature_name}", top=2)
    return format_lore_for_agent(results)
