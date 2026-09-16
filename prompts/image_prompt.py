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
    "Never default the frame to a cast of mid-twenties adults.\n"
    "- Modest, fully covering clothing appropriate to the region, period and "
    "setting of the scene."
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
    "- The attached portraits look straight down the lens because that is how "
    "a studio sitting is shot. That gaze belongs to the portrait session and "
    "stays in it: take the face from the reference, take where it is pointing "
    "and what the eyes are doing from this scene.\n"
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
    "- The room is arranged the way it would really be used. Things that "
    "exist in relation to each other are placed so that relation works: a "
    "sofa faces the screen it is for from across the room, never directly "
    "beneath it on the same wall; chairs face the desk or table they belong "
    "to; a door has clear floor to swing into. If someone sitting there "
    "could not do the thing that furniture is for, it is in the wrong "
    "place.\n"
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
    "LINES OF SIGHT AND AIM — every gesture ends somewhere inside this "
    "frame:\n"
    "- An arm that points, aims, reaches or holds something out runs toward "
    "the thing its ACTION line names, and that thing is visible in the shot "
    "in that direction, at the height it actually sits. Follow the line of "
    "the arm: it must arrive at the named target.\n"
    "- Nothing is pointed, aimed, offered or extended toward the camera, and "
    "no line of aim passes out through the lens. The camera stands off to the "
    "side of that line and watches it cross the room on a diagonal, so the "
    "person and the thing they are aiming at are both in the picture and "
    "neither is reduced to a back turned to the lens.\n"
    "- Each person's eyes go to whatever their ACTION line names, and that "
    "thing is where their gaze would actually land — if they are looking at "
    "something across the room, the angle of the head and eyes matches where "
    "it stands in the frame.\n\n"
    "PHYSICAL TRUTH OF THIS FRAME — a real camera could only have captured it "
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
    "- The driver's seat is on the side this scene's country drives on: the "
    "right-hand seat where traffic keeps left (India, the UK, Japan, "
    "Australia), the left-hand seat where traffic keeps right. Pedals, "
    "mirror and gear lever follow that same layout.\n"
    "- The driver's seat is the one nearest the centre of the road, so "
    "oncoming vehicles pass on the DRIVER'S side of the windshield, facing "
    "the camera, while the kerb, parked vehicles, shopfronts and pedestrians "
    "run along the passenger's side.\n"
    "- Everyone in the cabin is in a seat, upright against the seat back, at "
    "the height that seat really puts them — no one floats between seats or "
    "sits taller than the roof allows. Anyone at the frame edge is a whole "
    "person in a real seat, not a stray head or shoulder with no body.\n"
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


# Chapter 1 only — no previous scene exists yet, so this frame establishes the
# grade and optical language every later chapter is held to.
FIRST_IMAGE_SYSTEM_PROMPT = (
    "You are a master cinematographer capturing a high-resolution 35mm film "
    "still of a dramatic story hook.\n\n"
    f"{CINEMATIC_STYLE}\n\n"
    "REFERENCE HANDLING:\n"
    "- Attached portraits are reference for facial features, bone structure "
    "and physical identity only.\n"
    "- Their studio lighting, plain backdrop, neutral clothing and "
    "straight-to-camera pose all stay behind: render each subject fully "
    "integrated into this scene's dramatic environmental light, wearing "
    "exactly what the WEARING section specifies, and turned into the action "
    "at whatever head angle their ACTION line demands.\n\n"
    "Establish the precise colour grade, contrast ratio and film texture here "
    "— this frame locks the look for every chapter that follows."
)

# Chapter 2+ — receives two different kinds of reference image and must treat
# them differently, hence the explicit split below.
CONSISTENCY_IMAGE_SYSTEM_PROMPT = (
    "You are a master cinematographer maintaining strict visual continuity "
    "across a sequential story.\n\n"
    "REFERENCE USAGE:\n"
    "- CHARACTER PORTRAITS: use strictly for facial structural replication — "
    "eyes, nose, jawline, skin tone, hair type, age. Their studio lighting "
    "and default clothing stay behind, and so does the fact that they face "
    "the lens: that frontal framing belongs to the portrait session, not to "
    "this scene. The same face, seen from wherever the action turns it.\n"
    "- PREVIOUS SCENE FRAME: match its optical profile only — colour palette, "
    "contrast curve, lens grain, lighting atmosphere. Its pose, location and "
    "garments belong to that moment, and this is a different one.\n\n"
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

# Appended only on retry, after a first attempt is silently blocked by the
# image model's safety filter (see ImageBlockedError in generate_hook_image.py).
# Not used on the first attempt — most scenes render fine without constraining
# the prompt like this up front.
SAFETY_OVERRIDE_RETRY_ADDENDUM = "\n".join([
    "SAFETY OVERRIDE (RETRY): Render this in a strictly safe, PG-13, ad-friendly way.",
    "No nudity, sexual content, or suggestive body focus.",
    "Do not depict minors/children in vulnerable, harmful, romantic, or sexualized contexts; if age is unclear, portray all people as clearly adult (21+).",
    "No self-harm, suicide, hanging, overdose, abuse, blood, gore, injury, or graphic violence.",
    "Avoid explicit traumatic acts; use symbolic/indirect storytelling instead (emotion, lighting, environment, objects).",
    "Keep the scene respectful, non-graphic, and platform-safe.",
])
