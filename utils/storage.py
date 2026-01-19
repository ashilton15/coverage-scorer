"""Storage utilities for data persistence with Google Sheets integration."""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import Google Sheets functions
from utils.google_sheets import (
    get_clients_from_sheets, save_clients_to_sheets, add_client_to_sheets,
    update_client_in_sheets, delete_client_from_sheets,
    get_outlets_from_sheets, save_outlets_to_sheets, add_outlet_to_sheets,
    update_outlet_in_sheets, delete_outlet_from_sheets, bulk_update_outlet_tiers_in_sheets,
    get_history_from_sheets, save_history_to_sheets, add_to_history_sheets,
    delete_history_item_from_sheets, get_history_by_batch_from_sheets,
    test_connection, initialize_sheets
)

DATA_DIR = Path(__file__).parent.parent / "data"
STATIC_DIR = Path(__file__).parent.parent / "static"

def ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)
    STATIC_DIR.mkdir(exist_ok=True)

def load_json(filename: str, default: Any = None) -> Any:
    """Load JSON file from data directory."""
    ensure_data_dir()
    filepath = DATA_DIR / filename
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default if default is not None else {}
    return default if default is not None else {}

def save_json(filename: str, data: Any) -> None:
    """Save data to JSON file in data directory."""
    ensure_data_dir()
    filepath = DATA_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# Client Profile Functions (using Google Sheets)
def get_clients() -> List[Dict]:
    """Get all client profiles from Google Sheets."""
    return get_clients_from_sheets()

def save_clients(clients: List[Dict]) -> None:
    """Save client profiles to Google Sheets."""
    save_clients_to_sheets(clients)

def get_client_by_id(client_id: str) -> Optional[Dict]:
    """Get a specific client by ID."""
    clients = get_clients()
    for client in clients:
        if client.get("id") == client_id:
            return client
    return None

def add_client(client: Dict) -> None:
    """Add a new client profile to Google Sheets."""
    add_client_to_sheets(client)

def update_client(client_id: str, updated_client: Dict) -> bool:
    """Update an existing client profile in Google Sheets."""
    return update_client_in_sheets(client_id, updated_client)

def delete_client(client_id: str) -> bool:
    """Delete a client profile from Google Sheets."""
    return delete_client_from_sheets(client_id)

# Outlet Functions (using Google Sheets)
def get_outlets() -> List[Dict]:
    """Get all outlets from Google Sheets."""
    return get_outlets_from_sheets()

def save_outlets(outlets: List[Dict]) -> None:
    """Save outlets to Google Sheets."""
    save_outlets_to_sheets(outlets)

def get_outlet_by_id(outlet_id: str) -> Optional[Dict]:
    """Get a specific outlet by ID."""
    outlets = get_outlets()
    for outlet in outlets:
        if outlet.get("id") == outlet_id:
            return outlet
    return None

def add_outlet(outlet: Dict) -> None:
    """Add a new outlet to Google Sheets."""
    add_outlet_to_sheets(outlet)

def update_outlet(outlet_id: str, updated_outlet: Dict) -> bool:
    """Update an existing outlet in Google Sheets."""
    return update_outlet_in_sheets(outlet_id, updated_outlet)

def delete_outlet(outlet_id: str) -> bool:
    """Delete an outlet from Google Sheets."""
    return delete_outlet_from_sheets(outlet_id)

def bulk_update_outlet_tiers(outlet_ids: List[str], new_tier: int) -> int:
    """Bulk update tier for multiple outlets in Google Sheets."""
    return bulk_update_outlet_tiers_in_sheets(outlet_ids, new_tier)

# Config Functions
def get_config() -> Dict:
    """Get application configuration."""
    return load_json("config.json", {
        "api_key": "",
        "logo_path": ""
    })

def save_config(config: Dict) -> None:
    """Save application configuration."""
    save_json("config.json", config)

def get_api_key() -> str:
    """Get the Anthropic API key."""
    return get_config().get("api_key", "")

def save_api_key(api_key: str) -> None:
    """Save the Anthropic API key."""
    config = get_config()
    config["api_key"] = api_key
    save_config(config)

