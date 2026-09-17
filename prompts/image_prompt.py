# Opens the prompt. The detailed optical block below ends up ~75% of the way
# into a long prompt once the cast and scene are in front of it, which is too
# late to establish the medium — this short declaration goes first so the model
# knows it is making a photograph before it reads anything else.
PHOTOREAL_LEAD = (
    "THIS IS A PHOTOGRAPH — a single frame of 35mm motion picture film, shot "
    "on an ARRI Alexa LF with a 50mm f/1.8 prime, of real people who were "
    "physically present in front of the camera. Real skin with pores, fine "
    "lines and uneven tone; real hair with stray strands; real fabric with "
    "weave and creases; real light with true falloff and shadow. It was taken "
    "from inside the scene by someone nobody noticed was there. Every detail "
    "below describes something that actually stood in front of that lens."
)

# Written as positive optical imperatives rather than prohibitions. A distilled
# image model tends to miss the negation and latch onto the banned keyword, so
# "never a CGI render" can pull toward CGI; naming the film stock, lens and
# grain it SHOULD produce is what actually steers it. Camera and texture specs
# are front-loaded because the opening of the prompt carries the most weight.
CINEMATIC_STYLE = (
    "CAMERA & OPTICAL SPECIFICATIONS:\n"
    "- Authentic 35mm motion picture film scan with fine organic silver halide "
    "grain, shot on an ARRI Alexa LF with a 50mm f/1.8 prime lens.\n"
    "- Sharp plane of focus on the subject, with soft optical background bokeh "
    "and natural depth falloff.\n"
    "- Skin rendered with natural subsurface scattering, visible pore "
    "micro-texture, peach fuzz, fine lines, and organic tone variation.\n"
    "- Fabric with tangible micro-weave, realistic tension creases, natural "
    "drape under gravity, and true fibre highlights.\n"
    "- Physically accurate key lighting with defined shadow boundaries, "
    "realistic bounce fill, and dynamic highlight falloff.\n"
    "- Colour grade: cinematic film print stock, deep shadow tones, rich "
    "mid-tones, uncompressed highlight detail.\n"
    "- 16:9 cinematic frame composition.\n\n"
    "CASTING & WARDROBE:\n"
    "- Authentic regional facial structure, natural skin tones, and features "
    "matching the exact culture of the scene — for everyone in frame, "
    "including people in the background.\n"
    "- Everyone in frame is the gender and the age their description gives "
    "them, background people included. An age is a face, not a label: give a "
    "person in their fifties the skin, jawline, hairline, grey and eye-area "
    "lines of their fifties, and a person of twenty the face of twenty. "
    "Never default the frame to a cast of mid-twenties adults."
)

