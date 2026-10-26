import json
import os

TRACKS_FILE = 'tracks/tracks.json'

def ensure_file_exists():
    if not os.path.exists('tracks'):
        os.makedirs('tracks')
    if not os.path.exists(TRACKS_FILE):
        default_data = {
            "1": {"name": "Grand Prix 1", "grid": [], "fastest_time": None}
        }
        with open(TRACKS_FILE, 'w') as f:
            json.dump(default_data, f, indent=4)

def get_all_slots():
    """Returns all track slots from the JSON file."""
    ensure_file_exists()
    try:
        with open(TRACKS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def create_new_slot(name="Track"):
    """Finds the highest existing slot ID and creates the next sequential slot."""
    ensure_file_exists()
    slots = get_all_slots()
    
    # Calculate next integer ID
    existing_ids = [int(k) for k in slots.keys() if k.isdigit()]
    next_id = str(max(existing_ids, default=0) + 1)
    
    slots[next_id] = {
        "name": f"{name} {next_id}",
        "grid": [],
        "fastest_time": None
    }
    
    with open(TRACKS_FILE, 'w') as f:
        json.dump(slots, f, indent=4)
        
    return next_id

def delete_slot(slot_id):
    """Deletes a slot by ID."""
    ensure_file_exists()
    slots = get_all_slots()
    if str(slot_id) in slots:
        del slots[str(slot_id)]
        with open(TRACKS_FILE, 'w') as f:
            json.dump(slots, f, indent=4)

def load_slot(slot_id, default_rows=14, default_cols=24):
    ensure_file_exists()
    try:
        with open(TRACKS_FILE, 'r') as f:
            data = json.load(f)
            slot_data = data.get(str(slot_id), {})
            grid = slot_data.get("grid", [])
            name = slot_data.get("name", f"Track {slot_id}")
            
            if not grid:
                grid = [[None] * default_cols for _ in range(default_rows)]
            return grid, name
    except Exception:
        return [[None] * default_cols for _ in range(default_rows)], f"Track {slot_id}"

def save_slot(slot_id, grid, name=None):
    ensure_file_exists()
    all_data = get_all_slots()
    existing_data = all_data.get(str(slot_id), {})
    track_name = name.strip() if name and name.strip() else existing_data.get("name", f"Track {slot_id}")
    
    all_data[str(slot_id)] = {
        "name": track_name,
        "grid": grid,
        "fastest_time": existing_data.get("fastest_time", None)
    }
    
    with open(TRACKS_FILE, 'w') as f:
        json.dump(all_data, f, indent=4)