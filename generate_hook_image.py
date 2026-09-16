"""ChapterSnap — generate a "hook" image for each chapter of a book.

For each chapter, finds the single most gripping moment — the one meant to make
a reader feel they CANNOT stop reading — and renders it.

Character consistency comes from two anchors, not from chaining alone:
  1. A per-book character bible (see character_bible.py): one locked identity
     and one neutral studio portrait per recurring character, reused verbatim
     by every chapter. This stops both the text descriptions and the faces
     from drifting as the book goes on. Each batch is scanned for new cast
     before it is rendered, and a portrait is only paid for when a character
     first actually appears in a frame.
  2. The previous chapter's image, which carries the color grade forward.
     Wardrobe and location come from the chapter itself, not from this.
Both are attached to each chapter's image call.

Standalone project: depends only on its own llm_client/, prompts/, chapters.py
and its own input/.env/output. Uses the raw `openai` SDK, not langchain.

Reads:  input/<book_id>/<chapter_no>.md
Writes: output/<book_id>/characters.xml           (cast bible)
        output/<book_id>/characters/<id>[@age].png (anchor portraits, one per
            age the book needs a character at)
        output/<book_id>/chapterimg/<chapter>.png (chapter images)
        output/<book_id>/image_positions.md       (one table for the whole
            book: which paragraph each chapter's image goes before)

Nothing is written to disk as a handoff between steps — the moment description
flows straight from the text call into the image call in memory. The only file
read back in is the previous chapter's image (it's an upload, and it's what
makes a run resumable).

Usage:
    python generate_hook_image.py <book_id> [--chapter N] [--force] [--rebuild-bible]
"""

import argparse
import re
from pathlib import Path

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env")

from chapters import (  # noqa: E402
    OUTPUT_DIR,
    list_chapter_numbers,
    numbered_paragraphs,
    read_chapter_text,
    split_paragraphs,
)
from character_bible import (  # noqa: E402
    age_at_chapter,
    anchor_for_age,
    backfill_identity_facts,
    clean_field,
    detect_time_skips,
    ensure_anchors,
    extend_bible,
    load_bible,
    load_skips,
    normalise_gender,
    promote_characters,
    save_bible,
)
from llm_client.images import (  # noqa: E402
    CHAPTER_IMAGE_MODEL,
    ImageBlockedError,
    render_image,
)
from llm_client.tfy_client import get_tfy_client  # noqa: E402
from prompts.image_prompt import (  # noqa: E402
    CANDID_VIEWPOINT,
    CONSISTENCY_IMAGE_SYSTEM_PROMPT,
    FIRST_IMAGE_SYSTEM_PROMPT,
    PHOTOREAL_LEAD,
    SAFETY_OVERRIDE_RETRY_ADDENDUM,
    SCENE_REALISM,
)
from prompts.moment_prompt import (  # noqa: E402
    DEFUSED_RETRY_ADDENDUM,
    MOMENT_SYSTEM_PROMPT,
    build_roster_block,
)

TEXT_MODEL = "google-vertex/google-gemini-3.1-flash-lite"