# The most common failure before this block existed: everyone in frame turning
# to face the lens and settling into a posed, evenly-spaced group shot, which
# reads as a cast photo rather than a moment lifted out of the story. Stated as
# what the camera IS — an unnoticed witness — rather than as a ban on eye
# contact, because a bare prohibition tends to pull the gaze straight back.
#
# Telling the PEOPLE not to look at the lens was not enough on its own: the
# attached anchor portraits are straight-to-camera studio shots, and the
# renderer copies a reference's gaze along with its bone structure. So the
# rules below also move the CAMERA off everyone's eye-line and hand each
# person a named head angle. A lens nobody is facing cannot be looked into,
# which holds where an instruction not to look does not.
CANDID_VIEWPOINT = (
    "VIEWPOINT — an unnoticed witness took this; it was not taken for anyone:\n"
    "- The camera is an uninvolved bystander standing inside the scene. Nobody "
    "in frame knows it is there, nobody was asked to pose, and this instant "
    "would have looked exactly the same if no one had ever pointed a lens at "
    "it.\n"
    "- Every person's attention belongs to the scene. Their eyes are on "
    "whoever or whatever their ACTION line names, and their face, shoulders "
    "and whole body are turned toward that. No one looks into the camera, "
    "addresses it, or acknowledges it.\n"
    "- The lens sits OFF the axis of every person's gaze. Before placing the "
    "camera, follow each person's eye-line to the thing they are watching, "
    "then stand the camera away from that line — past a shoulder, off to one "
    "side, above or below their eye level, half-blocked by something in the "
    "room. Nobody in this frame is facing the spot the camera occupies, so "
    "the picture gives their eyes somewhere else to be.\n"
    "- Give every person a definite head angle taken from the action: three-"
    "quarter away, full profile, chin dropped, head turned back over a "
    "shoulder, tilted up toward someone taller, or the back of the head with "
    "the face hidden. Each face is rotated off the camera axis by a visible "
    "amount — the nose points somewhere other than at the viewer, and both "
    "eyes travel with it. Nobody is squared front-on with their pupils "
    "centred.\n"
    "- This holds for background and incidental people too: passers-by, "
    "onlookers, a shopkeeper, a driver in the next vehicle. They are busy "
    "with their own business and turned into it, not watching the "
    "photographer.\n"

    "- Everyone is caught mid-action: weight already shifted, an arm already "
    "extended, a step already taken, a hand already gripping or bracing or "
    "pressing, the expression already breaking across the face. Nobody stands "
    "neutral with their hands at their sides waiting to be photographed.\n"
    "- People stand at unequal distances from the lens and overlap one "
    "another, as they would in a real room. Never a row of people abreast, "
    "evenly spaced, centred and squared to the camera."
)

