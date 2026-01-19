"""Google Sheets integration for data persistence."""
import json
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Configuration
CREDENTIALS_PATH = Path(__file__).parent.parent / "credentials.json"
SPREADSHEET_ID = "1JIXvOCmy2duAUjLaj1m1WDtD-onCoP1mjxn8AzBcTTc"

# Sheet names
CLIENTS_SHEET = "Clients"
OUTLETS_SHEET = "Outlets"
HISTORY_SHEET = "History"

# Scopes required for Google Sheets access
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Column headers for each sheet
CLIENTS_HEADERS = ["id", "name", "industry", "key_messages", "competitors", "created_at", "updated_at"]
OUTLETS_HEADERS = ["id", "name", "domain", "tier", "type", "reach_estimate"]
HISTORY_HEADERS = ["id", "headline", "outlet", "author", "client", "url", "total_score",
                   "tier_scores", "detailed_scores", "full_analysis", "analyzed_at", "batch_id"]

# Cache for the gspread client
_client = None
_spreadsheet = None


def get_client():
    """Get or create authenticated gspread client."""
    global _client
    if _client is None:
        credentials = Credentials.from_service_account_file(
            str(CREDENTIALS_PATH),
            scopes=SCOPES
        )
        _client = gspread.authorize(credentials)
    return _client


def get_spreadsheet():
    """Get or open the spreadsheet."""
    global _spreadsheet
    if _spreadsheet is None:
        client = get_client()
        _spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return _spreadsheet


def get_or_create_sheet(sheet_name: str, headers: List[str]):
    """Get a worksheet, creating it with headers if it doesn't exist."""
    spreadsheet = get_spreadsheet()
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        # Check if headers exist
        existing_headers = worksheet.row_values(1)
        if not existing_headers:
            worksheet.update('A1', [headers])
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(headers))
        worksheet.update('A1', [headers])
    return worksheet


def serialize_value(value: Any) -> str:
    """Serialize complex values to JSON strings for sheet storage."""
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return str(value)


