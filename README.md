# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->



---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the 40 listings in `data/listings.json` by price ceiling and size, scores what is left by keyword overlap with the description, and returns the best matches. It does not call the model.
- **Inputs:** `description` (str, keywords such as "vintage graphic tee"); `size` (str | None, default None, skip size filtering); `max_price` (float | None, default None, skip price filtering, inclusive).
  - *Size match:* split the listing's `size` on whitespace, `/`, and parentheses, lowercase the pieces, and match only if every piece of the requested size is among them. So "M" matches `M`, `S/M`, and `M/L`, but not `XL` or `W30 L30`. "8" matches `US 8` but not `US 8.5`. "One Size" listings match only when the user asks for "one size".
  - *Keyword score:* lowercase `description` and split it into words. Each word scores 1 if it appears in the listing's `title`, `description`, `category`, `style_tags`, or `colors`. Listings scoring 0 are dropped.
- **Returns:** A `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10) listing dicts, highest score first, ties in file order. Each dict is the full listing record: `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`. Nothing is added or removed.
- **When it has nothing:** Returns `[]`. It never returns None, an error string, or an exception, including when the filters exclude everything.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the thrifted item, using the pieces in the user's wardrobe.
- **Inputs:** `new_item` (dict, one listing dict as returned by `search_listings`); `wardrobe` (dict, shape `{"items": [...]}`, where each item has `id`, `name`, `category`, `colors`, `style_tags`, and `notes` (str or None)).
- **Returns:** A non-empty `str` of plain text holding one or two outfit suggestions. With a non-empty wardrobe, each outfit names specific pieces the user already owns, using their `name` values. The string never starts with an error marker.
- **When it has nothing:** If `wardrobe["items"]` is empty, it does not fail. It returns general styling advice for the item, with no reference to owned pieces. It never returns `""`. If the model is unavailable, `generate.ModelUnavailable` propagates to the loop and is not swallowed here.

### `create_fit_card`

- **What it does:** Asks the model for a short social-post caption about the find, based on the item and the outfit suggestion.
- **Inputs:** `outfit` (str, the text returned by `suggest_outfit`); `new_item` (dict, the same listing dict).
- **Returns:** A `str` of two to four sentences written like a real post. It mentions the item, its `price`, and its `platform` once each. It does not require `brand`, which may be None. Repeated calls on the same input should come out differently, so `CACHE_ENABLED` and `TEMPERATURE` in `config.py` must allow variation.
- **When it has nothing:** If `outfit` is empty or whitespace-only, it makes no model call and returns the fixed message `"No outfit to write a caption for."`. It does not raise and it does not return `""`.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, set `session["error"]` to a message saying nothing matched (including the parsed description, size, and price), and stop. `suggest_outfit` and `create_fit_card` are not called. Otherwise, put the first result in `session["selected_item"]`, call `suggest_outfit` with it and the wardrobe, then call `create_fit_card` with the outfit string and the same item. An empty wardrobe is not a branch. `suggest_outfit` handles it and the loop continues as normal.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query`. A price is "under/below/less than/up to/max N" or "$N". A size is "size X" (optionally "in size X"). What is left becomes the description. It makes no model call and gives the same answer every time.

**What moves through the session:** `query`, then `parsed` (description, size, max_price), then `search_results`, then `selected_item` (the first result), then `outfit_suggestion`, then `fit_card`. `error` stays None unless the run stops early. The loop in `run_agent` runs one tool per pass, reads what came back, and chooses the next tool. Each pass calls `trace.check_iterations`. A `ModelUnavailable` from either model tool is caught and put in `session["error"]`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': ...  (output cut at 400 characters; 7 listings returned, best match lst_002 at $18, all at or under $30)
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
**Outfit 1: Casual Streetwear**
Pair the Vintage Levi's 501 Jeans with the fitted White ribbed tank top tucked in. Layer the Black cropped zip hoodie on top for a balanced silhouette, and finish the look with the Chunky white sneakers and the Black crossbody bag for an effortless, everyday vibe.

**Outfit 2: Cozy Retro Layers**
Style the Vintage Levi's 501 Jeans with the Brown leather belt. Throw on the Oversized grey crewneck sweatshirt for a relaxed, slouchy feel, and pair it with the Black combat boots for a touch of edge.
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
Vintage Levi's 501s in medium wash are the ultimate foundation for effortless style.

**Outfit 1: Casual Streetwear**
Pair the jeans with a crisp, slightly oversized white crewneck t-shirt and a classic black leather belt. Layer a distressed charcoal grey zip-up hoodie over top, and finish the look with retro white leather sneakers and a canvas tote bag.

**Outfit 2: Elevated Classic**
Tuck a fitted black ribbed tank top or a sleek bodysuit into the waistband. Add an oversized plaid blazer in neutral earth tones, a structured brown leather belt, and pointed-toe black leather boots for a sharp, timeless contrast.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; [print(create_fit_card('jeans and white sneakers', load_listings()[0])) for _ in range(3)]"
Nothing beats the effortless 90s off-duty model vibe of a truly broken-in pair of vintage Levi's 501 jeans. Just scored this dreamy medium wash on depop for $38 and I'm pairing them with crisp white sneakers and a beat-up leather jacket all fall. 🤌✨
Nothing beats the hunt for the ultimate pair of vintage Levi's 501 jeans, especially when you score them for just $38. Channeling that effortless 90s model-off-duty vibe—just add a crisp white tee and retro sneakers for the absolute easiest everyday uniform. Up now on my depop, so grab them before I change my mind and keep them!
Nothing beats that worn-in 90s slouch. Just scored these vintage Levi's 501 jeans in the perfect medium wash on depop for $38, and they are about to become my entire personality. Honestly, just add crisp white sneakers and an oversized tee for the ultimate effortlessly cool off-duty model vibe. ✨👖

$ python -c "...create_fit_card('  ', load_listings()[0])"
No outfit to write a caption for.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