# Placed immediately after the scene rather than inside CINEMATIC_STYLE: these
# rules govern WHAT is depicted, not how it is shot, and when they sat at the
# tail of a long style block the renderer ignored them — objects the brief had
# resting on the floor came back hovering in mid-air.
SCENE_REALISM = (
    "ENVIRONMENT & SPATIAL GEOMETRY — build the place first, as a real space:\n"
    "- Give it a complete, coherent structure: floor, walls or ground, ceiling "
    "or sky, and the openings, fixtures and furniture that belong to it, all "
    "consistent with each other and with a single viewpoint.\n"
    "- Every background element is anchored to something — standing on the "
    "floor, mounted to a wall, hanging from the ceiling, or resting on a piece "
    "of furniture. Nothing sits loose in space or passes through a surface.\n"
    "- Anything built into the structure keeps the fixed position it really "
    "has within it: controls, handles, fittings and installed equipment stay "
    "where they are actually mounted, attached to the surface that holds them, "
    "at the right height and orientation for someone using them.\n"
    "- Seating faces the direction that seating really faces, and a person "
    "occupying it is squared to it unless the scene says they have turned.\n"
    "- Where a space is built around one focal point, that point is at the "
    "FRONT of it and every row of seating faces it square on, aisles running "
    "between the rows toward it. People turned away from the thing they are "
    "gathered for, or that thing set off to the side of seating that faces "
    "elsewhere, is wrong however good the shot: the seating is what says "
    "where the front is.\n"
    "- The room is arranged the way it would really be used. Things that "
    "exist in relation to each other are placed so that relation works: a "
    "sofa faces the screen it is for from across the room, never directly "
    "beneath it on the same wall; chairs face the desk or table they belong "
    "to; a door has clear floor to swing into. If someone sitting there "
    "could not do the thing that furniture is for, it is in the wrong "
    "place.\n"
    "- Build the one room the brief describes, from the viewpoint it names: "
    "its left wall, the far wall, its right wall and the floor between "
    "them, at the size it gives. Every object and every person goes where "
    "that layout puts them, and the room keeps the same size and shape "
    "right across the frame.\n"
    "- Furniture and people are at true scale to each other: a seated "
    "adult's head reaches near the top of a sofa back, a standing adult "
    "clears a table by well over half their height, a doorway is taller "
    "than the people passing through it. Nothing is oversized or "
    "miniature for the space it sits in.\n"
    "- People occupy floor the furniture does not: nobody stands inside a "
    "table, a sofa or a wall, and anyone behind a piece of furniture is "
    "partly hidden by it, with its near edge crossing them.\n"
    "- Seats hold the number of people the scene seats, in the places it "
    "seats them, facing the way it says they face. No extra chairs "
    "invented to fill the floor.\n"
    "- The background is specific to this place, never a vague blur standing "
    "in for one.\n\n"
    "LIMBS & GESTURES:\n"
    "- Each person has exactly two arms and two legs, joined at the shoulders "
    "and hips, and one head.\n"
    "- Each hand does exactly ONE thing in this frame, in one place: no "
    "duplicated hands, no second version of an arm, no hand doing two jobs at "
    "once. Give each person the pose their ACTION line describes.\n"
    "- Give each person the physical action their ACTION line describes — the "
    "grip, the reach, the block, the pull, the lean — carried out, not "
    "approximated by two people standing near each other.\n\n"
    "AIM AND REACH — every gesture ends somewhere inside this frame:\n"
    "- An arm that points, aims, reaches or holds something out runs toward "
    "the thing its ACTION line names, and that thing is visible in the shot "
    "in that direction, at the height it actually sits. Follow the line of "
    "the arm: it must arrive at the named target.\n"
    "- Nothing is pointed, aimed, offered or extended toward the camera, and "
    "no line of aim passes out through the lens. The camera watches that line "
    "cross the room on a diagonal, so the person and the thing they are "
    "aiming at are both in the picture and neither is reduced to a back "
    "turned to the lens. That angle comes from where the camera stands, never "
    "from moving the room: the furniture and the focal point stay where the "
    "space needs them.\n\n"
    "SPACES WITH A KNOWN LAYOUT — some places have an arrangement everyone "
    "recognises, and it is not free to change:\n"
    "- Build the layout that kind of space really has. Its fixed parts sit "
    "where they really sit, in the numbers they really come in, at the height "
    "and on the side they are really fitted, and facing the way they really "
    "face. One of a thing that comes in ones.\n"
    "- Every person occupies a place the space actually provides — a seat, a "
    "bench, a step, a stool — squarely, with their weight on it. Nobody sits "
    "between two places, on the controls, or on a surface not meant to take "
    "them.\n"
    "- Anyone operating the space is at the position it is operated from, "
    "turned the way that job requires, with their hands on the controls that "
    "job uses.\n"
    "- Keep the real dimensions. A tight interior stays tight — heads close "
    "under the ceiling, shoulders near the walls, little room between rows — "
    "and a large space stays large. Neither is given the proportions of the "
    "other.\n\n"    "PHYSICAL TRUTH OF THIS FRAME — a real camera could only have captured it "
    "this way:\n"
    "- Each object named above sits exactly where the scene places it, with its "
    "full weight on that surface, touching it and casting contact shadow.\n"
    "- Anything in a person's hand is gripped with the fingers closed around "
    "it. Every other object rests on furniture, floor or ground.\n"
    "- Each person's weight is settled — through their feet into the floor, or "
    "their seat into the chair, bed or step they occupy — in a balance a real "
    "body holds.\n"
    "- Where a hand meets a shoulder, arm, fabric or surface, the contact is "
    "solid and presses in, with visible compression.\n"
    "- Hands and limbs are anatomically complete and correctly proportioned, "
    "five fingers per hand, joined naturally to the body.\n"
    "- The people are caught mid-motion, but every OBJECT is settled: nothing "
    "is in flight, mid-fall, mid-spill or mid-throw. Anything not closed "
    "inside a named hand has already come to rest on a surface that "
    "supports it."
)

