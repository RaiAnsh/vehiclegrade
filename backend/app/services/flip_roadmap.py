"""The "Level" roadmap: an ordered path from easy-to-resell cars to harder,
nicer, riskier ones, plus progress computed from a user's *sold* flips.

Levels are advice, not locks - `unlocked` only means the previous level's
graduation rule was met. Cars are matched on (make, model) so any generation
of a listed model counts toward that level.
"""

GRADUATE_MIN_SOLD = 2
GRADUATE_MAX_AVG_LOSS = 750  # average result must be no worse than -$750 to graduate

LEVELS = [
    {
        "level": 1, "name": "Daily-driver basics",
        "tagline": "Boring cars that sell fast. Learn the process while mistakes are cheap.",
        "why": "Huge buyer pool, cheap parts and insurance, few expensive failures. This is where you learn buying, inspecting, haggling and selling without a repair bill wiping you out.",
        "watch_for": ["Oil consumption on high-mileage four-cylinders", "Rust on Ontario cars", "Rebuilt titles priced as clean"],
        "buy_rule": "Aim to buy 12-15% under market value so tax, insurance and prep still leave you near break-even.",
        "cars": [
            {"make": "Honda", "model": "Accord", "note": "Includes V6 trims"},
            {"make": "Honda", "model": "Civic"},
            {"make": "Toyota", "model": "Corolla"},
            {"make": "Toyota", "model": "Camry"},
            {"make": "Mazda", "model": "Mazda3"},
        ],
    },
    {
        "level": 2, "name": "Reliable premium",
        "tagline": "Nicer interiors and a better drive, still dependable.",
        "why": "Premium-badged cars with Honda/Toyota-level reliability. They sell well to buyers wanting 'something nicer', with moderate parts and insurance costs.",
        "watch_for": ["Neglected maintenance on older cars", "Dash material degradation", "Automatic transmission wear at high mileage"],
        "buy_rule": "Insist on service records. Walk away from anything with unexplained gaps in maintenance.",
        "cars": [
            {"make": "Acura", "model": "TSX"},
            {"make": "Acura", "model": "ILX"},
            {"make": "Lexus", "model": "IS", "note": "IS 250 / IS 350 automatics"},
            {"make": "Lexus", "model": "ES"},
        ],
    },
    {
        "level": 3, "name": "Sport sedans & coupes",
        "tagline": "Real performance, with real insurance and tire bills.",
        "why": "V6 rear- or all-wheel-drive cars with strong enthusiast demand. They hold value well but cost more to insure, and previous owners may have driven them hard.",
        "watch_for": ["Oil consumption (VQ37 V6)", "Aftermarket modifications and tunes", "AWD service history", "Uneven or mismatched tires (hard driving)"],
        "buy_rule": "Prefer stock or lightly modified cars. Get an insurance quote for the exact VIN before you offer.",
        "cars": [
            {"make": "Infiniti", "model": "G37"},
            {"make": "Infiniti", "model": "Q50"},
            {"make": "Acura", "model": "TL"},
            {"make": "Acura", "model": "TLX"},
            {"make": "Lexus", "model": "GS"},
        ],
    },
    {
        "level": 4, "name": "Driver's cars",
        "tagline": "Fun, in demand, and expensive to insure.",
        "why": "Lightweight sporty coupes buyers actively hunt for. They resell quickly and lose little value, but young-driver insurance is high and many have been tracked or modified.",
        "watch_for": ["Track, drift and hard-driving abuse", "Valve spring recall (86 / BRZ)", "Modified or non-stock parts", "High insurance quotes"],
        "buy_rule": "Only buy documented, mostly stock cars, and only after you have a confirmed insurance quote.",
        "cars": [
            {"make": "Toyota", "model": "86"},
            {"make": "Subaru", "model": "BRZ"},
            {"make": "Nissan", "model": "370Z"},
        ],
    },
    {
        "level": 5, "name": "European performance",
        "tagline": "The highest upside and the easiest way to lose money.",
        "why": "Turbo and supercharged German cars are cheap to buy but one failure can erase the whole margin. Treat these as expert-level.",
        "watch_for": ["High-pressure fuel pump and injector failures (N54 335i)", "Water pump and thermostat housing leaks", "Dual-clutch gearbox wear (S tronic)", "Oil leaks from gaskets and seals"],
        "buy_rule": "Never buy without a specialist pre-purchase inspection, and budget a repair reserve well above the calculator's average.",
        "cars": [
            {"make": "BMW", "model": "3-Series"},
            {"make": "Audi", "model": "S4"},
            {"make": "Audi", "model": "A4"},
            {"make": "Mercedes-Benz", "model": "C-Class"},
        ],
    },
]

_LEVEL_BY_CAR = {
    (car["make"].lower(), car["model"].lower()): level["level"]
    for level in LEVELS for car in level["cars"]
}


def level_for(make, model):
    return _LEVEL_BY_CAR.get((str(make).lower(), str(model).lower()))


def compute_progress(sold):
    """`sold`: list of (level_or_None, actual_net) for sold flips. Returns
    per-level stats and which level the user is currently working on."""
    levels = []
    previous_graduated = True
    current = 1
    for level in LEVELS:
        nets = [net for lvl, net in sold if lvl == level["level"]]
        avg = round(sum(nets) / len(nets), 2) if nets else None
        graduated = len(nets) >= GRADUATE_MIN_SOLD and avg is not None and avg >= -GRADUATE_MAX_AVG_LOSS
        levels.append({
            "level": level["level"], "flips_sold": len(nets), "avg_net": avg,
            "unlocked": previous_graduated, "graduated": graduated,
        })
        if previous_graduated and not graduated:
            current = level["level"]
        previous_graduated = previous_graduated and graduated
    if all(l["graduated"] for l in levels):
        current = LEVELS[-1]["level"]
    return {
        "current_level": current, "levels": levels,
        "rule": f"Sell {GRADUATE_MIN_SOLD} flips at a level with an average result no worse than -${GRADUATE_MAX_AVG_LOSS} to graduate to the next.",
    }


def public_levels():
    return LEVELS
