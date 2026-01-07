from website.services.shared.llm import generate_image, call_gpt


BOOK_STYLE = """
Soft watercolor children's book illustration.
Bright but gentle colors.
Hand-painted texture.
No photorealism.
Consistent character proportions across pages.
"""


def extract_story_scenes(story_text, max_scenes=3):
    """
    Split story into illustratable scenes.
    One paragraph = one image.
    """
    paragraphs = [
        p.strip() for p in story_text.split("\n\n")
        if len(p.strip()) > 30 and "The End" not in p
    ]
    return paragraphs[:max_scenes]


def summarize_scene(scene_text, max_words=14):
    """
    Reduce a paragraph to ONE action, ONE pose.
    """
    prompt = f"""
Summarize this children's story paragraph into ONE single action.
Max {max_words} words.
No compound actions.
No transitions.

Paragraph:
{scene_text}

Output:
"""
    return call_gpt(prompt, temperature=0.3).strip()


def generate_images_from_story(story_text, character_profile):
    """
    Generate images grounded strictly in story content.
    """

    scenes = extract_story_scenes(story_text)
    images = []

    visual = character_profile["visual_identity"]

    character_desc = (
        f"{character_profile['name']}, {character_profile['age_range']} years old, "
        f"{visual['skin_tone']} skin, {visual.get('hair_description','')} "
        f"({visual.get('hairstyle','')}), "
        f"wearing {visual['clothing_description']}."
    )

    for idx, scene in enumerate(scenes):
        action = summarize_scene(scene)

        prompt = f"""
CHILDREN'S BOOK ILLUSTRATION

RULES:
- EXACTLY ONE character
- SINGLE POSE
- SINGLE ACTION
- NO text, NO symbols, NO diagrams
- NO metadata representation

CHARACTER:
{character_desc}

SCENE:
{action}

STYLE:
{BOOK_STYLE}
"""

        try:
            img_url = generate_image(prompt)
            images.append(img_url)
        except Exception:
            images.append("/static/fallback_image.png")

    return images