def deserialize_value(value: str, expected_type: str = "string") -> Any:
    """Deserialize values from sheet storage."""
    if not value or value == "":
        if expected_type == "list":
            return []
        if expected_type == "dict":
            return {}
        if expected_type == "int":
            return 0
        if expected_type == "float":
            return 0.0
        return None

    if expected_type in ("list", "dict"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return [] if expected_type == "list" else {}
    elif expected_type == "int":
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    elif expected_type == "float":
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    return value


def row_to_client(row: List[str], headers: List[str]) -> Dict:
    """Convert a sheet row to a client dictionary."""
    if len(row) < len(headers):
        row.extend([""] * (len(headers) - len(row)))

    return {
        "id": row[headers.index("id")] if "id" in headers else "",
        "name": row[headers.index("name")] if "name" in headers else "",
        "industry": row[headers.index("industry")] if "industry" in headers else "",
        "key_messages": deserialize_value(row[headers.index("key_messages")] if "key_messages" in headers else "", "list"),
        "competitors": deserialize_value(row[headers.index("competitors")] if "competitors" in headers else "", "list"),
        "created_at": row[headers.index("created_at")] if "created_at" in headers else "",
        "updated_at": row[headers.index("updated_at")] if "updated_at" in headers else ""
    }


def client_to_row(client: Dict) -> List[str]:
    """Convert a client dictionary to a sheet row."""
    return [
        client.get("id", ""),
        client.get("name", ""),
        client.get("industry", ""),
        serialize_value(client.get("key_messages", [])),
        serialize_value(client.get("competitors", [])),
        client.get("created_at", ""),
        client.get("updated_at", "")
    ]


def row_to_outlet(row: List[str], headers: List[str]) -> Dict:
    """Convert a sheet row to an outlet dictionary."""
    if len(row) < len(headers):
        row.extend([""] * (len(headers) - len(row)))

    return {
        "id": row[headers.index("id")] if "id" in headers else "",
        "name": row[headers.index("name")] if "name" in headers else "",
        "domain": row[headers.index("domain")] if "domain" in headers else "",
        "tier": deserialize_value(row[headers.index("tier")] if "tier" in headers else "", "int"),
        "type": row[headers.index("type")] if "type" in headers else "",
        "reach_estimate": deserialize_value(row[headers.index("reach_estimate")] if "reach_estimate" in headers else "", "int")
    }


def outlet_to_row(outlet: Dict) -> List[str]:
    """Convert an outlet dictionary to a sheet row."""
    return [
        outlet.get("id", ""),
        outlet.get("name", ""),
        outlet.get("domain", ""),
        str(outlet.get("tier", 0)),
        outlet.get("type", ""),
        str(outlet.get("reach_estimate", 0))
    ]


def row_to_history(row: List[str], headers: List[str]) -> Dict:
    """Convert a sheet row to a history dictionary."""
    if len(row) < len(headers):
        row.extend([""] * (len(headers) - len(row)))

    return {
        "id": row[headers.index("id")] if "id" in headers else "",
        "headline": row[headers.index("headline")] if "headline" in headers else "",
        "outlet": row[headers.index("outlet")] if "outlet" in headers else "",
        "author": row[headers.index("author")] if "author" in headers else "",
        "client": row[headers.index("client")] if "client" in headers else "",
        "url": row[headers.index("url")] if "url" in headers else "",
        "total_score": deserialize_value(row[headers.index("total_score")] if "total_score" in headers else "", "float"),
        "tier_scores": deserialize_value(row[headers.index("tier_scores")] if "tier_scores" in headers else "", "dict"),
        "detailed_scores": deserialize_value(row[headers.index("detailed_scores")] if "detailed_scores" in headers else "", "dict"),
        "full_analysis": row[headers.index("full_analysis")] if "full_analysis" in headers else "",
        "analyzed_at": row[headers.index("analyzed_at")] if "analyzed_at" in headers else "",
        "batch_id": row[headers.index("batch_id")] if "batch_id" in headers else ""
    }


def history_to_row(history: Dict) -> List[str]:
    """Convert a history dictionary to a sheet row."""
    return [
        history.get("id", ""),
        history.get("headline", ""),
        history.get("outlet", ""),
        history.get("author", ""),
        history.get("client", ""),
        history.get("url", ""),
        str(history.get("total_score", 0)),
        serialize_value(history.get("tier_scores", {})),
        serialize_value(history.get("detailed_scores", {})),
        history.get("full_analysis", ""),
        history.get("analyzed_at", ""),
        history.get("batch_id", "")
    ]


# ==================== Client Functions ====================

def get_clients_from_sheets() -> List[Dict]:
    """Get all client profiles from Google Sheets."""
    try:
        worksheet = get_or_create_sheet(CLIENTS_SHEET, CLIENTS_HEADERS)
        all_values = worksheet.get_all_values()
        if len(all_values) <= 1:
            return []
        headers = all_values[0]
        clients = [row_to_client(row, headers) for row in all_values[1:] if any(row)]
        return clients
    except Exception as e:
        print(f"Error reading clients from sheets: {e}")
        return []


def save_clients_to_sheets(clients: List[Dict]) -> bool:
    """Save all client profiles to Google Sheets."""
    try:
        worksheet = get_or_create_sheet(CLIENTS_SHEET, CLIENTS_HEADERS)
        # Clear existing data (except headers)
        worksheet.clear()
        # Write headers and data
        data = [CLIENTS_HEADERS] + [client_to_row(c) for c in clients]
        worksheet.update('A1', data)
        return True
    except Exception as e:
        print(f"Error saving clients to sheets: {e}")
        return False


def add_client_to_sheets(client: Dict) -> bool:
    """Add a new client profile to Google Sheets."""
    try:
        worksheet = get_or_create_sheet(CLIENTS_SHEET, CLIENTS_HEADERS)
        client["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
        client["created_at"] = datetime.now().isoformat()
        worksheet.append_row(client_to_row(client))
        return True
    except Exception as e:
        print(f"Error adding client to sheets: {e}")
        return False


def update_client_in_sheets(client_id: str, updated_client: Dict) -> bool:
    """Update an existing client profile in Google Sheets."""
    try:
        worksheet = get_or_create_sheet(CLIENTS_SHEET, CLIENTS_HEADERS)
        all_values = worksheet.get_all_values()
        headers = all_values[0]
        id_col = headers.index("id") + 1

        # Find the row with the matching ID
        cell = worksheet.find(client_id, in_column=id_col)
        if cell:
            updated_client["id"] = client_id
            # Preserve created_at
            existing_row = all_values[cell.row - 1]
            created_at_idx = headers.index("created_at")
            updated_client["created_at"] = existing_row[created_at_idx] if created_at_idx < len(existing_row) else ""
            updated_client["updated_at"] = datetime.now().isoformat()
            worksheet.update(f'A{cell.row}', [client_to_row(updated_client)])
            return True
        return False
    except Exception as e:
        print(f"Error updating client in sheets: {e}")
        return False


def delete_client_from_sheets(client_id: str) -> bool:
    """Delete a client profile from Google Sheets."""
    try:
        worksheet = get_or_create_sheet(CLIENTS_SHEET, CLIENTS_HEADERS)
        headers = worksheet.row_values(1)
        id_col = headers.index("id") + 1

        cell = worksheet.find(client_id, in_column=id_col)
        if cell:
            worksheet.delete_rows(cell.row)
            return True
        return False
    except Exception as e:
        print(f"Error deleting client from sheets: {e}")
        return False


# ==================== Outlet Functions ====================

def get_outlets_from_sheets() -> List[Dict]:
    """Get all outlets from Google Sheets."""
    try:
        worksheet = get_or_create_sheet(OUTLETS_SHEET, OUTLETS_HEADERS)
        all_values = worksheet.get_all_values()
        if len(all_values) <= 1:
            return []
        headers = all_values[0]
        outlets = [row_to_outlet(row, headers) for row in all_values[1:] if any(row)]
        return outlets
    except Exception as e:
        print(f"Error reading outlets from sheets: {e}")
        return []


def save_outlets_to_sheets(outlets: List[Dict]) -> bool:
    """Save all outlets to Google Sheets."""
    try:
        worksheet = get_or_create_sheet(OUTLETS_SHEET, OUTLETS_HEADERS)
        # Clear existing data (except headers)
        worksheet.clear()
        # Write headers and data
        data = [OUTLETS_HEADERS] + [outlet_to_row(o) for o in outlets]
        worksheet.update('A1', data)
        return True
    except Exception as e:
        print(f"Error saving outlets to sheets: {e}")
        return False


def add_outlet_to_sheets(outlet: Dict) -> bool:
    """Add a new outlet to Google Sheets."""
    try:
        worksheet = get_or_create_sheet(OUTLETS_SHEET, OUTLETS_HEADERS)
        outlet["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
        worksheet.append_row(outlet_to_row(outlet))
        return True
    except Exception as e:
        print(f"Error adding outlet to sheets: {e}")
        return False


def update_outlet_in_sheets(outlet_id: str, updated_outlet: Dict) -> bool:
    """Update an existing outlet in Google Sheets."""
    try:
        worksheet = get_or_create_sheet(OUTLETS_SHEET, OUTLETS_HEADERS)
        headers = worksheet.row_values(1)
        id_col = headers.index("id") + 1

        cell = worksheet.find(outlet_id, in_column=id_col)
        if cell:
            updated_outlet["id"] = outlet_id
            worksheet.update(f'A{cell.row}', [outlet_to_row(updated_outlet)])
            return True
        return False
    except Exception as e:
        print(f"Error updating outlet in sheets: {e}")
        return False


def delete_outlet_from_sheets(outlet_id: str) -> bool:
    """Delete an outlet from Google Sheets."""
    try:
        worksheet = get_or_create_sheet(OUTLETS_SHEET, OUTLETS_HEADERS)
        headers = worksheet.row_values(1)
        id_col = headers.index("id") + 1

        cell = worksheet.find(outlet_id, in_column=id_col)
        if cell:
            worksheet.delete_rows(cell.row)
            return True
        return False
    except Exception as e:
        print(f"Error deleting outlet from sheets: {e}")
        return False


def bulk_update_outlet_tiers_in_sheets(outlet_ids: List[str], new_tier: int) -> int:
    """Bulk update tier for multiple outlets."""
    try:
        worksheet = get_or_create_sheet(OUTLETS_SHEET, OUTLETS_HEADERS)
        all_values = worksheet.get_all_values()
        headers = all_values[0]
        id_idx = headers.index("id")
        tier_idx = headers.index("tier")

        updated_count = 0
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) > id_idx and row[id_idx] in outlet_ids:
                worksheet.update_cell(i, tier_idx + 1, str(new_tier))
                updated_count += 1

        return updated_count
    except Exception as e:
        print(f"Error bulk updating outlet tiers: {e}")
        return 0


# ==================== History Functions ====================

def get_history_from_sheets() -> List[Dict]:
    """Get analysis history from Google Sheets."""
    try:
        worksheet = get_or_create_sheet(HISTORY_SHEET, HISTORY_HEADERS)
        all_values = worksheet.get_all_values()
        if len(all_values) <= 1:
            return []
        headers = all_values[0]
        history = [row_to_history(row, headers) for row in all_values[1:] if any(row)]
        return history
    except Exception as e:
        print(f"Error reading history from sheets: {e}")
        return []


def save_history_to_sheets(history: List[Dict]) -> bool:
    """Save all analysis history to Google Sheets."""
    try:
        worksheet = get_or_create_sheet(HISTORY_SHEET, HISTORY_HEADERS)
        # Clear existing data (except headers)
        worksheet.clear()
        # Write headers and data
        data = [HISTORY_HEADERS] + [history_to_row(h) for h in history]
        worksheet.update('A1', data)
        return True
    except Exception as e:
        print(f"Error saving history to sheets: {e}")
        return False


def add_to_history_sheets(analysis: Dict) -> bool:
    """Add an analysis to history in Google Sheets."""
    try:
        worksheet = get_or_create_sheet(HISTORY_SHEET, HISTORY_HEADERS)
        analysis["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
        analysis["analyzed_at"] = datetime.now().isoformat()
        # Insert at row 2 (after headers) to keep most recent first
        worksheet.insert_row(history_to_row(analysis), 2)
        return True
    except Exception as e:
        print(f"Error adding to history in sheets: {e}")
        return False


def delete_history_item_from_sheets(item_id: str) -> bool:
    """Delete a history item from Google Sheets."""
    try:
        worksheet = get_or_create_sheet(HISTORY_SHEET, HISTORY_HEADERS)
        headers = worksheet.row_values(1)
        id_col = headers.index("id") + 1

        cell = worksheet.find(item_id, in_column=id_col)
        if cell:
            worksheet.delete_rows(cell.row)
            return True
        return False
    except Exception as e:
        print(f"Error deleting history item from sheets: {e}")
        return False


def get_history_by_batch_from_sheets(batch_id: str) -> List[Dict]:
    """Get all history items belonging to a specific batch."""
    history = get_history_from_sheets()
    return [h for h in history if h.get("batch_id") == batch_id]


# ==================== Connection Test ====================

def test_connection() -> tuple[bool, str]:
    """Test the Google Sheets connection and return status."""
    try:
        spreadsheet = get_spreadsheet()
        # Try to get sheet info
        title = spreadsheet.title
        return True, f"Successfully connected to spreadsheet: {title}"
    except FileNotFoundError:
        return False, f"Credentials file not found at {CREDENTIALS_PATH}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def initialize_sheets() -> tuple[bool, str]:
    """Initialize all sheets with headers if they don't exist."""
    try:
        get_or_create_sheet(CLIENTS_SHEET, CLIENTS_HEADERS)
        get_or_create_sheet(OUTLETS_SHEET, OUTLETS_HEADERS)
        get_or_create_sheet(HISTORY_SHEET, HISTORY_HEADERS)
        return True, "All sheets initialized successfully"
    except Exception as e:
        return False, f"Error initializing sheets: {str(e)}"
