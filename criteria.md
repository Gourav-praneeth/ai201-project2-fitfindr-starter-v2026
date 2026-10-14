# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
Not 5 of 5, because two things in this path are outside my control. `search_listings` is a literal keyword match, so a phrasing like "t-shirt" won't hit a listing tagged "tee", and my query parser can misread a size or price. Two model calls also sit in the path, and either can fail or time out. Not 3 of 5, because for the queries from `python app.py examples` the keywords appear in the data, so a miss would mean a bug and not bad luck.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
5 of 5 because this path never calls the model. A query with nothing in the data makes `search_listings` return `[]`, and the loop's branch is a plain `if not results`, so the outcome is the same every time. The only variable is the message, and I build that from the parsed description, size and price, so it can always name what to change. One miss would mean the branch is wrong, not that I got unlucky.

---

## 3. Something about state

In 5 of 5 successful runs, `session["selected_item"]["id"]` equals the `id` of the item passed into `suggest_outfit` and into `create_fit_card`, and equals `session["search_results"][0]["id"]`. I check this by logging the `id` at each of the three points (the trace step or a print) and comparing them by eye or with an assert.

**Why this target:**
5 of 5, because this is pure bookkeeping with no model or randomness involved. If the `id` ever differs, the loop is passing the wrong variable. The `id` is the right thing to compare because a listing's title or price can look plausible for the wrong item, but two different items never share an `id`. It's the first check to run when a fit card describes the wrong item.



---

## 4. Something about the fit card

Across 5 fit cards generated for 5 different items, at least 4 of 5 must (a) be 2 to 4 sentences, (b) contain the item's price as it appears in the listing, and (c) name the platform. No two of the 5 may share the same first sentence. Word-for-word differences between runs on the same item are acceptable and expected.

**Why this target:**
The wording can vary, but the facts can't. A caption missing the price or platform fails the spec for the tool, and those are easy to count with a string check. I'm allowing 1 miss of 5 because the model can phrase a price differently, for example "$18" and "18 bucks", and I don't want to fail a good caption on formatting. I'm requiring zero shared opening sentences because that is the visible symptom of a cache hit or temperature 0, both set in `config.py`, and I can check it exactly.



---

## 5. Your choice

With an empty wardrobe, the agent still completes all three tools and returns a non-empty fit card in 5 of 5 tries. Over those 5 runs, `suggest_outfit` must not return an empty string and must not name any wardrobe piece, since the wardrobe has none.

**Why this target:**
5 of 5, because the empty wardrobe is a case I decided in the spec: `suggest_outfit` switches to general styling advice, and the loop does not treat it as a branch. It's the case a first-time user hits before they've entered any clothes, so it can't be flaky. The one thing that could still fail is the model returning an empty reply, which is why I check for non-empty output and don't just check that the call ran.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