# Always on, and deliberately last in the prompt so nothing after it can
# soften it. This is the final gate before render: by this point the WEARING
# lines have already been written by an earlier model from chapter text that
# may itself describe someone undressed, and the attached anchor portraits are
# their own source of garments. So this block is stated as outranking both,
# and as outranking the scene — otherwise each stage assumes an earlier one
# handled it and nobody does.
#
# Decency and platform safety are one block rather than two. They were split
# before — modesty in the body of the prompt, the safety constraints in a
# retry-only addendum that fired AFTER a frame had already been silently
# blocked, which made every first attempt the experiment. Both halves ship on
# every render now, and SAFETY_RETRY_PREFIX escalates this same block instead
# of restating it, so there is one place to edit these rules.
SAFETY_RULES = (
    "SAFETY & DECENCY — this governs the frame. It overrides the WEARING "
    "lines, the scene text and every attached reference image, and nothing "
    "in this prompt relaxes it:\n"
    "- Every person in this frame is fully and properly dressed, including "
    "everyone in the background. Clothing covers shoulders, chest, torso, "
    "midriff and legs, sits closed and fastened, and is opaque, dry and "
    "intact — never sheer, clinging, wet, torn, unbuttoned, slipping or "
    "underwear-like.\n"
    "- Every man wears a shirt, kurta or other upper garment, on his body and "
    "fastened. No bare chest, no bare torso, no towel or sheet standing in "
    "for clothing — not in a bedroom, bathroom, sickbed, gym, field, "
    "riverbank or any scene of heat, sleep, work, injury or waking.\n"
    "- If the WEARING text or the scene describes anyone as undressed, "
    "shirtless, in underwear, in a towel, or in anything revealing, disregard "
    "that description and clothe them in the decent, fully-covering outfit "
    "they would wear in that place at that hour. Carry the moment with "
    "expression, posture, framing and light instead.\n"
    "- Frame and crop it decently too: no shot composed around a body, no "
    "close crop on chest, hips or legs, no camera angle that looks up a "
    "garment or down a neckline. The camera is at a respectful distance and "
    "on the faces and the action.\n"
    "- Bodies are held in ordinary, unsuggestive postures, and contact "
    "between people is the plain kind a family audience reads without "
    "comment.\n"
    "- Everyone depicted is clearly an adult. Where a person's age is "
    "uncertain, render them as unmistakably adult.\n"
    "- Keep the whole frame publishable: no nudity or sexual content, no "
    "self-harm, and no blood, wounds, gore or graphic violence.\n"
    "- Intimate, sexual and violent moments are never depicted at all — not "
    "explicitly, not mildly, not suggestively, whatever the scene text asks "
    "for. Nothing sexual or romantic-physical: no kissing, embracing, "
    "undressing, lying together, straddling, caressing, or bodies pressed "
    "together. Nothing violent: no striking, slapping, choking, grabbing, "
    "dragging, restraining, weapons raised or in use, and no one mid-blow or "
    "mid-fall from one.\n"
    "- Those moments are shown by what surrounds them instead. Render the "
    "beat just before or just after: two people standing apart in the same "
    "room, a face reacting from a doorway, a back turned, a closed door, a "
    "hand on a doorframe, an object left behind, the stillness after. The "
    "viewer understands what happened without being shown it happening.\n"
    "- Where people must be near each other, keep them at ordinary social "
    "distance in plain, unsuggestive postures — standing, seated, walking, "
    "facing one another and talking. Contact is limited to the everyday kind "
    "a family audience reads without comment: a hand on a forearm or "
    "shoulder, a steadying touch.\n"
    "- When the scene gives you nothing safe to show, fall back to the "
    "people's faces and the room around them. A restrained frame is always "
    "the right answer here; an explicit one is never salvageable."
)