def _block(raw: str, label: str, stop_labels: tuple[str, ...]) -> str:
    """Pull one labelled section out of the model's response, stopping at the
    next known label so multi-line sections stay intact."""
    stop = "|".join(stop_labels)
    match = re.search(rf"{label}:\s*(.*?)(?=\n(?:{stop}):|\Z)", raw, re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_new_characters(block: str) -> list[dict]:
    """Parse `id | Name | identity | default outfit` lines from NEW_CHARACTERS."""
    if not block or block.strip().upper() == "NONE":
        return []
    found = []
    for line in block.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3 or not parts[0] or parts[0].upper() == "NONE":
            continue
        # Skip the format-example line echoed back by a confused model.
        if parts[0].startswith("<"):
            continue
        # Six fields since gender and age became their own columns; the
        # four-field form is still accepted so a model that falls back to the
        # old shape yields a usable character instead of a discarded line.
        if len(parts) >= 6 and parts[3].strip().isdigit():
            gender, age, identity, outfit = parts[2], parts[3], parts[4], parts[5]
        else:
            gender, age = "", ""
            identity = parts[2]
            outfit = parts[3] if len(parts) > 3 else ""
        found.append({
            "id": re.sub(r"[^a-z0-9_]", "", parts[0].lower()),
            "name": parts[1],
            "gender": normalise_gender(gender),
            "age": age.strip(),
            "identity": clean_field(identity),
            "default_outfit": clean_field(outfit),
        })
    return [c for c in found if c["id"] and c["identity"]]


def find_moment(
    paragraphs: list[str],
    characters: list[dict],
    book_id: str = "",
    chapter_no: int | None = None,
    defused: bool = False,
) -> dict:
    """Locate the chapter's peak moment. Returns the paragraph to insert after,
    which roster characters are present, and what is happening.

    `defused` re-briefs the same moment with the act taken out of it. It is
    only used after the image model has already refused the faithful brief,
    because a defused brief is what produces a frame of two people standing
    quietly where the chapter had someone being seized.
    """
    response = get_tfy_client({
        "book_id": str(book_id),
        "chapter_no": str(chapter_no),
        "stage": "find_moment_defused" if defused else "find_moment",
    }).chat.completions.create(
        model=TEXT_MODEL,
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": MOMENT_SYSTEM_PROMPT + (
                    DEFUSED_RETRY_ADDENDUM if defused else ""
                ),
            },
            {
                "role": "user",
                "content": f"{build_roster_block(characters)}\n\n=== CHAPTER ===\n{numbered_paragraphs(paragraphs)}",
            },
        ],
    )
    raw = (response.choices[0].message.content or "").strip()

    # Tolerate "[62]" as well as "62" — the model sometimes echoes the bracket
    # markers it was shown, and a miss here silently misplaces the image.
    para_match = re.search(r"PARAGRAPH:\s*\[?\s*(\d+)", raw)
    paragraph_index = int(para_match.group(1)) if para_match else len(paragraphs)
    paragraph_index = max(1, min(paragraph_index, len(paragraphs)))
    if not para_match:
        print(f"WARNING: couldn't parse PARAGRAPH, defaulting to last paragraph:\n{raw!r}")

    labels = (
        "CHARACTERS", "NEW_CHARACTERS", "MINOR_PRESENT", "WARDROBE",
        "EVENT_DESCRIPTION",
    )

    known_ids = {c["id"] for c in characters}
    roster_block = _block(raw, "CHARACTERS", labels)
    present_ids = [
        cid for cid in (s.strip().lower() for s in roster_block.split(","))
        if cid in known_ids
    ]

    new_characters = _parse_new_characters(_block(raw, "NEW_CHARACTERS", labels))

    minor = _block(raw, "MINOR_PRESENT", labels)
    if minor.upper() == "NONE":
        minor = ""

    wardrobe = _block(raw, "WARDROBE", labels)
    if wardrobe.upper().replace(" ", "") in {"NOTSPECIFIED", "NONE", ""}:
        wardrobe = ""

    event_description = _block(raw, "EVENT_DESCRIPTION", labels)
    if not event_description:
        print(f"WARNING: couldn't parse EVENT_DESCRIPTION cleanly:\n{raw!r}")
        event_description = raw

    return {
        "paragraph_index": paragraph_index,
        "present_ids": present_ids,
        "new_characters": new_characters,
        "minor_present": minor,
        "wardrobe": wardrobe,
        "event_description": event_description,
    }


def action_lines(event_description: str) -> str:
    """The ACTION lines on their own.

    They are the one part of the brief that says what is actually happening,
    and they sit in the middle of a prompt whose fixed style, realism and
    viewpoint blocks run to ~1,600 tokens. Restating them last puts them in
    the other position the model weights heavily, so the pose survives the
    boilerplate around it.
    """
    lines = [
        line.strip() for line in event_description.splitlines()
        if line.strip().upper().startswith("ACTION")
    ]
    return "\n".join(lines)


def describe_gender_age(character: dict, age: str = "") -> str:
    """'a woman, age 48', 'a boy, age 10' — stated before the face description.

    Buried in the middle of an identity paragraph these two facts lose out to
    the dozen appearance details around them and to the attached portrait, and
    the renderer settles everyone at a generic young adult.

    The noun has to follow the age, not the bible: gender is recorded once for
    the whole book, so a character the timeline has aged back down to ten was
    being described as "a man, age 10", which reads as a contradiction and
    hands the renderer an adult.
    """
    gender = character.get("gender") or "person"
    age = age or character.get("age")
    if str(age).isdigit() and int(age) < 18:
        gender = {"man": "boy", "woman": "girl"}.get(gender, "child")
    return f"a {gender}, age {age}" if age else f"a {gender}"


