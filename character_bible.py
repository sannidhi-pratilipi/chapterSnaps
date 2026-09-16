"""Per-book character bible: one locked identity + one anchor portrait per
recurring character, established once and reused verbatim by every chapter.

Without this, each chapter asks the text model to describe the cast from
scratch, and those descriptions drift — a character's age, hair and build all
shift from chapter to chapter, and names can change outright. Chaining each
chapter's image off the previous one then compounds that drift visually.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from chapters import OUTPUT_DIR, list_chapter_numbers, read_chapter_text
from llm_client.images import (
    ANCHOR_IMAGE_MODEL,
    PORTRAIT_SIZE,
    ImageBlockedError,
    render_image,
)
from llm_client.tfy_client import get_tfy_client
from prompts.character_prompt import (
    CHARACTER_ANCHOR_PORTRAIT_PROMPT,
    CHARACTER_BIBLE_SYSTEM_PROMPT,
    IDENTITY_FACTS_SYSTEM_PROMPT,
    TIME_SKIP_SYSTEM_PROMPT,
)

TEXT_MODEL = "google-vertex/google-gemini-3.1-flash-lite"


def bible_path(book_id: str) -> Path:
    return OUTPUT_DIR / book_id / "characters.xml"


# A character keeps ONE portrait for the whole book. A second is only rendered
# when the story moves them somewhere the first genuinely cannot stand in for,
# which in practice means one of two things: they cross between childhood and
# adulthood, or the book jumps far enough that the face itself would have
# changed. Short of that the same portrait is reused, because a face is
# recognisably the same person across years, and a fresh render is a fresh
# face — the inconsistency costs far more than the slight age mismatch.
ADULT_AGE = 18
ANCHOR_AGE_TOLERANCE = 15


def anchor_path(book_id: str, character_id: str, age: str | int | None = None) -> Path:
    """Where a character's portrait lives. The un-suffixed name is kept for the
    portrait rendered at their first age, so bibles written before a story's
    time jumps were understood keep working untouched."""
    directory = OUTPUT_DIR / book_id / "characters"
    return directory / (f"{character_id}@{age}.png" if age else f"{character_id}.png")


def parse_skips(text: str) -> list[tuple[int, int]]:
    """"38:15,44:2" -> [(38, 15), (44, 2)] — from this chapter on, everyone is
    that many years older."""
    skips = []
    for part in (p.strip() for p in text.split(",") if p.strip()):
        chapter, _, years = part.partition(":")
        if chapter.strip().isdigit() and years.strip().isdigit():
            skips.append((int(chapter), int(years)))
    return sorted(skips)


def format_skips(skips: list[tuple[int, int]]) -> str:
    return ",".join(f"{chapter}:{years}" for chapter, years in sorted(skips))


def age_at_chapter(character: dict, chapter_no: int, skips: list[tuple[int, int]]) -> str:
    """The character's age in this particular chapter.

    The bible records one age, taken from where they first appear. A story that
    jumps forward leaves that age right for the early chapters and wrong for
    everything after — which is how a schoolboy ends up locked at the age he
    reaches two-thirds of the way through the book, wearing a school uniform.
    """
    base = character.get("age")
    if not str(base).isdigit():
        return ""
    since = int(character.get("age_ref_chapter") or 1)
    # The recorded age belongs to one chapter, and the jumps run in both
    # directions from it: a character first described after a jump — an adult
    # home from university in chapter 38 — was a child in the chapters before
    # it, and has to be aged back down for those.
    forward = sum(y for chapter, y in skips if since < chapter <= chapter_no)
    backward = sum(y for chapter, y in skips if chapter_no < chapter <= since)
    return str(max(0, int(base) + forward - backward))


def load_bible(book_id: str) -> list[dict]:
    path = bible_path(book_id)
    if not path.exists():
        return []

    characters = []
    for element in ET.parse(path).getroot().findall("character"):
        anchor = (element.findtext("anchor_image") or "").strip()
        # age -> portrait path, one per age this character has been rendered at.
        anchors = {
            (a.get("age") or "").strip(): (a.text or "").strip()
            for a in element.findall("anchor")
            if (a.text or "").strip()
        }
        if anchor:
            # Pre-timeline bibles recorded a single portrait; it belongs to
            # whatever age that character was written at.
            anchors.setdefault((element.findtext("age") or "").strip(), anchor)
        characters.append({
            "id": (element.get("id") or "").strip(),
            "name": (element.findtext("name") or "").strip(),
            "identity": (element.findtext("identity") or "").strip(),
            "gender": (element.findtext("gender") or "").strip(),
            "age": (element.findtext("age") or "").strip(),
            "age_ref_chapter": (element.findtext("age_ref_chapter") or "").strip(),
            "anchors": anchors,
            "default_outfit": (element.findtext("default_outfit") or "").strip(),
            # anchor_image set -> portrait ready. anchor_blocked set -> the
            # safety filter refused it, don't keep retrying. Neither -> pending,
            # rendered the first time this character is actually in a frame.
            "anchor_image": anchor or None,
            "anchor_blocked": element.find("anchor_blocked") is not None,
        })
    return [c for c in characters if c["id"]]


def _parse_ranges(text: str) -> set[int]:
    numbers: set[int] = set()
    for part in (p.strip() for p in text.split(",") if p.strip()):
        low, sep, high = part.partition("-")
        if sep and low.isdigit() and high.isdigit():
            numbers.update(range(int(low), int(high) + 1))
        elif part.isdigit():
            numbers.add(int(part))
    return numbers


def _format_ranges(numbers: set[int]) -> str:
    """Collapse to "1-5,11,20-22" so the record stays readable on long books."""
    parts: list[str] = []
    start = previous = None
    for n in sorted(numbers):
        if start is None:
            start = previous = n
        elif n == previous + 1:
            previous = n
        else:
            parts.append(str(start) if start == previous else f"{start}-{previous}")
            start = previous = n
    if start is not None:
        parts.append(str(start) if start == previous else f"{start}-{previous}")
    return ",".join(parts)


def load_skips(book_id: str) -> list[tuple[int, int]]:
    path = bible_path(book_id)
    if not path.exists():
        return []
    return parse_skips(ET.parse(path).getroot().get("skips", ""))


def timeline_scanned(book_id: str) -> bool:
    path = bible_path(book_id)
    if not path.exists():
        return False
    return ET.parse(path).getroot().get("timeline_scanned") == "true"


def load_scanned(book_id: str) -> set[int]:
    """Chapters already scanned for new cast — recorded so no chapter is ever
    scanned twice, across runs as well as within one."""
    path = bible_path(book_id)
    if not path.exists():
        return set()
    return _parse_ranges(ET.parse(path).getroot().get("scanned", ""))


def save_bible(
    book_id: str,
    characters: list[dict],
    scanned: set[int] | None = None,
    skips: list[tuple[int, int]] | None = None,
    mark_timeline_scanned: bool | None = None,
) -> None:
    # Keep the existing scan record unless the caller is explicitly updating it.
    if scanned is None:
        scanned = load_scanned(book_id)
    if skips is None:
        skips = load_skips(book_id)
    if mark_timeline_scanned is None:
        mark_timeline_scanned = timeline_scanned(book_id)

    root = ET.Element("characters")
    if scanned:
        root.set("scanned", _format_ranges(scanned))
    if skips:
        root.set("skips", format_skips(skips))
    if mark_timeline_scanned:
        # Recorded even when the skip list is empty, so a book with no time
        # jumps is not rescanned for them on every run.
        root.set("timeline_scanned", "true")
    for character in characters:
        element = ET.SubElement(root, "character", id=character["id"])
        ET.SubElement(element, "name").text = character["name"]
        if character.get("gender"):
            ET.SubElement(element, "gender").text = character["gender"]
        if character.get("age"):
            ET.SubElement(element, "age").text = str(character["age"])
        if character.get("age_ref_chapter"):
            ET.SubElement(element, "age_ref_chapter").text = str(character["age_ref_chapter"])
        ET.SubElement(element, "identity").text = character["identity"]
        ET.SubElement(element, "default_outfit").text = character.get("default_outfit", "")
        for age, path in sorted((character.get("anchors") or {}).items()):
            ET.SubElement(element, "anchor", age=str(age)).text = path
        if character.get("anchor_blocked") and not character.get("anchors"):
            ET.SubElement(element, "anchor_blocked").text = "true"

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    path = bible_path(book_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def render_anchor(book_id: str, character: dict, age: str = "") -> None:
    """Render this character's identity portrait at `age`, recording it under
    that age (or marking them blocked, which is survivable — that character
    just falls back to text-only consistency).

    A character gets one portrait per age the book actually needs them at:
    a story that jumps forward needs the child and the adult, and attaching
    the wrong one is worse than attaching none, since the face reference
    overrides everything the text says about age.
    """
    age = str(age or character.get("age") or "")
    existing = character.get("anchors") or {}
    path = anchor_path(book_id, character["id"], age if existing else None)
    path.parent.mkdir(parents=True, exist_ok=True)
    at_age = f" at age {age}" if age else ""
    print(f"[{book_id}] Rendering anchor portrait for {character['name']}{at_age}...")
    try:
        path.write_bytes(render_image(
            ANCHOR_IMAGE_MODEL,
            CHARACTER_ANCHOR_PORTRAIT_PROMPT.format(
                identity=character["identity"],
                gender=character.get("gender") or "person",
                age=age or "adult",
                default_outfit=character.get("default_outfit", "plain everyday clothing"),
            ),
            metadata={
                "book_id": str(book_id),
                "stage": "anchor_portrait",
                "character_id": character["id"],
            },
            size=PORTRAIT_SIZE,
            # Anchors stay at 2K while chapter frames run at 4K: these are
            # re-uploaded as references on every chapter call, and a 17MB
            # multipart body would tax every request for identity detail the
            # model does not read back at that resolution.
            image_size="2K",
        ))
        character.setdefault("anchors", {})[age] = str(path.relative_to(OUTPUT_DIR))
        character["anchor_blocked"] = False
    except ImageBlockedError as e:
        print(f"[{book_id}] WARNING: anchor portrait blocked for {character['name']}: {e}")
        character["anchor_blocked"] = True


def _portrait_still_fits(rendered_age: int, scene_age: int) -> bool:
    """Whether a portrait rendered at one age can still stand in at another.

    It can, unless the two sit on opposite sides of childhood — where the face
    really is a different one — or are separated by enough years that the face
    would visibly have changed.
    """
    if (rendered_age < ADULT_AGE) != (scene_age < ADULT_AGE):
        return False
    return abs(rendered_age - scene_age) <= ANCHOR_AGE_TOLERANCE


def anchor_for_age(book_id: str, character: dict, age: str) -> tuple[str, Path] | None:
    """The existing portrait that best stands in for `age`, if any still fits."""
    candidates = [
        (existing_age, path)
        for existing_age, path in (character.get("anchors") or {}).items()
        if str(existing_age).isdigit() and (OUTPUT_DIR / path).exists()
    ]
    if not candidates:
        return None
    if not str(age).isdigit():
        # No age to match against — any portrait is better than none.
        best_age, best_path = candidates[0]
        return best_age, OUTPUT_DIR / best_path
    best_age, best_path = min(candidates, key=lambda c: abs(int(c[0]) - int(age)))
    if not _portrait_still_fits(int(best_age), int(age)):
        return None
    return best_age, OUTPUT_DIR / best_path


def ensure_anchors(
    book_id: str,
    characters: list[dict],
    needed_ids: list[str],
    chapter_no: int = 1,
    skips: list[tuple[int, int]] | None = None,
) -> bool:
    """Make sure everyone about to appear has a portrait at the age they are in
    THIS chapter.

    Portraits are deliberately deferred to this point rather than rendered when
    a character joins the bible: a character can be central to a chapter's text
    and still never appear in any hook-image frame, since each image shows only
    that chapter's single peak moment. Rendering a portrait on joining would
    pay for a fair number that are never used.

    A second portrait is rendered only when the story has moved a character far
    enough from every portrait they already have — so a book with no time jumps
    still pays for exactly one per character, as before.

    Returns True if the bible changed and should be saved.
    """
    by_id = {c["id"]: c for c in characters}
    skips = skips or []
    changed = False
    for cid in needed_ids:
        character = by_id.get(cid)
        if not character:
            continue
        age = age_at_chapter(character, chapter_no, skips)
        # The recorded portraits are trusted only as far as the files behind
        # them. Deleting a bad one used to leave the bible still claiming it
        # existed, so it was never re-rendered — and because the reference list
        # in process_chapter silently drops paths that don't exist, that
        # character then rendered with no face reference at all, free to drift.
        if anchor_for_age(book_id, character, age):
            continue
        if character.get("anchor_blocked") and not character.get("anchors"):
            continue
        render_anchor(book_id, character, age)
        changed = True
    return changed


def promote_characters(
    book_id: str,
    characters: list[dict],
    new_characters: list[dict],
    chapter_no: int = 1,
) -> list[dict]:
    """Fallback for a character the batch scan missed: add them to the bible
    so they get a locked identity like everyone else, instead of being
    re-described (and re-drifted) every chapter they appear in. Their portrait
    is rendered later, on first actual use.

    Mutates and returns `characters`. Existing entries are never rewritten —
    their anchors are already in use by chapters already rendered.
    """
    known = {c["id"] for c in characters}
    added = []
    for candidate in new_characters:
        if candidate["id"] in known or not candidate["identity"]:
            continue
        print(f"[{book_id}] New recurring character: {candidate['name']} — adding to bible")
        candidate.setdefault("age_ref_chapter", str(chapter_no))
        characters.append(candidate)
        known.add(candidate["id"])
        added.append(candidate)

    if added:
        save_bible(book_id, characters)
    return characters


def clean_field(text: str) -> str:
    """Strip the angle-bracket placeholders the model sometimes copies from the
    response template (`<identity>`) instead of replacing them."""
    return re.sub(r"^<+|>+$", "", text.strip()).strip()


def normalise_gender(text: str) -> str:
    """Collapse whatever the model wrote to 'man' or 'woman'. Anything else is
    dropped rather than guessed — a blank field is recoverable, a wrong one
    gets rendered."""
    lowered = clean_field(text).lower()
    if re.search(r"\b(woman|female|girl|lady)\b", lowered):
        return "woman"
    if re.search(r"\b(man|male|boy|gentleman)\b", lowered):
        return "man"
    return ""


def age_from_identity(identity: str) -> str:
    """Pull an age back out of a prose identity written before AGE was its own
    field — they nearly all end '..., 48 years old.'"""
    match = re.search(r"(\d{1,3})\s*(?:years old|-year-old|yo\b)", identity, re.I)
    return match.group(1) if match else ""


def detect_time_skips(book_id: str) -> list[tuple[int, int]]:
    """Find where the book jumps forward in time, once per book.

    Only the opening of each chapter is read. A jump is announced where it
    happens — "15 वर्षों बाद...", "ten years later" — so the first few hundred
    characters carry it, and feeding whole chapters of a fifty-chapter book to
    find one line is not worth what it costs.
    """
    if timeline_scanned(book_id):
        return load_skips(book_id)

    chapters = list_chapter_numbers(book_id)
    if not chapters:
        return []
    print(f"[{book_id}] Checking the book's timeline for time jumps...")
    openings = "\n\n".join(
        f"=== CHAPTER {n} ===\n{read_chapter_text(book_id, n)[:700]}" for n in chapters
    )

    response = get_tfy_client({
        "book_id": str(book_id),
        "stage": "timeline_scan",
    }).chat.completions.create(
        model=TEXT_MODEL,
        temperature=0.1,  # reading a marker off the page, not interpreting
        messages=[
            {"role": "system", "content": TIME_SKIP_SYSTEM_PROMPT},
            {"role": "user", "content": openings},
        ],
    )
    skips = parse_skips(
        ",".join(
            f"{parts[0].strip()}:{parts[1].strip()}"
            for line in (response.choices[0].message.content or "").splitlines()
            if len(parts := line.split("|")) >= 2
        )
    )
    if skips:
        summary = ", ".join(f"+{years}y from chapter {ch}" for ch, years in skips)
        print(f"[{book_id}] Timeline: {summary}")
    else:
        print(f"[{book_id}] Timeline: no time jumps.")
    # Recorded straight away — including when empty — so this costs one call
    # per book ever, and so every age derived from it is computed the same way.
    save_bible(book_id, load_bible(book_id), skips=skips, mark_timeline_scanned=True)
    return skips


def strip_age_from_identity(identity: str) -> str:
    """Remove an age left embedded in the prose.

    The age is a field now, and it moves when the story jumps forward, so a
    second copy sitting in the description only contradicts it a few chapters
    later — the renderer then gets told both '11' and '25 years old'.
    """
    cleaned = re.sub(
        r",?\s*(?:aged\s*)?\d{1,3}\s*(?:years old|-year-old|yo)\b\.?",
        "",
        identity,
        flags=re.I,
    ).strip()
    return re.sub(r"\s{2,}", " ", cleaned).rstrip(",. ") + "."


def backfill_identity_facts(
    book_id: str, characters: list[dict], recheck: bool = False
) -> list[dict]:
    """Fill in gender and age for roster entries saved before they were fields.

    Without this an existing book keeps rendering from an identity paragraph
    that never says whether the person is a man or a woman, and the image model
    falls back to guessing from the name. Ages are recovered locally where the
    prose still carries one; only what is genuinely missing costs a call, and
    the result is saved, so this runs at most once per book.
    """
    if recheck:
        # Re-derive everyone from the chapters instead of trusting what is
        # saved — for bibles written under an older rule, where every
        # character was forced to an adult age whatever the story said.
        for character in characters:
            character["gender"] = ""
            character["age"] = ""
            character["age_ref_chapter"] = ""
    else:
        for character in characters:
            if not character.get("age"):
                character["age"] = age_from_identity(character.get("identity", ""))

    missing = [
        c for c in characters
        if not c.get("gender") or not c.get("age") or not c.get("age_ref_chapter")
    ]
    if not missing:
        return characters

    print(f"[{book_id}] Filling in gender/age for: {', '.join(c['name'] for c in missing)}")
    # Read from the front of the book: a character's gender and age are
    # established when they are introduced, not in the chapter being rendered.
    chapters_available = list_chapter_numbers(book_id)
    sample = chapters_available if recheck else chapters_available[:6]
    # Openings carry the age evidence — school, class, who collects them,
    # "seven years later" — without paying for every chapter in full.
    chapters = "\n\n".join(
        f"=== CHAPTER {n} ===\n{read_chapter_text(book_id, n)[:2500]}" for n in sample
    )
    roster = "\n".join(f"- {c['id']} | {c['name']}: {c['identity']}" for c in missing)

    response = get_tfy_client({
        "book_id": str(book_id),
        "stage": "identity_facts_backfill",
    }).chat.completions.create(
        model=TEXT_MODEL,
        temperature=0.2,  # factual recovery, not invention
        messages=[
            {"role": "system", "content": IDENTITY_FACTS_SYSTEM_PROMPT},
            {"role": "user", "content": f"{chapters}\n\nCHARACTERS NEEDING GENDER AND AGE:\n{roster}"},
        ],
    )

    by_id = {c["id"]: c for c in characters}
    for line in (response.choices[0].message.content or "").splitlines():
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 3:
            continue
        character = by_id.get(parts[0].lower())
        if not character:
            continue
        if not character.get("gender"):
            character["gender"] = normalise_gender(parts[1])
        if not character.get("age") and parts[2].isdigit():
            character["age"] = parts[2]
        if not character.get("age_ref_chapter"):
            character["age_ref_chapter"] = parts[3] if len(parts) > 3 and parts[3].isdigit() else "1"

    for character in characters:
        character["identity"] = strip_age_from_identity(character["identity"])

    save_bible(book_id, characters)
    return characters


def _parse_bible(raw: str) -> list[dict]:
    characters = []
    for block in raw.split("---"):
        id_match = re.search(r"CHARACTER:\s*([^\s|]+)\s*\|\s*(.+)", block)
        identity_match = re.search(r"IDENTITY:\s*(.*?)(?=\nDEFAULT_OUTFIT:|\Z)", block, re.DOTALL)
        outfit_match = re.search(r"DEFAULT_OUTFIT:\s*(.+)", block, re.DOTALL)
        if not id_match or not identity_match:
            continue
        gender_match = re.search(r"GENDER:\s*(.+)", block)
        age_match = re.search(r"AGE:\s*(\d{1,3})", block)
        ref_match = re.search(r"AGE_IN_CHAPTER:\s*(\d{1,4})", block)
        characters.append({
            "id": id_match.group(1).strip().lower(),
            "name": id_match.group(2).strip(),
            "gender": normalise_gender(gender_match.group(1)) if gender_match else "",
            "age": age_match.group(1) if age_match else "",
            "age_ref_chapter": ref_match.group(1) if ref_match else "",
            "identity": clean_field(identity_match.group(1)),
            "default_outfit": clean_field(outfit_match.group(1)) if outfit_match else "",
        })
    return characters


def _existing_roster_block(characters: list[dict]) -> str:
    if not characters:
        return "EXISTING ROSTER: (empty — this is the start of the book)"
    lines = ["EXISTING ROSTER — already established, do NOT list these again:"]
    for c in characters:
        lines.append(f"- {c['id']} | {c['name']}: {c['identity']}")
    return "\n".join(lines)


def extend_bible(
    book_id: str, characters: list[dict], chapter_numbers: list[int]
) -> list[dict]:
    """Scan the chapters about to be rendered and add any significant new cast
    member to the bible *before* those chapters are generated, so they already
    have a locked identity and portrait when their scenes come up.

    Reading a whole batch at once — rather than judging one chapter in
    isolation — is what makes "does this person actually matter?" answerable:
    someone who shows up across several of these chapters is real cast, someone
    who appears once is not.

    Chapters already scanned on a previous run are skipped, so each chapter is
    read for cast exactly once for the life of the book.

    Existing entries are never rewritten; their portraits are already in use by
    chapters that have been rendered.
    """
    already_scanned = load_scanned(book_id)
    todo = [n for n in chapter_numbers if n not in already_scanned]
    if not todo:
        return characters

    scan = "\n\n".join(
        f"=== CHAPTER {n} ===\n{read_chapter_text(book_id, n)}" for n in todo
    )
    span = f"{todo[0]}-{todo[-1]}" if len(todo) > 1 else str(todo[0])
    print(f"[{book_id}] Scanning chapters {span} for new cast...")

    response = get_tfy_client({
        "book_id": str(book_id),
        "stage": "cast_scan",
        "chapter_range": span,
    }).chat.completions.create(
        model=TEXT_MODEL,
        temperature=0.3,  # low — factual extraction, not a creative pass
        messages=[
            {"role": "system", "content": CHARACTER_BIBLE_SYSTEM_PROMPT},
            {"role": "user", "content": f"{_existing_roster_block(characters)}\n\n{scan}"},
        ],
    )
    found = _parse_bible((response.choices[0].message.content or "").strip())

    # Record the scan before anything else, so these chapters are never read
    # for cast again even if no one new turned up.
    scanned = already_scanned | set(todo)

    known = {c["id"] for c in characters}
    fresh = [c for c in found if c["id"] not in known and c["identity"]]
    if not fresh:
        print(f"[{book_id}] No new cast in chapters {span}.")
        save_bible(book_id, characters, scanned)
        return characters

    # Text entries only — each one's portrait is rendered later, the first time
    # they actually turn up in a frame.
    print(f"[{book_id}] New cast: {', '.join(c['name'] for c in fresh)}")
    for character in fresh:
        # Falls back to the start of the batch their age was read from — it
        # is their age HERE, not in chapter 1 and not after a later jump.
        if not character.get("age_ref_chapter"):
            character["age_ref_chapter"] = str(todo[0])
    characters.extend(fresh)
    save_bible(book_id, characters, scanned)
    return characters
