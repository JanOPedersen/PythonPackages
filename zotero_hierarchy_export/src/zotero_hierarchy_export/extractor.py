import sqlite3
import json
from pathlib import Path

def connect_db(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Database not found at: {path}")
    return sqlite3.connect(path)

def fetch_collections(conn):
    query = """
    SELECT collectionID, collectionName, parentCollectionID
    FROM collections
    """
    rows = conn.execute(query).fetchall()
    return [
        {
            "id": r[0],
            "name": r[1],
            "parent": r[2],
            "children": [],
            "items": []
        }
        for r in rows
    ]

def fetch_items_for_collections(conn):
    query = """
    SELECT c.collectionID, i.itemID, i.key
    FROM collectionItems c
    JOIN items i ON c.itemID = i.itemID
    """
    rows = conn.execute(query).fetchall()
    mapping = {}
    for coll_id, item_id, item_key in rows:
        mapping.setdefault(coll_id, []).append({
            "itemID": item_id,
            "key": item_key,
            "attachments": []
        })
    return mapping

def fetch_attachments(conn):
    query = """
    SELECT ia.parentItemID,
           ia.itemID,
           i.key,
           ia.path
    FROM itemAttachments ia
    JOIN items i ON ia.itemID = i.itemID
    """
    rows = conn.execute(query).fetchall()
    mapping = {}
    for parent_id, item_id, key, path in rows:
        mapping.setdefault(parent_id, []).append({
            "attachmentID": item_id,
            "key": key,
            "path": path
        })
    return mapping

def build_hierarchy(collections, items_map, attachments_map):
    index = {c["id"]: c for c in collections}

    for coll_id, items in items_map.items():
        for item in items:
            item_id = item["itemID"]
            item["attachments"] = attachments_map.get(item_id, [])
        if coll_id in index:
            index[coll_id]["items"] = items

    root_nodes = []
    for coll in collections:
        parent = coll["parent"]
        if parent and parent in index:
            index[parent]["children"].append(coll)
        else:
            root_nodes.append(coll)

    return root_nodes

def export_hierarchy(db_path: Path):
    conn = connect_db(db_path)
    collections = fetch_collections(conn)
    items_map = fetch_items_for_collections(conn)
    attachments_map = fetch_attachments(conn)
    hierarchy = build_hierarchy(collections, items_map, attachments_map)
    conn.close()
    return hierarchy

def export_to_json(hierarchy, output_path: Path):
    output_path.write_text(
        json.dumps(hierarchy, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