def cast_facts(
    characters: list[dict], present_ids: list[str], ages: dict[str, str] | None = None
) -> str:
    """One flat line of who is what age, for the tail of the image prompt."""
    by_id = {c["id"]: c for c in characters}
    ages = ages or {}
    return " ".join(
        f"{c['name']} is {describe_gender_age(c, ages.get(cid, ''))}."
        for cid in present_ids
        if (c := by_id.get(cid)) and (c.get("gender") or ages.get(cid) or c.get("age"))
    )


def build_character_block(
    characters: list[dict],
    present_ids: list[str],
    minor: str,
    ages: dict[str, str] | None = None,
) -> str:
    """Who is in frame — identity only, taken from the bible verbatim so it
    can't drift. What they're wearing is handled separately."""
    by_id = {c["id"]: c for c in characters}
    ages = ages or {}
    lines = [
        f"[{c['id'].upper()}] {c['name']} — {describe_gender_age(c, ages.get(cid, ''))}: {c['identity']}"
        for cid in present_ids
        if (c := by_id.get(cid))
    ]
    if minor:
        lines.append(f"Also in frame (unnamed background, no detail needed): {minor}")
    if lines:
        # Stated as a rule as well as in each description: without it the
        # renderer settles everyone at a generic mid-twenties regardless of
        # the age the roster gives them.
        lines.append(
            "Render each person as exactly the gender and age given above — "
            "an age is a face, not a label, so give it the skin, jawline, "
            "hairline, grey and eye-area lines of those years."
        )
    return "\n".join(lines) if lines else "No named cast members in frame."


def build_wardrobe_block(
    characters: list[dict], present_ids: list[str], scene_wardrobe: str
) -> str:
    """What everyone wears in THIS scene. The chapter's own description wins;
    each character's default outfit is only the fallback when the scene gives
    no reason to think they've changed."""
    if scene_wardrobe:
        return scene_wardrobe

    by_id = {c["id"]: c for c in characters}
    lines = [
        f"{c['name']}: {c['default_outfit']}"
        for cid in present_ids
        if (c := by_id.get(cid)) and c.get("default_outfit")
    ]
    return "\n".join(lines) if lines else "Dress appropriately for the scene described."


def generate_chapter_image(
    character_block: str,
    wardrobe_block: str,
    event_description: str,
    cast_facts_line: str,
    references: list[Path],
    reference_labels: list[str],
    is_first: bool,
    safety_override: bool = False,
    metadata: dict | None = None,
) -> bytes:
    """Assemble the image prompt.

    The scene goes FIRST and the technical/style block last: what to depict is
    what most needs the model's attention, and burying it under a long style
    preamble costs staging accuracy.

    Attachments are named in order, because several look-alike studio portraits
    otherwise arrive with nothing to say whose face is whose, leaving the model
    to guess which reference belongs to which person named in the brief.
    """
    manifest = "\n".join(
        f"  Image {i}: {label}" for i, label in enumerate(reference_labels, start=1)
    )
    # The cast block leads. Face fidelity is the one thing a viewer notices
    # instantly across a whole book, and when this sat after the scene the
    # renderer drifted the faces despite the portraits being attached.
    prompt = f"{PHOTOREAL_LEAD}\n\n"
    if manifest:
        prompt += (
            "CAST — these people are already cast, and their attached "
            "photographs are the authority on how they look:\n"
            f"{manifest}\n"
            "Reproduce each attached face feature by feature: the same bone "
            "structure, face width and length, eye shape, colour and spacing, "
            "nose, mouth, jawline, brow, hairline, hair and skin tone. The "
            "person in the finished frame must be recognisably that same "
            "individual, simply caught here in the middle of something "
            "instead of sitting for a portrait — the face is the same face, "
            "but the head angle, expression and lighting all come from this "
            "scene, not from the studio shot.\n\n"
        )
    prompt += (
        "RENDER THIS EXACT MOMENT. Every line below is a specific instruction "
        "— the place, the objects and where each one sits, and each person's "
        "position, pose, hands, gaze and expression. Depict all of it "
        "faithfully rather than approximating the general idea.\n\n"
        f"{event_description}\n\n"
        f"{CANDID_VIEWPOINT}\n\n"
        f"PEOPLE IN FRAME (the attached photograph of each person governs their "
        f"face; this text only helps you tell them apart):\n"
        f"{character_block}\n\n"
        f"WEARING:\n{wardrobe_block}\n\n"
        f"{SCENE_REALISM}\n"
    )
    if safety_override:
        prompt += f"\n{SAFETY_OVERRIDE_RETRY_ADDENDUM}\n"

    system_prompt = FIRST_IMAGE_SYSTEM_PROMPT if is_first else CONSISTENCY_IMAGE_SYSTEM_PROMPT

    # Genuinely last, after the style block — the two things that kept coming
    # back wrong, named once each. Not a restatement of the ACTION lines: this
    # prompt forbids duplicated limbs a few paragraphs up, and feeding the same
    # pose in twice is how that happens.
    checks = []
    if cast_facts_line:
        checks.append(f"- {cast_facts_line}")
    if action_lines(event_description):
        checks.append("- Every ACTION line above is physically happening in the frame.")
    closing = "\n\nBEFORE ANYTHING ELSE:\n" + "\n".join(checks) if checks else ""

    return render_image(
        CHAPTER_IMAGE_MODEL,
        f"{prompt}\n{system_prompt}{closing}",
        references,
        metadata,
        upscale=True,
    )


