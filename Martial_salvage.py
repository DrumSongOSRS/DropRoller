drop_table = {
    "pre-roll" : {
        "clue scroll (hard)": 1/500,
        "Broken sextant":     1/3000,
        "Dragon cannonball":  1/3000,
        "Salvor's paint":      1/24000
    },
    "main table" : {
        "Mithril longsword": 1/8.1,
        "Adamant longsword":  1/12.15,
        "Adamant 2h sword": 1/24.3,
        "Green d'hide body": 1/24.3,
        "Rune longsword": 1/243,
        "Adamant arrowtips (3)": 1/8.1,
        "Mithril dart tip (3)": 1/8.1,
        "Adamant dart tip (2)": 1/12.15,
        "Adamant arrow (2)": 1/12.15,
        "Adamant bolts(unf) (2)": 1/24.3,
        "Rune arrow (2)": 1/24.3,
        "Adamant cannonball (2)": 1/24.3,
        "Rune cannonball (1.5)": 1/48.6,
        "Umbral frag": 19/4860,
        "Camphor seed": 19/4860,
        "Ironwood seed": 2/4860,
        "Amulet of power": 1/12.15,
        "Mahogany logs": 1/24.3,
        "Adamantite nails (2)": 1/48.6
    }
}

print(sum(drop_table["main table"].values()))