# Vehicle interiors were the single worst-failing setting, and they failed the
# same way every time: the frame came back as two incompatible cameras welded
# together — the road ahead seen through the windshield, which only happens
# from BEHIND the occupants, and simultaneously the driver's face square to the
# lens, which only happens from in FRONT of her. The generic SCENE_REALISM
# rules never caught it, because each half is a legal photograph on its own and
# nothing in the brief says a car has only one interior geometry.
#
# Appended only for scenes that are actually in a vehicle (see vehicle_block).
# A car block on a kitchen scene is prompt weight spent on nothing, and the
# renderer has been observed to drag furniture toward whatever the last long
# block described.
VEHICLE_INTERIOR = (
    "INSIDE A VEHICLE — one camera, in one seat, for the whole frame:\n"
    "- The camera occupies a single real position inside this vehicle, and "
    "everything in the frame is what a lens in that one spot would see. "
    "Choose it before anything else, and let it decide which faces are "
    "visible — rather than showing the road ahead and a front-on face "
    "together, which no single camera inside a car can capture.\n"
    "- From a seat BEHIND the occupants, the windshield and the road ahead "
    "fill the frame, and the people in the front seats are seen from behind: "
    "backs of heads, shoulders, a cheek in three-quarter, an eye-line caught "
    "in the rear-view or wing mirror. A face reaches this camera only as a "
    "reflection in a mirror, and it appears in exactly one place — either "
    "reflected or direct, never the same face twice in one frame.\n"
    "- From a seat BESIDE or AHEAD of a person, their face is visible "
    "directly, and what lies behind them through the glass is the side "
    "window, the door, the seat back, or the road falling away — not the "
    "forward view down the lane.\n"
    "- The vehicle is a complete built interior around the people: dashboard "
    "under the windshield with its instrument cluster, the A-pillar between "
    "windshield and side window, door card and window frame, headrests, seat "
    "backs and fastened seatbelts, roof lining overhead. The cabin encloses "
    "them on every side rather than opening into empty space.\n"
    "- The steering wheel sits on its column directly in front of ONE seat, "
    "at chest height, with the dashboard beneath it and the driver squared "
    "to it, hands closed on the rim. That is the only steering wheel in the "
    "vehicle — the other front seat has a plain dashboard in front of it.\n"
    "- The driver's seat is on the side this scene's country drives on — the "
    "country visible through the windows, not the one the vehicle's badge "
    "suggests. Where traffic keeps left (India, the UK, Japan, Australia) the "
    "steering wheel, pedals, instrument cluster and gear lever are ALL on the "
    "RIGHT of the cabin and the driver sits on the right; where traffic keeps "
    "right they are all on the left. An Indian street outside means a "
    "right-hand-drive cabin inside, whatever make of car it is.\n"
    "- The seats belong to ONE row at ONE depth from the lens. Everyone in "
    "the front row sits shoulder to shoulder at the same distance from the "
    "camera, and any row behind them is genuinely further away — smaller in "
    "frame, seen past the front headrests and seat backs, through the gap "
    "between them. Front-row doors, rear-row doors and their handles and "
    "windows each stay with their own row rather than meeting in one plane.\n"
    "- The driver's seat is the one nearest the centre of the road, so "
    "oncoming vehicles pass on the DRIVER'S side of the windshield, facing "
    "the camera, while the kerb, parked vehicles, shopfronts and pedestrians "
    "run along the passenger's side.\n"
    "- Everyone in the cabin is IN a seat and facing the way that seat faces: "
    "hips square in the seat pan, back against the seat back, both feet down "
    "in the footwell in front of them, at the height that seat really puts "
    "them. When the action turns someone toward a neighbour, only the upper "
    "body turns — shoulders and head rotate over hips that stay in the seat, "
    "knees still pointing forward. Nobody sits sideways with their legs up on "
    "the seat, and nobody perches on the centre console, the armrest, the "
    "gear lever or the gap between two seats.\n"
    "- A person in the driver's seat keeps their body to the wheel: knees "
    "under the steering column, feet at the pedals, however far they have "
    "turned their head and shoulders to speak to someone.\n"
    "- No one floats between seats or sits taller than the roof allows. "
    "Anyone at the frame edge is a whole person in a real seat, not a stray "
    "head or shoulder with no body.\n"
    "- Every vehicle outside is the kind that belongs on this road in this "
    "country, on its correct side, moving the direction its lane runs."
)