def chapter_image_path(book_id: str, chapter_no: int) -> Path:
    return OUTPUT_DIR / book_id / "chapterimg" / f"{chapter_no}.png"


def positions_path(book_id: str) -> Path:
    return OUTPUT_DIR / book_id / "image_positions.md"


_POSITIONS_HEADER = (
    "# Image insertion positions — book {book_id}\n"
    "\n"
    "Place each chapter's image immediately **before** the paragraph listed below —\n"
    "find the paragraph that starts with the quoted line and put the image above it.\n"
    "Paragraphs are counted non-empty, excluding the `# N.` heading line.\n"
    "\n"
    "| Chapter | Insert before ¶ | That paragraph starts with… |\n"
    "|--------:|----------------:|-----------------------------|"
)


def _cell(text: str, limit: int = 100) -> str:
    """Flatten a paragraph's opening into one table cell."""
    flat = " ".join(text.split())
    if len(flat) > limit:
        flat = flat[:limit] + "…"
    return flat.replace("|", "\\|")


def _opening_preview(paragraphs: list[str], index: int) -> str:
    """Locator text for paragraph `index` (1-based). Some paragraphs are just
    separators ("........"), which are useless for finding the spot by eye, so
    those also show the next paragraph that actually has words."""
    paragraph = paragraphs[index - 1]
    if re.search(r"\w", paragraph):
        return _cell(paragraph)
    for following in paragraphs[index:]:
        if re.search(r"\w", following):
            return f"{_cell(paragraph, 24)} — then: {_cell(following, 74)}"
    return _cell(paragraph)


