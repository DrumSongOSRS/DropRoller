import sys
import importlib.util
import random
import io
import json
from contextlib import redirect_stdout
from collections import defaultdict
from pathlib import Path

from item_store import ItemStore
from results_printer import print_results

def parse_fraction(fraction_str):
    """
    Parse a fraction string to a float.
    Examples: "1/500" -> 0.002, "1/8.1" -> 0.123456...
    """
    if '/' in fraction_str:
        numerator, denominator = fraction_str.split('/')
        return float(numerator) / float(denominator)
    return float(fraction_str)

def load_drop_table(table_name):
    """
    Load drop_table from JSON file in drop-tables directory.
    Returns a tuple of (drop_table_dict, item_metadata_dict).
    
    drop_table_dict: {table_section: {item_name: drop_rate_float}}
    item_metadata_dict: {item_name: {quantity: float, uses: [str]}}
    """
    # Remove .json extension if present
    if table_name.endswith('.json'):
        table_name = table_name[:-5]
    
    json_path = Path("drop-tables") / f"{table_name}.json"
    
    if not json_path.exists():
        raise FileNotFoundError(f"Could not find {json_path}")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    if "drop_table" not in data:
        raise ValueError(f"No 'drop_table' found in {json_path}")
    
    # Build drop_table with parsed rates and metadata
    drop_table = {}
    item_metadata = {}
    
    for table_section, items in data["drop_table"].items():
        drop_table[table_section] = {}
        for item_name, item_data in items.items():
            # Parse rate
            rate = parse_fraction(item_data["rate"])
            drop_table[table_section][item_name] = rate
            
            # Store metadata (quantity, bar_type, alch_value)
            quantity = item_data.get("quantity", 1)
            bar_type = item_data.get("bar_type", None)
            alch_value = item_data.get("alch_value", False)
            item_metadata[item_name] = {
                "quantity": quantity,
                "bar_type": bar_type,
                "alch_value": alch_value
            }
    
    return drop_table, item_metadata

def parse_quantity(item_name):
    """
    Extract quantity from item name if present in parentheses.
    Returns (base_name, quantity).
    
    This function is now primarily for backward compatibility if needed.
    The JSON-based system stores quantity separately.
    
    Examples:
        "Adamant arrowtips (3)" -> ("Adamant arrowtips", 3)
        "Rune cannonball (1.5)" -> ("Rune cannonball", 1.5)
        "Broken sextant" -> ("Broken sextant", 1)
    """
    if '(' in item_name and item_name.endswith(')'):
        # Find the last opening parenthesis
        last_paren = item_name.rfind('(')
        try:
            quantity = float(item_name[last_paren+1:-1])
            base_name = item_name[:last_paren].strip()
            return base_name, quantity
        except ValueError:
            # If it's not a number in parentheses, treat whole thing as name
            return item_name, 1
    return item_name, 1

def roll_drop(drop_table):
    """
    Simulate a single roll of the drop table.
    Evaluates pre-rolls in order, and if none hit, rolls main table.
    Returns (item_name, table_type) where table_type is 'pre-roll' or 'main table'.
    """
    # Evaluate pre-rolls in order
    if "pre-roll" in drop_table:
        for item_name, drop_rate in drop_table["pre-roll"].items():
            if random.random() < drop_rate:
                return item_name, "pre-roll"
    
    # If no pre-roll hit, roll main table
    if "main table" in drop_table:
        all_items = list(drop_table["main table"].items())
        accumulated_prob = 0
        roll = random.random()
        
        for item_name, drop_rate in all_items:
            accumulated_prob += drop_rate
            if roll < accumulated_prob:
                return item_name, "main table"
    
    return None, None

def simulate_rolls(drop_table, item_metadata, num_rolls):
    """
    Simulate multiple rolls and aggregate results by table type.
    Returns a tuple of (pre_roll_results, main_table_results) dicts.
    Each dict maps {item_name: total_quantity (floored to int)}.
    
    Quantities from metadata are multiplied by roll count and floored.
    """
    pre_roll_results = defaultdict(float)
    main_table_results = defaultdict(float)
    
    for _ in range(num_rolls):
        item, table_type = roll_drop(drop_table)
        if item:
            # Get quantity from metadata (defaults to 1)
            quantity = item_metadata.get(item, {}).get("quantity", 1)
            
            if table_type == "pre-roll":
                pre_roll_results[item] += quantity
            else:
                main_table_results[item] += quantity
    
    # Floor all quantities to integers
    pre_roll_results = {k: int(v) for k, v in pre_roll_results.items()}
    main_table_results = {k: int(v) for k, v in main_table_results.items()}
    
    return pre_roll_results, main_table_results

def get_item_order(drop_table, table_type):
    """
    Get the order of items as they appear in the drop table.
    Returns a list of base item names (without quantity modifiers) in order.
    """
    if table_type not in drop_table:
        return []
    
    order = []
    for item_name in drop_table[table_type].keys():
        base_name, _ = parse_quantity(item_name)
        if base_name not in order:
            order.append(base_name)
    
    return order

def format_output(table_name, num_rolls, drop_table, pre_roll_results, main_table_results, item_metadata=None, item_store=None):
    """Format and print the results preserving dictionary order."""
    # Use results_printer for output
    print_results(num_rolls, pre_roll_results, main_table_results, item_metadata, item_store)

def main():
    if len(sys.argv) != 3:
        print("Usage: python drop_sim.py <table_name> <num_rolls>")
        print("Example: python drop_sim.py Martial_salvage 2")
        sys.exit(1)
    
    table_name = sys.argv[1]
    try:
        num_rolls = int(sys.argv[2])
    except ValueError:
        print(f"Error: num_rolls must be an integer, got '{sys.argv[2]}'")
        sys.exit(1)
    
    if num_rolls < 1:
        print("Error: num_rolls must be at least 1")
        sys.exit(1)
    
    # Load drop table
    try:
        drop_table, item_metadata = load_drop_table(table_name)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Initialize ItemStore and pre-load all items in drop table
    # This is done before simulation to catch errors early
    item_store = ItemStore("item_data.json")
    try:
        item_store.load()
        
        # Get all unique items from drop table and pre-load their values
        all_items = list(item_metadata.keys())
        if all_items:
            try:
                item_store.get_all_items(all_items)
            except Exception as e:
                print(f"Warning: Could not pre-load item values: {e}")
                print("Continuing without value summaries...")
                item_store = None
    except Exception as e:
        print(f"Warning: ItemStore initialization failed: {e}")
        print("Continuing without value summaries...")
        item_store = None
    
    # Simulate rolls
    pre_roll_results, main_table_results = simulate_rolls(drop_table, item_metadata, num_rolls)
    
    # Print results with optional value summaries
    format_output(table_name, num_rolls, drop_table, pre_roll_results, main_table_results, item_metadata, item_store)

if __name__ == "__main__":
    main()