# Cheap keyword gate rather than another model call: the block costs nothing to
# skip and a false positive only adds unused rules, so the list leans inclusive.
VEHICLE_CUES = (
    "car", "cab", "taxi", "auto", "rickshaw", "van", "truck", "lorry", "jeep",
    "bus", "driving", "drives", "driver", "steering", "windshield", "windscreen",
    "dashboard", "passenger seat", "back seat", "backseat", "rear-view",
    "rearview", "seatbelt", "seat belt", "traffic", "highway", "roadside",
)


def vehicle_block(event_description: str) -> str:
    """Return the vehicle-interior rules if this scene appears to happen in or
    around a vehicle, otherwise an empty string."""
    text = event_description.lower()
    return f"\n{VEHICLE_INTERIOR}\n" if any(c in text for c in VEHICLE_CUES) else ""


# The same instruction was written three times — once in each system prompt
# and once in CANDID_VIEWPOINT — and the three copies had drifted apart in
# wording, which is how a rule quietly weakens. One definition now, used by
# both system prompts. It lives here rather than in the prompt body because it
# governs how to read an ATTACHMENT, which is meaningless when none is sent.
PORTRAIT_REFERENCE_RULE = (
    "CHARACTER PORTRAITS — identity only:\n"
    "- Use each attached portrait strictly for facial structure: eyes, nose, "
    "jawline, brow, hairline, face width and length, skin tone, hair type, "
    "age. That face is reproduced feature by feature.\n"
    "- Everything else in the portrait belongs to the studio sitting and "
    "stays there — its flat lighting, plain backdrop and neutral clothing, "
    "and the fact that the subject looks straight down the lens. That frontal "
    "gaze is an artefact of being photographed, not a fact about the person.\n"
    "- Render each subject fully inside this scene instead: lit by this "
    "scene's light, wearing exactly what the WEARING section specifies, "
    "turned into the action at whatever head angle their ACTION line demands, "
    "with their eyes on what that line names."
)


# Chapter 1 only — no previous scene exists yet, so this frame establishes the
# grade and optical language every later chapter is held to.
FIRST_IMAGE_SYSTEM_PROMPT = (
    "You are a master cinematographer capturing a high-resolution 35mm film "
    "still of a dramatic story hook.\n\n"
    f"{CINEMATIC_STYLE}\n\n"
    f"{PORTRAIT_REFERENCE_RULE}\n\n"
    "Establish the precise colour grade, contrast ratio and film texture here "
    "— this frame locks the look for every chapter that follows."
)

# Chapter 2+ — receives two different kinds of reference image and must treat
# them differently, hence the explicit split below.
CONSISTENCY_IMAGE_SYSTEM_PROMPT = (
    "You are a master cinematographer maintaining strict visual continuity "
    "across a sequential story.\n\n"
    f"{PORTRAIT_REFERENCE_RULE}\n\n"
    "PREVIOUS SCENE FRAME — optics only:\n"
    "- Match its optical profile and nothing else: colour palette, contrast "
    "curve, lens grain, lighting atmosphere. Its pose, location and garments "
    "belong to that moment, and this is a different one.\n\n"
    "CONTINUITY EXECUTION:\n"
    "1. Identity: lock each face to its reference portrait, then layer this "
    "scene's specifics (sweat, dirt, tears, emotion) over that same base.\n"
    "2. Wardrobe: follow the WEARING text exactly. It is authoritative and "
    "governs over any garment visible in a reference image.\n"
    "3. Environment: build the location this scene describes, in full "
    "photographic detail.\n"
    "4. Optics: hold the 35mm cinematic film aesthetic throughout.\n\n"
    f"{CINEMATIC_STYLE}"
)

# The safety rules above already ship on every render, so a retry does not need
# a second copy of them — it needs them applied harder. This one line says the
# previous attempt was rejected and asks for the most conservative reading,
# which is the only thing a retry can usefully add.
SAFETY_RETRY_PREFIX = (
    "RETRY — the previous attempt at this frame was rejected by the safety "
    "filter. Apply the SAFETY & DECENCY rules below at their most "
    "conservative: pull the camera back, keep the moment indirect, and choose "
    "the plainest, most fully-covered staging the scene allows."
)