def record_position(
    book_id: str, chapter_no: int, after_index: int, paragraphs: list[str]
) -> None:
    """Upsert this chapter's row, keeping the file sorted by chapter. Existing
    rows are carried through untouched, so re-running one chapter or a batch
    never loses the rest.

    `after_index` is the peak-moment paragraph; the image goes just past it,
    which is reported here as "before the next paragraph" so it can be located
    by reading forward to that paragraph's opening line.
    """
    before_index = after_index + 1
    if before_index > len(paragraphs):
        # Peak moment is the final paragraph, so there's nothing to sit before.
        position, opening = "end", "*(end of chapter — place after the final paragraph)*"
    else:
        position, opening = str(before_index), _opening_preview(paragraphs, before_index)

    path = positions_path(book_id)
    rows: dict[int, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|"):
                continue
            first = line.split("|")[1].strip()
            if first.isdigit():
                rows[int(first)] = line

    rows[chapter_no] = f"| {chapter_no} | {position} | {opening} |"

    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(rows[k] for k in sorted(rows))
    path.write_text(
        f"{_POSITIONS_HEADER.format(book_id=book_id)}\n{body}\n", encoding="utf-8"
    )


def latest_image_before(book_id: str, chapter_no: int, all_chapters: list[int]) -> Path | None:
    """Most recent already-rendered chapter image before `chapter_no`, so a
    single-chapter run still inherits wardrobe/grade continuity instead of
    starting cold."""
    for n in sorted((c for c in all_chapters if c < chapter_no), reverse=True):
        path = chapter_image_path(book_id, n)
        if path.exists():
            return path
    return None


def process_chapter(
    book_id: str,
    chapter_no: int,
    characters: list[dict],
    previous_image_path: Path | None,
    skips: list[tuple[int, int]] | None = None,
) -> Path | None:
    """Returns the generated image path, or None if it stayed blocked by the
    safety filter even after the override retry (chapter skipped, run goes on)."""
    image_path = chapter_image_path(book_id, chapter_no)
    image_path.parent.mkdir(parents=True, exist_ok=True)

    skips = skips or []
    paragraphs = split_paragraphs(read_chapter_text(book_id, chapter_no))
    print(f"[{book_id}/{chapter_no}] Finding the peak moment...")
    moment = find_moment(paragraphs, characters, book_id, chapter_no)

    # Characters introduced mid-book get promoted into the bible with their own
    # anchor portrait, so they're locked from their first appearance onward
    # rather than being re-described every chapter.
    if moment["new_characters"]:
        promote_characters(book_id, characters, moment["new_characters"], chapter_no)
        known_ids = {c["id"] for c in characters}
        for candidate in moment["new_characters"]:
            if candidate["id"] in known_ids and candidate["id"] not in moment["present_ids"]:
                moment["present_ids"].append(candidate["id"])

    # Everyone's age in THIS chapter, which is their recorded age plus any
    # years the story has jumped since they were introduced.
    by_id = {c["id"]: c for c in characters}
    ages = {
        cid: age_at_chapter(by_id[cid], chapter_no, skips)
        for cid in moment["present_ids"]
        if cid in by_id
    }
    character_block = build_character_block(
        characters, moment["present_ids"], moment["minor_present"], ages
    )
    wardrobe_block = build_wardrobe_block(
        characters, moment["present_ids"], moment["wardrobe"]
    )

    # Portraits are rendered here, on first actual use, rather than when a
    # character joins the bible — plenty of cast never make it into a frame.
    if ensure_anchors(book_id, characters, moment["present_ids"], chapter_no, skips):
        save_bible(book_id, characters)

    # Identity anchors first, then the previous scene for grade carry-over.
    references: list[Path] = []
    reference_labels: list[str] = []
    for cid in moment["present_ids"]:
        character = by_id.get(cid)
        if not character:
            continue
        found = anchor_for_age(book_id, character, ages.get(cid, ""))
        if not found:
            continue
        portrait_age, path = found
        name = character["name"]
        references.append(path)
        reference_labels.append(
            f"studio portrait of {name} at age {portrait_age} — copy this face "
            f"exactly onto the person named {name} in the scene above"
        )
    if previous_image_path is not None:
        references.append(previous_image_path)
        reference_labels.append(
            "the previous chapter's frame — match its colour grade and film look "
            "only, not its location, clothing, poses or action"
        )

    image_metadata = {
        "book_id": str(book_id),
        "chapter_no": str(chapter_no),
        "stage": "chapter_image",
    }
    cast = ", ".join(moment["present_ids"]) or "none"
    print(f"[{book_id}/{chapter_no}] Rendering (cast: {cast}, {len(references)} reference image(s))...")
    def render(description: str, safety_override: bool) -> bytes:
        return generate_chapter_image(
            character_block, wardrobe_block, description,
            cast_facts(characters, moment["present_ids"], ages),
            references, reference_labels,
            is_first=previous_image_path is None,
            safety_override=safety_override,
            metadata={**image_metadata, "safety_override": str(safety_override).lower()},
        )

    try:
        image_bytes = render(moment["event_description"], safety_override=False)
    except ImageBlockedError:
        print(f"[{book_id}/{chapter_no}] Blocked by safety filter — retrying with safety override...")
        try:
            image_bytes = render(moment["event_description"], safety_override=True)
        except ImageBlockedError:
            # Last resort: re-brief the same moment with the act taken out of
            # it. Costs one extra text call, and only on chapters that have
            # already been refused twice — which is the point, since this is
            # the step that flattens the action.
            print(f"[{book_id}/{chapter_no}] Still blocked — re-briefing the moment without the act...")
            defused = find_moment(paragraphs, characters, book_id, chapter_no, defused=True)
            try:
                image_bytes = render(defused["event_description"], safety_override=True)
            except ImageBlockedError as e:
                print(f"[{book_id}/{chapter_no}] SKIPPED — still blocked after re-brief: {e}")
                return None

    image_path.write_bytes(image_bytes)
    record_position(book_id, chapter_no, moment["paragraph_index"], paragraphs)

    print(f"[{book_id}/{chapter_no}] Done -> {image_path} (insert after paragraph {moment['paragraph_index']}/{len(paragraphs)})")
    return image_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("book_id", help="Book id under input/, e.g. 1")
    parser.add_argument(
        "--chapter", type=int, default=None,
        help="Only process this one chapter number (still picks up the most "
             "recent earlier chapter's image, if any, for continuity).",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Regenerate even if the output image already exists.",
    )
    parser.add_argument(
        "--rebuild-bible", action="store_true",
        help="Start the cast bible from scratch instead of loading the saved "
             "one. Rescans every chapter for cast and re-renders each anchor "
             "portrait, so existing identities and faces are replaced.",
    )
    parser.add_argument(
        "--recheck-ages", action="store_true",
        help="Re-derive every character's gender and age from the chapters "
             "instead of trusting the saved bible. Use on books written "
             "before ages were read faithfully, where children were recorded "
             "as adults. Keeps identities and existing portraits; a portrait "
             "is only re-rendered where the corrected age no longer matches "
             "it.",
    )
    parser.add_argument(
        "--batch-size", type=int, default=5,
        help="Chapters per batch (default 5). Each batch is scanned for new "
             "cast before any of it is rendered. Progress is on disk, so a "
             "failed batch is resumed by re-running the same command.",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Stop after this many chapters actually processed this run.",
    )
    args = parser.parse_args()

    if args.rebuild_bible:
        # Clearing the roster is not enough on its own: extend_bible reads
        # the scan record off the same file, so every chapter still counts
        # as already scanned and the rebuilt bible comes back empty. Wipe
        # both together.
        characters = []
        save_bible(args.book_id, [], scanned=set())
    else:
        characters = load_bible(args.book_id)
        # Books whose bible predates the gender/age fields get them filled
        # in once, here, rather than re-rendering every anchor portrait.
        characters = backfill_identity_facts(
            args.book_id, characters, recheck=args.recheck_ages
        )

    # A story that jumps forward ages everyone on the far side of the jump.
    # Detected once and recorded in the bible, so later runs just read it.
    skips = detect_time_skips(args.book_id)
    if skips != load_skips(args.book_id):
        save_bible(args.book_id, characters, skips=skips)

    all_chapters = list_chapter_numbers(args.book_id)
    chapter_numbers = [args.chapter] if args.chapter is not None else all_chapters

    previous_image_path = latest_image_before(args.book_id, chapter_numbers[0], all_chapters)
    processed = skipped = blocked = 0

    for start in range(0, len(chapter_numbers), args.batch_size):
        if args.limit is not None and processed >= args.limit:
            break

        batch = chapter_numbers[start:start + args.batch_size]
        batch_no = start // args.batch_size + 1
        total_batches = (len(chapter_numbers) + args.batch_size - 1) // args.batch_size
        print(f"\n=== Batch {batch_no}/{total_batches}: chapters {batch[0]}-{batch[-1]} ===")

        # Setup pass: learn this batch's cast before rendering any of it, so a
        # character introduced mid-batch already has a locked identity by the
        # time their scene comes up. Chapters scanned on an earlier run are
        # skipped inside extend_bible, so this costs at most one call per batch,
        # once ever.
        characters = extend_bible(args.book_id, characters, batch)

        for chapter_no in batch:
            if args.limit is not None and processed >= args.limit:
                break

            image_path = chapter_image_path(args.book_id, chapter_no)
            if image_path.exists() and not args.force:
                print(f"[{args.book_id}/{chapter_no}] Already exists, skipping (use --force to regenerate).")
                previous_image_path = image_path
                skipped += 1
                continue

            try:
                result = process_chapter(
                    args.book_id, chapter_no, characters, previous_image_path, skips
                )
            except Exception as e:
                # One bad chapter shouldn't kill a long run — record and move on.
                print(f"[{args.book_id}/{chapter_no}] ERROR: {type(e).__name__}: {e}")
                blocked += 1
                continue

            if result is None:
                blocked += 1
            else:
                previous_image_path = result
                processed += 1

        done = min(start + args.batch_size, len(chapter_numbers))
        print(f"--- Batch {batch_no} complete: {processed} rendered, {skipped} already present, "
              f"{blocked} blocked/errored ({done}/{len(chapter_numbers)} chapters seen) ---")

    print(f"\nRun finished: {processed} rendered, {skipped} already present, {blocked} blocked/errored.")


if __name__ == "__main__":
    main()
