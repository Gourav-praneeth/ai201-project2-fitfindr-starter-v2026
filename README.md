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

FitFindr is a thrift-shopping agent. You describe a piece in plain language, for example "vintage graphic tee under $30" or "90s track jacket in size M", and it searches 40 secondhand listings (depop, thredUp, poshmark) filtered by size and price. It takes the best match and suggests one or two outfits that use pieces from your own wardrobe, or general styling advice if you haven't entered a wardrobe. It finishes with a short social-media caption about the find. If nothing matches, it stops and tells you what to change, such as raising your price limit, rather than guessing.

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
$ python app.py ask 'vintage graphic tee under $30'
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[2] suggest_outfit
      in:  dict with keys: item_id, wardrobe_items
      out: **Outfit 1: Y2K Streetwear** Pair the Y2K Baby Tee — Butterfly Print with the baggy straight-leg jeans, dark w…
[3] create_fit_card
      in:  dict with keys: item_id
      out: Absolute steal on Depop today—scored this Y2K butterfly print baby tee for just $18! Obsessed with the sugary-…

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit 1: Y2K Streetwear**
Pair the Y2K Baby Tee — Butterfly Print with the baggy straight-leg jeans, dark wash, sitting high above the hip to nail the 2000s silhouette. Layer the vintage black denim jacket on top for a structured edge. Finish the look with the chunky white sneakers and the black crossbody bag for an effortless everyday vibe. 

**Outfit 2: Edgy Contrast**
Tuck the Y2K Baby Tee — Butterfly Print into the wide-leg khaki trousers to balance the fitted top with relaxed earth tones. Add the black combat boots for a subtle grunge contrast against the sweet graphic print, and accessorize with the brown leather belt to tie the look together.

  Fit card: Absolute steal on Depop today—scored this Y2K butterfly print baby tee for just $18! Obsessed with the sugary-sweet graphic, especially when I contrast it with chunky black combat boots and relaxed khaki trousers for that ultimate 2000s grunge vibe. 🦋✨

1 model calls this session, 1 served from cache, 285 prompt + 60 output tokens
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
Scored these vintage Levi's 501 jeans on Depop for just $38 and I am never taking them off. The medium wash has that perfectly broken-in 90s slouch that you just can't fake. Throwing them on with crisp white sneakers for that effortlessly cool Sunday morning farmer's market vibe.
Scored these vintage Levi's 501 jeans on Depop for just $38 and I am never taking them off. The medium wash is seriously *chef's kiss* and has that perfect broken-in 90s slouch. Just threw them on with my crisp white sneakers for the ultimate effortless weekend uniform.
Can't believe I snagged these vintage Levi's 501 jeans on Depop for only $38! The medium wash is seriously unmatched for that effortless 90s off-duty vibe. Honestly, I'm never taking them off—just gonna live in these with my favorite white sneakers from here on out.

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

- *What I asked for:* Claude Code wrote `search_listings`, `suggest_outfit` and `create_fit_card` from the spec in my Tool Inventory.
- *What came back:* Working tools that matched the spec, with one problem I caught before testing: `generate()` caches identical prompts, so `create_fit_card` would have returned the same caption on repeated calls, which my fit card criterion forbids.
- *What I changed:* `create_fit_card` calls `generate(..., cache=False)`. I confirmed three runs on one item gave three different captions.

**Moment 2**

- *What I asked for:* Run the five criteria five times each and score them, then pick one improvement from the diagnosis.
- *What came back:* All five criteria met (criterion 3 unverifiable), but when the cards were read, 29 of 40 sounded like the seller ("up now on my Depop"). A first scoring pass also wrongly reported that criterion 2 failed, because the word "suggest_outfit" appeared in the branch note; checking the actual step list showed it never ran.
- *What I changed:* One prompt in `create_fit_card` so the poster is the buyer. Seller-style cards went from 29 of 40 to 0 of 40. I also added a note that the counter is a pattern list and not a reader.

**Other things worth knowing**