def get_logo_path() -> str:
    """Get the logo file path."""
    return get_config().get("logo_path", "")

def save_logo(uploaded_file) -> str:
    """Save uploaded logo and return path."""
    ensure_data_dir()
    logo_path = STATIC_DIR / f"logo_{uploaded_file.name}"
    with open(logo_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    config = get_config()
    config["logo_path"] = str(logo_path)
    save_config(config)
    return str(logo_path)

# History Functions (using Google Sheets)
def get_history() -> List[Dict]:
    """Get analysis history from Google Sheets."""
    return get_history_from_sheets()

def save_history(history: List[Dict]) -> None:
    """Save analysis history to Google Sheets."""
    save_history_to_sheets(history)

def add_to_history(analysis: Dict) -> None:
    """Add an analysis to history in Google Sheets."""
    add_to_history_sheets(analysis)

def get_history_item(item_id: str) -> Optional[Dict]:
    """Get a specific history item by ID."""
    history = get_history()
    for item in history:
        if item.get("id") == item_id:
            return item
    return None

def delete_history_item(item_id: str) -> bool:
    """Delete a history item from Google Sheets."""
    return delete_history_item_from_sheets(item_id)


# Batch Functions
def get_batches() -> List[Dict]:
    """Get all batch summaries."""
    return load_json("batches.json", [])


def save_batches(batches: List[Dict]) -> None:
    """Save batch summaries."""
    save_json("batches.json", batches)


def add_batch(batch: Dict) -> str:
    """
    Add a new batch summary and return its ID.

    Args:
        batch: Dict containing batch_name, client, article_count,
               successful_count, failed_count, avg_score

    Returns:
        The generated batch_id
    """
    batches = get_batches()
    batch_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    batch["batch_id"] = batch_id
    batch["created_at"] = datetime.now().isoformat()
    batches.insert(0, batch)  # Most recent first
    save_batches(batches)
    return batch_id


def get_batch_by_id(batch_id: str) -> Optional[Dict]:
    """Get a specific batch by ID."""
    batches = get_batches()
    for batch in batches:
        if batch.get("batch_id") == batch_id:
            return batch
    return None


def delete_batch(batch_id: str) -> bool:
    """Delete a batch summary."""
    batches = get_batches()
    initial_len = len(batches)
    batches = [b for b in batches if b.get("batch_id") != batch_id]
    if len(batches) < initial_len:
        save_batches(batches)
        return True
    return False


def get_history_by_batch(batch_id: str) -> List[Dict]:
    """Get all history items belonging to a specific batch from Google Sheets."""
    return get_history_by_batch_from_sheets(batch_id)


def get_unique_batch_names() -> List[str]:
    """Get list of unique batch names from batches."""
    batches = get_batches()
    return sorted([b.get("batch_name", "") for b in batches if b.get("batch_name")])


def update_batch_article(batch_id: str, article_index: int, updated_article: Dict) -> bool:
    """
    Update a specific article within a batch.

    Args:
        batch_id: The batch ID
        article_index: Index of the article in the batch's articles list
        updated_article: The updated article data

    Returns:
        True if update was successful, False otherwise
    """
    batches = get_batches()
    for batch in batches:
        if batch.get("batch_id") == batch_id:
            if "articles" in batch and 0 <= article_index < len(batch["articles"]):
                batch["articles"][article_index] = updated_article
                # Recalculate batch stats
                articles = batch["articles"]
                successful = sum(1 for a in articles if a.get("status") == "success")
                failed = sum(1 for a in articles if a.get("status") == "failed")
                scores = [a["total_score"] for a in articles if a.get("total_score") is not None]
                batch["successful_count"] = successful
                batch["failed_count"] = failed
                batch["avg_score"] = round(sum(scores) / len(scores), 1) if scores else 0
                save_batches(batches)
                return True
    return False


def delete_batch_with_history(batch_id: str) -> bool:
    """Delete a batch (articles are embedded, so no separate history cleanup needed)."""
    return delete_batch(batch_id)
