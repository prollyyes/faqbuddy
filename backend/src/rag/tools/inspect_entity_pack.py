#!/usr/bin/env python3
"""
Inspect a single Entity Pack in Pinecone (canonical + summary)
Usage examples:

  Inspect by table + PK:
    python3 -m backend.src.rag.tools.inspect_entity_pack --table Corso --pk <UUID>

  Inspect EdizioneCorso (composite key id + data):
    python3 -m backend.src.rag.tools.inspect_entity_pack --table EdizioneCorso --pk <UUID> --data S1/2024

  Inspect a sample row (auto-picks first row from Neon):
    python3 -m backend.src.rag.tools.inspect_entity_pack --table Corso --sample
"""

import os
import sys
import argparse
from typing import List, Tuple, Optional
from dotenv import load_dotenv
from pinecone import Pinecone

# Add src to path for absolute-style imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from rag.config import ADVANCED_DB_NAMESPACE
from utils.db_utils import get_connection, MODE


TABLE_PREFIX = {
    "Utente": "utente",
    "Insegnanti_Anagrafici": "insegnanti_anagrafici",
    "Dipartimento": "dipartimento",
    "Facolta": "facolta",
    "Corso_di_Laurea": "corso_di_laurea",
    "Corso": "corso",
    "EdizioneCorso": "edizione_corso",
    "Materiale_Didattico": "materiale",
    "Review": "review",
    "Tesi": "tesi",
    "Studenti": "studenti",
}


def sample_pk(table: str) -> Tuple[str, Optional[str]]:
    """Fetch a sample primary key (and data for EdizioneCorso) from Neon."""
    conn = get_connection(mode=MODE)
    cur = conn.cursor()
    try:
        if table == "EdizioneCorso":
            cur.execute("SELECT id, data FROM EdizioneCorso LIMIT 1")
            row = cur.fetchone()
            if not row:
                raise RuntimeError("No rows in EdizioneCorso")
            return str(row[0]), str(row[1])
        else:
            cur.execute(f"SELECT id FROM {table} LIMIT 1")
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"No rows in {table}")
            return str(row[0]), None
    finally:
        cur.close()
        conn.close()


def build_ids(table: str, pk: str, data: Optional[str]) -> List[str]:
    prefix = TABLE_PREFIX.get(table)
    if not prefix:
        raise ValueError(f"Unsupported table '{table}'")
    if table == "EdizioneCorso":
        if not data:
            raise ValueError("--data is required for EdizioneCorso")
        base = f"{prefix}_{pk}_{data}"
    else:
        base = f"{prefix}_{pk}"
    return [f"{base}__canonical", f"{base}__summary"]


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Inspect a single entity pack in Pinecone")
    parser.add_argument("--table", required=True, help="Table name (e.g., Corso, Facolta, EdizioneCorso)")
    parser.add_argument("--pk", help="Primary key value (UUID)")
    parser.add_argument("--data", help="EdizioneCorso 'data' value (e.g., S1/2024)")
    parser.add_argument("--sample", action="store_true", help="Sample a row from Neon if PK not specified")
    args = parser.parse_args()

    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY is not set")
        sys.exit(1)

    table = args.table.strip()
    pk = args.pk
    data = args.data

    if not pk:
        if args.sample:
            pk, maybe_data = sample_pk(table)
            if table == "EdizioneCorso" and not data:
                data = maybe_data
            print(f"📌 Sampled PK from Neon → table={table}, pk={pk}{', data='+data if data else ''}")
        else:
            print("❌ Provide --pk or use --sample to pick a row")
            sys.exit(1)

    ids = build_ids(table, pk, data)
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    from rag.config import INDEX_NAME
    index = pc.Index(INDEX_NAME)

    print(f"\n🔎 Fetching IDs in namespace '{ADVANCED_DB_NAMESPACE}': {ids}")
    out = index.fetch(ids=ids, namespace=ADVANCED_DB_NAMESPACE)
    vectors = out.get("vectors", {}) if isinstance(out, dict) else getattr(out, "vectors", {})
    if not vectors:
        print("⚠️ No vectors found. Ensure the entity packs were upserted and the namespace is correct.")
        sys.exit(2)

    for vid in ids:
        v = vectors.get(vid)
        if not v:
            print(f"\n— {vid}: not found")
            continue
        md = v.get("metadata", {}) if isinstance(v, dict) else getattr(v, "metadata", {})
        text = md.get("text", "")
        print(f"\n— {vid}")
        print(f"table_name: {md.get('table_name')}  node_type: {md.get('node_type')}  chunk_kind: {md.get('chunk_kind')}  pk: {md.get('primary_key')}")
        print("\nText:\n" + (text if text else "<empty>"))


if __name__ == "__main__":
    main()
