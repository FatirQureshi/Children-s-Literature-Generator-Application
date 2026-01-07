from website.services.shared.llm import generate_image, call_gpt
import json


BOOK_STYLE = """
Soft watercolor children's book illustration.
Bright but gentle colors.
Hand-painted texture.
No photorealism.
Consistent character proportions across pages.
Storybook compositions with clear emotions and readable actions.
"""


# ============================================================
# ILLUSTRATION PLANNING
# ============================================================

def plan_illustrations_from_story(story_text, max_scenes=3):
    """
    Plan key illustration moments from the full story, focusing on narrative beats
    instead of strict paragraph splits.

    Returns a list of scene dicts:
    [
        {
            "scene_id": 1,
            "short_title": "...",
            "full_scene_description": "...",
            "emotional_tone": "...",
            "page_role": "opening | build-up | climax | resolution"
        },
        ...
    ]
    """
    prompt = f"""
You are an experienced children's book illustrator.

TASK:
Read the story below and select up to {max_scenes} key visual moments
that should be illustrated as full-page or half-page children's book illustrations.

For each selected moment:
- Choose a clear narrative beat (not just random sentences).
- Capture the main action, the setting, and the emotional tone.
- Note if the moment is an opening, build-up, climax, or resolution.

STORY:
\"\"\" 
{story_text}
\"\"\"

Return ONLY valid JSON in this format (no extra commentary):
[
  {{
    "scene_id": 1,
    "short_title": "short descriptive title",
    "full_scene_description": "One paragraph describing setting, what is visually happening, what matters in the scene, and important background elements, including 
any secondary characters or objects.",
    "emotional_tone": "e.g. curious, excited, worried, proud",
    "page_role": "opening | build-up | climax | resolution"
  }}
]
"""
    try:
        raw = call_gpt(prompt, temperature=0.3)
        scenes = json.loads(raw)
        if not isinstance(scenes, list):
            raise ValueError("Expected list of scenes")
        return scenes[:max_scenes]
    except Exception:
        # Fallback: simple paragraph-based slicing if planning fails
        return fallback_extract_story_scenes(story_text, max_scenes=max_scenes)


def fallback_extract_story_scenes(story_text, max_scenes=3):
    """
    Fallback: simple paragraph-based scene extraction.
    One paragraph = one image, filtered to substantive paragraphs.
    """
    paragraphs = [
        p.strip() for p in story_text.split("\n\n")
        if len(p.strip()) > 30 and "The End" not in p
    ]
    scenes = []
    for i, p in enumerate(paragraphs[:max_scenes], start=1):
        scenes.append({
            "scene_id": i,
            "short_title": f"Scene {i}",
            "full_scene_description": p,
            "emotional_tone": "gentle",
            "page_role": "build-up"
        })
    return scenes


# ============================================================
# SCENE SUMMARIZATION (RICH, NOT ONE-ACTION-ONLY)
# ============================================================

def summarize_scene_for_illustration(scene_description, max_words=60):
    """
    Turn a full scene description into a compact but rich visual brief.

    Keeps:
    - Main character's action
    - Important background / setting elements
    - Emotional tone
    - Any important secondary characters or objects

    Avoids:
    - Long narration
    - Multiple sequential actions
    """
    prompt = f"""
You are helping an illustrator create a single, rich image for a children's book.

TASK:
Summarize the following scene description into a single vivid visual moment
for an illustration. Include:
- the main character's visible action and pose,
- the setting and key background elements,
- the emotional tone (how the character looks/feels),
- other characters or important objects if they matter visually.

Use at most {max_words} words.
Write it as a visual description, not a sentence from the story.

SCENE DESCRIPTION:
{scene_description}

Output (one paragraph):
"""
    try:
        return call_gpt(prompt, temperature=0.3).strip()
    except Exception:
        # Fallback: truncate
        return scene_description[:max_words * 6]


# ============================================================
# CHARACTER DESCRIPTION BUILDER
# ============================================================

def build_character_description(character_profile):
    """
    Build a stable, reusable character description string from character_profile.

    Handles optional age text and visual_identity safely.
    """
    visual = character_profile.get("visual_identity", {}) or {}

    # Age may be text like "7-9" or "8 years old"
    age_text = (
        character_profile.get("age_range")
        or character_profile.get("age_descriptor")
        or ""
    )
    age_phrase = f"age {age_text}, " if age_text else ""

    name = character_profile.get("name", "Child")

    desc = (
        f"{name}, {age_phrase}"
        f"{visual.get('skin_tone', 'light brown')} skin, "
        f"{visual.get('hair_description', '').strip()} "
        f"({visual.get('hairstyle', '').strip()}), "
        f"wearing {visual.get('clothing_description', 'simple, comfortable clothing')}."
    )

    # Clean up extra spaces and parentheses
    desc = " ".join(desc.split())
    desc = desc.replace("( )", "").replace("()", "").strip()
    return desc


# ============================================================
# MAIN PUBLIC FUNCTION
# ============================================================

def generate_images_from_story(story_text, character_profile):
    """
    Generate narrative-following images for a children's story.

    - Uses a beat-based illustration plan rather than 1 paragraph = 1 image.
    - Each prompt is a rich scene composition: action, setting, emotion, context.
    - Character remains visually consistent via a stable description.
    """

    # 1. Plan the key illustration scenes from the whole story
    scenes = plan_illustrations_from_story(story_text)

    images = []
    character_desc = build_character_description(character_profile)

    for scene in scenes:
        # Scene is expected to have:
        # - full_scene_description
        # - emotional_tone
        # - page_role
        full_desc = scene.get("full_scene_description", "")
        emotional_tone = scene.get("emotional_tone", "").strip()
        page_role = scene.get("page_role", "").strip()

        # 2. Summarize to a concise but rich visual brief
        visual_brief = summarize_scene_for_illustration(full_desc)

        # 3. Build the final image prompt
        role_line = f"This illustration shows a key {page_role} moment in the story." if page_role else ""
        emotion_line = (
            f"The overall emotional tone is {emotional_tone}, "
            f"clearly visible in the character's expression and body language."
            if emotional_tone else
            "Show clear emotions in the character's expression and body language."
        )

        prompt = f"""
CHILDREN'S BOOK ILLUSTRATION

ROLE:
{role_line}

CHARACTER (must remain visually consistent across all images):
{character_desc}

SCENE TO ILLUSTRATE:
{visual_brief}

EMOTION AND STORYTELLING:
{emotion_line}

STYLE:
{BOOK_STYLE}

RULES:
- Focus on the main character as the clear focal point.
- You may include other characters, animals, or objects if they are implied by the scene.
- Show a single, coherent moment (not a comic strip, not multiple panels).
- No speech bubbles, no written text, no interface elements, no diagrams.
- Composition should feel like a full-page children's book illustration, not a rough storyboard frame.
"""
        try:
            img_url = generate_image(prompt)
            images.append(img_url or "/static/fallback_image.png")
        except Exception:
            images.append("/static/fallback_image.png")

    return images

