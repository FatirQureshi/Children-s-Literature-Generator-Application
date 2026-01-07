from datetime import datetime
from website.services.model_b.validation import validate_story
from website.services.model_b.story_plan import generate_story_plan
from website.services.model_b.story_generation import generate_story
from website.services.model_b.character_profile import generate_character_profile
from website.services.model_b.image_generation import generate_images_from_story
from website.services.model_b.cultural_profile import build_cultural_profile


def run_model_b(user_input, user_metadata, cluster_context):
    """
    Model B: Narrative-grounded children's book generator.
    Images are generated ONLY from validated story text.
    """

    print("\n" + "=" * 60)
    print("📘 MODEL B: Story-first, image-grounded generation")
    print("=" * 60)

    # -----------------------------
    # 1. Normalize traits
    # -----------------------------
    traits = user_input.get("traits", [])
    if isinstance(traits, str):
        traits = [t.strip() for t in traits.split(",") if t.strip()]
    if not traits:
        traits = ["curious", "kind"]

    user_input["traits"] = traits

    # -----------------------------
    # 2. Cultural profile (TEXT-ONLY)
    # -----------------------------
    cultural_profile = build_cultural_profile(
        user_metadata=user_metadata,
        cluster_context=cluster_context
    )

    # -----------------------------
    # 3. Story plan (internal scaffold)
    # -----------------------------
    story_plan = generate_story_plan(
        user_input=user_input,
        cultural_profile=cultural_profile
    )

    # -----------------------------
    # 4. Character profile (canonical)
    # -----------------------------
    character_profile = generate_character_profile(
        character_name=user_input.get("character_name", "Child"),
        age_range=user_input.get("age_range", "7-9"),
        character_type=user_input.get("character_type", "human"),
        character_gender=user_input.get("character_gender", "unspecified"),
        traits=traits,
        cultural_profile=cultural_profile
    )

    # -----------------------------
    # 5. Story generation
    # -----------------------------
    story_text = generate_story(
        story_plan=story_plan,
        cultural_profile=cultural_profile
    )

    # -----------------------------
    # 6. Validation & polish
    # -----------------------------
    story_text = validate_story(
        story_text=story_text,
        cultural_profile=cultural_profile
    )

    if not story_text.strip().endswith("The End."):
        story_text = story_text.rstrip() + "\n\nThe End."

    # -----------------------------
    # 7. Image generation (STORY → IMAGE)
    # -----------------------------
    images = generate_images_from_story(
        story_text=story_text,
        character_profile=character_profile
    )

    print("✨ Model B completed successfully\n")

    return {
        "story_text": story_text,
        "images": images,
        "character_profile": character_profile,
        "metadata": {
            "model": "B",
            "traits": traits,
            "timestamp": datetime.now().isoformat()
        }
    }
