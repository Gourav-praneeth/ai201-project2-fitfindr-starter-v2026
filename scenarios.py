"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Criterion 3 — state. Checked from the trace: the item_id passed to
        # suggest_outfit and create_fit_card must equal the first search result.
        "name": "state: same item reaches every tool",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 3,
    },
    # Criterion 4 — fit card across five different items. One scenario per
    # item; try 1 of each is the five cards the criterion scores.
    {"name": "fit card item A: graphic tee", "query": "vintage graphic tee under $30",
     "wardrobe": "example", "criterion": 4},
    {"name": "fit card item B: track jacket", "query": "90s track jacket in size M",
     "wardrobe": "example", "criterion": 4},
    {"name": "fit card item C: platform sneakers", "query": "platform sneakers size 8",
     "wardrobe": "example", "criterion": 4},
    {"name": "fit card item D: slip dress", "query": "silk slip dress in midi length under $40",
     "wardrobe": "example", "criterion": 4},
    {"name": "fit card item E: denim jacket", "query": "denim jacket under $50",
     "wardrobe": "example", "criterion": 4},
    {
        # Criterion 5 — empty wardrobe still completes with a fit card.
        "name": "empty wardrobe completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "empty",
        "criterion": 5,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
