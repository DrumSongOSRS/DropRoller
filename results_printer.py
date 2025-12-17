"""
ResultsPrinter: Formats and prints drop simulation results with value summaries.

Handles formatting of pre-roll vs main table drops, and calculates value summaries
for alchable items and Giant's Foundry items.
"""

from typing import Dict, Optional, List
from item_store import ItemStore


def print_results(
    num_rolls: int,
    pre_roll_drops: Dict[str, int],
    main_table_drops: Dict[str, int],
    item_metadata: Dict = None,
    item_store: Optional[ItemStore] = None,
) -> None:
    """
    Print drop simulation results with optional value summaries.

    Prints results in order they appear in drop tables, separating pre-roll
    items above main table items. If item_store provided, adds alch and
    Giant's Foundry summaries for applicable items.

    Args:
        num_rolls: Number of rolls simulated (for header)
        pre_roll_drops: Dict of pre-roll items and quantities
        main_table_drops: Dict of main table items and quantities
        item_metadata: Dict mapping item names to {quantity, bar_type, alch_value}
        item_store: Optional ItemStore for value lookups (if None, skips summaries)
    """
    print(f"\nRolling the Martial Salvage Drop Table {num_rolls} times.\n")
    print("Rewards:")

    # Print pre-roll items first
    for item, quantity in pre_roll_drops.items():
        print(f"{item}: {quantity}")

    # Print main table separator and items
    print("\nMain Drop Table:")
    for item, quantity in main_table_drops.items():
        print(f"{item}: {quantity}")

    # Print value summaries if item_store available
    if item_store:
        print()
        _print_alch_summary(main_table_drops, item_metadata, item_store)
        _print_gf_summary(main_table_drops, item_metadata, item_store)


def _print_alch_summary(drops: Dict[str, int], item_metadata: Dict, item_store: ItemStore) -> None:
    """
    Print high alch value summary for alchable items.

    Shows items marked with alch_value: true and calculates total alch value and magic XP.
    Breaks down into two sections:
    - Alch All: All alchable items
    - Alch and Giant's Foundry: Only items that can also be used at GF (have bar_type)

    Magic XP = 65 XP per alch cast.

    Args:
        drops: Dict of items and quantities from main table
        item_metadata: Dict mapping items to {quantity, bar_type, alch_value}
        item_store: ItemStore for high_alch value lookups
    """
    xp_per_alch = 65
    
    # Collect all alchable items
    all_alch_items = []
    gf_and_alch_items = []
    
    for item, quantity in drops.items():
        # Check if item has alch value
        alch_value = item_metadata.get(item, {}).get("alch_value", False) if item_metadata else False
        if not alch_value:
            continue
        
        values = item_store.get_item_values(item)
        high_alch = values.get("high_alch")

        if high_alch is not None:
            item_alch = high_alch * quantity
            all_alch_items.append((item, quantity, high_alch, item_alch))
            
            # Check if also has bar_type (GF item)
            bar_type = item_metadata.get(item, {}).get("bar_type", None) if item_metadata else None
            if bar_type is not None:
                gf_and_alch_items.append((item, quantity, high_alch, item_alch))

    if all_alch_items:
        # Alch All section
        alch_total = sum(item[3] for item in all_alch_items)
        total_alchs = sum(item[1] for item in all_alch_items)  # Sum of quantities
        magic_xp = total_alchs * xp_per_alch
        
        print("Alch All:")
        for item, quantity, high_alch, item_alch in all_alch_items:
            print(f"  {item} × {quantity} @ {high_alch}gp = {item_alch:,}gp")
        print(f"Number of Alchs: {total_alchs}")
        print(f"Magic XP: {magic_xp:,}")
        print(f"Total Alch Value: {alch_total:,}")
        
        # Alch and Giant's Foundry section (only items that can't be used at GF)
        alch_only_items = [item for item in all_alch_items if item not in gf_and_alch_items]
        
        if alch_only_items:
            print("\nAlch and Giant's Foundry:")
            alch_only_total = sum(item[3] for item in alch_only_items)
            alch_only_alchs = sum(item[1] for item in alch_only_items)  # Sum of quantities
            alch_only_magic_xp = alch_only_alchs * xp_per_alch
            
            for item, quantity, high_alch, item_alch in alch_only_items:
                print(f"  {item} × {quantity} @ {high_alch}gp = {item_alch:,}gp")
            print(f"Number of Alchs: {alch_only_alchs}")
            print(f"Magic XP: {alch_only_magic_xp:,}")
            print(f"Total Alch Value: {alch_only_total:,}")


def _print_gf_summary(drops: Dict[str, int], item_metadata: Dict, item_store: ItemStore) -> None:
    """
    Print Giant's Foundry summary for craftable items.

    Shows items with bar_type defined and calculates bars yielded by type.
    Estimates XP assuming all moulds unlocked (16,570 XP per complete sword).
    XP is based on the limiting bar type (min complete sets of 14 bars).

    Args:
        drops: Dict of items and quantities from main table
        item_metadata: Dict mapping items to {quantity, bar_type, alch_value}
        item_store: ItemStore for bars_used value lookups
    """
    gf_items = []
    bars_by_type = {}  # Track bars by type

    for item, quantity in drops.items():
        # Check if item has bar_type (Giants Foundry item)
        bar_type = item_metadata.get(item, {}).get("bar_type", None) if item_metadata else None
        if bar_type is None:
            continue
        
        values = item_store.get_item_values(item)
        bars_used = values.get("bars_used")

        if bars_used is not None:
            bars_yielded = bars_used * quantity
            gf_items.append((item, quantity, bars_used, bars_yielded))
            
            # Track bars by type
            if bar_type not in bars_by_type:
                bars_by_type[bar_type] = 0
            bars_by_type[bar_type] += bars_yielded

    if gf_items:
        print("\nGiant's Foundry Summary:")
        for item, quantity, bars_used, bars_yielded in gf_items:
            print(f"  {item} × {quantity} @ {bars_used} bars = {bars_yielded} bars")
        
        # Print total bars yielded by type
        if bars_by_type:
            print("Total Bars Yielded:")
            for bar_type in sorted(bars_by_type.keys()):
                total = bars_by_type[bar_type]
                print(f"  {bar_type}: {total}")
        
        # Estimate XP: 16,570 XP per complete sword
        # Swords made = min(adamant_bars // 14, mithril_bars // 14)
        xp_per_sword = 16570
        bar_types = sorted(bars_by_type.keys())
        
        if len(bar_types) >= 2:
            # Calculate complete sword sets (limited by whichever bar type has fewer sets of 14)
            complete_sets = min(bars_by_type[bar_type] // 14 for bar_type in bar_types)
            estimated_xp = complete_sets * xp_per_sword
            print(f"Estimated XP (all moulds unlocked): {estimated_xp:,}")
        elif len(bar_types) == 1:
            # Only one bar type, can't make complete swords
            print(f"Estimated XP (all moulds unlocked): 0 (need both Adamant and Mithril bars)")
