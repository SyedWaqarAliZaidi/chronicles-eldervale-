"""
setup_foundry_iq.py — Upload world lore to Azure AI Search (Foundry IQ)
Run this ONCE before playing to populate the knowledge base.

Usage:
    python setup_foundry_iq.py
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
)
from azure.core.credentials import AzureKeyCredential

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX", "eldervale-lore")
DATA_DIR = Path("data")


def create_index():
    """Create the Azure AI Search index with semantic configuration."""
    print(f"Creating index '{INDEX_NAME}' with semantic configuration...")

    index_client = SearchIndexClient(
        endpoint=SEARCH_ENDPOINT,
        credential=AzureKeyCredential(SEARCH_KEY)
    )

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchableField(name="source", type=SearchFieldDataType.String),
        SearchableField(name="tags", type=SearchFieldDataType.String),
        SimpleField(name="doc_type", type=SearchFieldDataType.String, filterable=True),
    ]

    # Semantic configuration — required by Foundry IQ
    semantic_config = SemanticConfiguration(
        name="eldervale-semantic",
        prioritized_fields=SemanticPrioritizedFields(
            content_fields=[SemanticField(field_name="content")],
            keywords_fields=[SemanticField(field_name="tags")],
            title_field=SemanticField(field_name="source")
        )
    )
    semantic_search = SemanticSearch(configurations=[semantic_config])

    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        semantic_search=semantic_search
    )

    try:
        index_client.delete_index(INDEX_NAME)
        print(f"  Deleted existing index.")
    except:
        pass

    index_client.create_index(index)
    print(f"  ✓ Index created with semantic configuration.")


def parse_markdown_to_chunks(filepath: Path) -> list[dict]:
    """Parse a markdown file into searchable chunks."""
    content = filepath.read_text(encoding="utf-8")
    chunks = []

    sections = content.split("\n## ")

    for i, section in enumerate(sections):
        if not section.strip():
            continue

        if section.startswith("# "):
            section = section[2:]

        lines = section.strip().split("\n")
        title = lines[0].strip().replace("#", "").strip()
        body = "\n".join(lines[1:]).strip()

        if not body:
            continue

        tags = ""
        for line in lines:
            if line.strip().startswith("**Tags**:"):
                tags = line.replace("**Tags**:", "").strip()

        chunk_id = f"{filepath.stem}_{i}_{title[:30].replace(' ', '_').lower()}"
        chunk_id = "".join(c if c.isalnum() or c == "_" else "" for c in chunk_id)

        chunks.append({
            "id": chunk_id,
            "content": f"# {title}\n\n{body}",
            "source": f"{filepath.stem}.md — {title}",
            "tags": tags,
            "doc_type": filepath.stem
        })

    return chunks


def upload_lore_documents():
    """Upload all lore markdown files to Azure AI Search."""
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY)
    )

    all_chunks = []

    for md_file in DATA_DIR.glob("*.md"):
        print(f"  Processing {md_file.name}...")
        chunks = parse_markdown_to_chunks(md_file)
        all_chunks.extend(chunks)
        print(f"    -> {len(chunks)} sections extracted")

    if not all_chunks:
        print("ERROR: No markdown files found in data/ directory!")
        return

    print(f"\nUploading {len(all_chunks)} knowledge chunks to Foundry IQ...")

    batch_size = 50
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        result = search_client.upload_documents(documents=batch)
        succeeded = sum(1 for r in result if r.succeeded)
        print(f"  Batch {i//batch_size + 1}: {succeeded}/{len(batch)} uploaded OK")

    print(f"\n✓ Foundry IQ knowledge base populated with {len(all_chunks)} lore chunks!")


def test_search():
    """Test that Foundry IQ retrieval is working."""
    print("\nTesting Foundry IQ retrieval...")

    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY)
    )

    test_queries = [
        "Moonlit Gate ruins",
        "Bran Ironvale warrior",
        "magic surge Ashfields",
        "Kael Thorn rival"
    ]

    for query in test_queries:
        results = list(search_client.search(query, top=1))
        if results:
            print(f"  OK '{query}' -> found: {results[0]['source']}")
        else:
            print(f"  MISS '{query}' -> no results")

    print("\nFoundry IQ is ready!")


if __name__ == "__main__":
    print("=" * 60)
    print("CHRONICLES OF ELDERVALE — Foundry IQ Setup")
    print("=" * 60)
    print()

    if not SEARCH_ENDPOINT or not SEARCH_KEY:
        print("ERROR: Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_KEY in .env")
        exit(1)

    print(f"Search endpoint: {SEARCH_ENDPOINT}")
    print(f"Index name: {INDEX_NAME}")
    print()

    create_index()
    upload_lore_documents()
    test_search()

    print("\n" + "=" * 60)
    print("Setup complete! Run 'python main.py' to start playing.")
    print("=" * 60)