- Claude Code also drafted my criteria 3–5 and the "why this target" lines for all five. The brief says to write criteria yourself and use a model to attack them; I asked Claude to write them directly, so those words are not originally mine.
- I only had a Gemini key. Claude first added a Groq provider to `generate.py`, found the default model wasn't available on my account, and then removed the whole Groq change when I said I would use Gemini.
- Claude wrote the loop, the MCP registration and the README logs. The run logs are real output from `run_eval.py`, in `results/`.

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
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Same item reaches every tool | 5 of 5 | n/m | n/m | n/m | n/m | n/m | NOT MEASURABLE (ids hidden in trace) |
| 4. Fit cards for 5 items (each Try = the 5 items' cards from that try) | each set: ≥4 of 5 cards pass; no shared opener | PASS | PASS | PASS | PASS | PASS | MET (5/5 sets) |
| 5. Empty wardrobe completes | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| _Diagnostic, not one of the five: fit cards that read as a seller's post_ | none wanted |  |  |  |  |  | **29 of 40 cards** |

`n/m` = not measurable: in this run the trace printed `item_id` as "dict with keys: …", so there was nothing to compare. Marking those PASS (as I first did) overstated what the log showed. Criterion 4 is scored per set: Try k is the five cards produced in try k for five different items (graphic tee, track jacket, platform sneakers, slip dress, denim jacket).

Source: `results/run_2026-10-25_2212_before.md`, scored by a script that reads the file. The checks for sentence count, price and platform are string checks, so I hand-checked any card the script failed: one price written as "thirty bucks" counts, and a card with no sentence-ending punctuation counts as one sentence.

**Real output from one try** — `run_eval.py` calling `agent.py::run_agent`, whose last step is `tools.py::create_fit_card`. Query: `vintage graphic tee under $30`, example wardrobe.

```
selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)

outfit_suggestion:
**Outfit 1: Y2K Streetwear Contrast**
Pair the Y2K Baby Tee — Butterfly Print with the baggy straight-leg jeans, dark wash for a classic early 2000s silhouette. Cinch the waist with the brown leather belt, and layer the vintage black denim jacket on top. Finish the look with the chunky white sneakers and the black crossbody bag for an effortless everyday vibe.

**Outfit 2: Casual Edgy Mix**
Combine the Y2K Baby Tee — Butterfly Print with the wide-leg khaki trousers to blend cottagecore and earth-tone aesthetics. Throw on the black cropped zip hoodie for easy layering, and step into the black combat boots to add a touch of grunge edge.

fit_card:
Found this absolute gem of a butterfly print Y2K baby tee and I am obsessed. Snag it on my Depop right now for just $18 before I change my mind and keep it for myself. Style it with baggy denim and chunky sneakers for the ultimate nostalgic street vibe, or grunge it up with combat boots.
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
| 1 | Matching query completes all three tools | 4 of 5 | MET (5/5) in all three logs | `session["error"]` None and `fit_card` non-empty in every try of 'vintage graphic tee under $30'. |
| 2 | Impossible query stops before the second tool | 5 of 5 | MET (5/5) in all three logs | Every trace has only `search_listings` then `branch`, and the error text names what to change; `fit_card` is None. |
| 3 | Same item reaches every tool | 5 of 5 | Before/after: NOT MEASURABLE. Final: MET (5/5) | The first two logs hid `item_id`, so I could not compare ids. After the trace printed ids, all five tries showed one id at all three steps. |
| 4 | Fit cards for 5 items | each set: ≥4 of 5 cards pass, no shared opener | Before: MET (5/5 sets). After: MISSED once (4/5 sets). Final: MET (5/5 sets) | Per try, I counted cards with 2–4 sentences, the price and the platform, and checked the five first sentences were different. In the after log, try 2 had two cards opening "Score!". |
| 5 | Empty wardrobe completes | 5 of 5 | MET (5/5) in all three logs | Non-empty outfit and card, and no wardrobe piece named, in every try. |

My first write-up scored criterion 4 on try 1 only and said "5/5". Scoring all five tries is what exposed the try-2 miss.

**Diagnoses**

*No criterion was missed on its own terms, and that is itself a finding: my criteria were too easy to miss in one respect.* Every one of my five passed, yet 29 of 40 fit cards in the before run read as a *seller's* post: "Snag it on my Depop right now for just $18 before I change my mind", "up now on my depop", "I just listed". The user is buying the item, so those captions are wrong for the product. None of my criteria asked whether the caption has the right point of view, so they could not see it.

- **Where:** the model's output, in `tools.py::create_fit_card`. The tool ran correctly and the loop passed the right item.
- **Mechanism:** the prompt gave the model `Price: $18` and `Platform: depop` as bare fields and said only "a thrift find". Price plus platform is the shape of a listing, so the model wrote the caption as the person who posted it. The prompt never said who the poster is.
- **Criterion 3:** the loop does pass the right item (the outfit names it every time), but I cannot prove it from the trace, because `trace._short` collapses a dict without a `title` into its key names. That is a gap in my measurement, not a failure I can show in the tool.

**The one criterion miss — criterion 4, after run, try 2.**
- **Where:** the model's output from `tools.py::create_fit_card`. The tool ran correctly and the loop passed different items.
- **Mechanism:** the prompt says nothing about varying how a caption begins, and "like a real post" pulls the model toward a few templates ("Score!", "Just scored this…", "Found the ultimate…"). Temperature is 0.9, so each card draws one of those openers more or less at random. With five cards in a set, two draws of "Score!" sometimes collide, and in try 2 items B and E did.
- **Not caused by the prompt rewrite, as far as I can tell.** Before the rewrite "Found the ultimate" opened 9 of 40 cards; afterwards the most common opener ("Just scored this") opened 5 of 40. The earlier run was more repetitive and just never collided inside one set. One collision in 5 sets is too few to say the rewrite changed the rate.

**Target set too low, and the tighter one.** Criterion 4 only forbids shared openers *within a set of five items*, and it never asks whether the caption is in the right voice. Both gaps let bad output pass. A tighter version: *"In 5 of 5 sets of 5 cards, 0 of 5 read as the seller, and no 3-word opening phrase appears in more than 2 of the 25 cards."* I scored the opener half of it on the 25 criterion-4 cards in each log: the most common 3-word opener appears in 5 cards (before, "Found the ultimate"), 4 cards (after, "Score!") and 4 cards (final, "Just scored this"). The limit is 2, so the tighter target is missed in all three logs, which is what I would want from a target that was too low before. The seller-voice half is met in the after and final logs (0 of 40) and missed in the before log (29 of 40). I added it as a revision under criterion 4 in `criteria.md`, without editing the original.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path** (`python app.py ask 'vintage graphic tee under $30' --trace`)

```
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[2] suggest_outfit
      in:  dict with keys: item_id, wardrobe_items
      out: **Outfit 1: Y2K Streetwear** Pair the Y2K Baby Tee — Butterfly Print with the baggy straight-leg jeans, dark w…
[3] create_fit_card
      in:  dict with keys: item_id
      out: Found the absolute cutest Y2K baby tee with the dreamiest butterfly print on Depop for just $18! I’m already p…
```

**Empty search** (`python app.py ask 'designer ballgown size XXS under $5' --trace`)

```
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[2] branch
      →    search returned [] — stopping before suggest_outfit

  Nothing matched 'designer ballgown', size XXS, under $5. To get results, use fewer or more general keywords, or try a different size or leave size out, or raise your price limit.

0 model calls this session
```

The empty trace has two steps and the happy one has three, and the empty run made 0 model calls.

**On the MCP move:** `search_listings` is registered as a tool in `mcp_server.py`, with a description that states units, the size-matching rule and the empty case. In `agent.py::run_agent` the direct call became `call_tool("search_listings", {...})` from `mcp_client.py`, and the trace step is named `search_listings (via MCP)`. The return value did not change: for six queries (including `designer ballgown`, size XXS, under $5) the direct and MCP results were equal as Python values (`direct == via`), and the empty case came back as `[]`, not `None`, so the branch still fires. Behaviour that did change: each call now starts and stops a server process, so a search is slower. I did not time it. **The two run logs above were both recorded before this move, with the direct call.** I checked the MCP path with the traces here and the six-query comparison, but did not rerun `run_eval.py` after it.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** one prompt, in `tools.py::create_fit_card`. It now says the poster is "a shopper who just BOUGHT this secondhand find", labels the fields `Price paid` and `Bought on`, and says the poster is the buyer, not the seller: never say they listed it or that it is on "my" shop, page or closet, and never tell readers to grab it. Nothing else changed between the two runs: same loop, same search, same temperature (0.9), same scenarios.

**Which failure it was meant to fix:** the seller's-post framing in the model's output (29 of 40 cards before).

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Same item reaches every tool | 5 of 5 | n/m | n/m | n/m | n/m | n/m | NOT MEASURABLE (ids hidden in trace) |
| 4. Fit cards for 5 items (each Try = the 5 items' cards from that try) | each set: ≥4 of 5 cards pass; no shared opener | PASS | FAIL | PASS | PASS | PASS | MISSED once (4/5 sets) |
| 5. Empty wardrobe completes | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| _Diagnostic, not one of the five: fit cards that read as a seller's post_ | none wanted |  |  |  |  |  | **0 of 40 cards** |

Source: `results/run_2026-10-25_2218_after.md`. Try 2 failed criterion 4: items B (track jacket) and E (denim jacket) both opened with "Score!".

**Did it help, and how do I know:** It fixed the problem it targeted and did not clearly change anything else. Seller-framed cards went from 29 of 40 to 0 of 40, counted with the same pattern list on the same 40 cards (8 scenarios that reach the fit card, 5 tries each); a caption now reads "Finally scored this Y2K butterfly print baby tee on Depop for just $18 and I am obsessed" where before it said "Snag it on my Depop right now". The five criteria did not improve, because they were already met. One of them, criterion 4, scored one miss in the after run (4 of 5 sets), which I traced to opener collisions rather than to the rewrite (see Diagnoses). The rerun on the final code went back to 5 of 5 sets, which also tells me that miss is run-to-run noise, not a regression I can pin on the change.

What I can't claim:
- **My counter is a pattern list, not a reader.** It could miss a seller-sounding caption phrased in a way I didn't list. I read a sample by hand and found none, but 0 of 40 means "none matched my patterns".
- **It measures the model, which varies.** One run of 40 cards each side is enough to see 72% going to 0%, but it is not a precise rate.
- **No regression that I found.** Sentence counts stayed at 24 of 25 in range both times. The one short card was two sentences my splitter missed, and the one card my price check failed wrote "thirty bucks", so the price was there.
- **It did not touch the repeated openers.** Across the 40 cards, several still share a first few words ("Still pinching myself" 4 times, "Score!" 3 times), which my criterion 4 only forbids across five different items.



### Run Log — Final (rerun on the finished code)

Rerun after the MCP move and after the trace was changed to print item ids. Same scenarios and scorer, nothing else changed since the "after" run.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Same item reaches every tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit cards for 5 items (each Try = the 5 items' cards from that try) | each set: ≥4 of 5 cards pass; no shared opener | PASS | PASS | PASS | PASS | PASS | MET (5/5 sets) |
| 5. Empty wardrobe completes | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| _Diagnostic, not one of the five: fit cards that read as a seller's post_ | none wanted |  |  |  |  |  | **0 of 40 cards** |

Source: `results/run_2026-10-25_2248_final.md`. Criterion 3 is now measured: in all five tries the id printed after `search_listings (via MCP)` ("first result id: lst_004") equals the `item_id` printed in the `suggest_outfit` step and in the `create_fit_card` step.

---

## What's Still Broken

- **Criterion 3 was unmeasurable in two of the three logs.** The before and after logs predate the trace change, so their criterion 3 cells are `n/m`. The final log measures it (5 of 5). I did not rerun the before and after logs, because rerunning would change their meaning.
- **My criteria don't test point of view.** Criterion 4 passed a set of cards that were wrong for the user. I wrote the tighter target (0 of 5 seller-voice, no opener in more than 2 of 25 cards) as a revision under criterion 4, but I scored it afterwards: the opener rule is missed in all three logs (top opener in 5, 4 and 4 of 25 cards, limit 2), so openers are still too repetitive and I have not fixed that.
- **Repeated openers.** Across the 40 after-run cards, a few captions still open with the same words (see above). I'd raise the variety in the prompt, but didn't, to keep this to one change.
- **The empty-search message is generic.** It names the description, size and price that were searched and suggests loosening each one that was set, but it can't say *which* of them caused the miss. I haven't tested whether users find it useful.
- **Failure modes.** Empty search and empty wardrobe are covered by criteria 2 and 5. For the model being unavailable I set a wrong key for one command (`GEMINI_API_KEY=not-a-real-key python app.py ask ... --trace`, `.env` untouched). The run stopped with "The model rejected your API key…" and no stack trace. One caveat: `suggest_outfit` still ran at step 2 because its prompt was already cached, so the failure appeared at step 3 (`create_fit_card`, which bypasses the cache). I only triggered the bad key once, for `GEMINI_API_KEY`, and not a network failure or a missing model name.
- **Before/after logs predate the MCP move; the final log doesn't.** The one-change comparison (before vs after) was run with a direct `search_listings` call. The final log runs on MCP and shows no criterion changing.

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
