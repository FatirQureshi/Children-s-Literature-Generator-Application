from datetime import datetime
from typing import Dict, List
import json

from website.services.shared.llm import call_gpt
from website.services.model_b.validation import validate_story
from website.services.model_b.story_plan import generate_story_plan
from website.services.model_b.story_generation import generate_story
from website.services.model_b.character_profile import generate_character_profile
from website.services.model_b.cultural_profile import build_cultural_profile
from website.services.model_b.image_generation import generate_images_from_story


# ============================================================
# CULTURAL INTELLIGENCE ENGINE (TEXT-ONLY, NO VISUAL LEAKAGE)
# ============================================================

class CulturalIntelligenceEngine:
    """
    Cultural and trait-aware guidance engine.
    Produces narrative guidance ONLY — never used for images.
    """

    def __init__(self):
        self.cultural_principles = {
            "inclusive_storytelling": [
                "Show authentic cultural elements",
                "Focus on individual lived experiences",
                "Include positive representation",
                "Avoid stereotypes or symbolism",
                "Express personality traits through actions"
            ]
        }

    def analyze_cultural_context(
        self,
        user_input: Dict,
        user_metadata: Dict
    ) -> Dict:
        """
        Returns narrative guidance for story generation.
        """

        traits = user_input.get("traits", [])
        traits_text = ", ".join(traits) if traits else "kind, curious"

        prompt = f"""
Analyze this children's story request for culturally inclusive storytelling.

CHARACTER:
- Name: {user_input.get("character_name", "Child")}
- Age range: {user_input.get("age_range", "7-9")}
- Gender: {user_input.get("character_gender", "unspecified")}
- Type: {user_input.get("character_type", "human")}
- Personality traits: {traits_text}

STORY SETTING:
- Location: {user_input.get("location", "")}
- Theme: {user_input.get("theme", "adventure")}

CULTURAL CONTEXT:
- Cultural background: {user_metadata.get("cultural_background", "")}
- Region: {user_metadata.get("region", "")}

TASK:
Provide narrative guidance only.
DO NOT describe visuals or images.

Return valid JSON only in this format:
{{
  "cultural_themes": [],
  "authentic_details": [],
  "trait_expression": [],
  "age_appropriate": []
}}
"""

        try:
            response = call_gpt(prompt, temperature=0.3)
            return json.loads(response)
        except Exception:
            return {
                "cultural_themes": ["friendship", "community"],
                "authentic_details": ["family interactions", "daily routines"],
                "trait_expression": ["traits shown through choices"],
                "age_appropriate": ["simple language", "positive tone"]
            }


# ============================================================
# MODEL B — STORY-FIRST PIPELINE
# ============================================================

def run_model_b(
    user_input: Dict,
    user_metadata: Dict,
    cluster_context: Dict
) -> Dict:
    """
    Model B pipeline:
    - Text-first
    - Narrative-grounded
    - Image generation ONLY from validated story text
    """

    print("\n" + "=" * 60)
    print("📘 MODEL B — STORY-GROUNDED GENERATION")
    print("=" * 60)

    try:
        # ----------------------------------------------------
        # 1. Normalize personality traits
        # ----------------------------------------------------
        traits = user_input.get("traits", [])

        if isinstance(traits, str):
            traits = [t.strip() for t in traits.split(",") if t.strip()]
        elif not isinstance(traits, list):
            traits = []

        if not traits:
            traits = ["curious", "kind"]

        user_input["traits"] = traits

        print(f"🧠 Traits locked: {traits}")

        # ----------------------------------------------------
        # 2. Cultural analysis (TEXT ONLY)
        # ----------------------------------------------------
        cultural_engine = CulturalIntelligenceEngine()
        cultural_analysis = cultural_engine.analyze_cultural_context(
            user_input=user_input,
            user_metadata=user_metadata
        )

        # ----------------------------------------------------
        # 3. Build cultural profile (no visual info)
        # ----------------------------------------------------
        cultural_profile = build_cultural_profile(
            user_metadata=user_metadata,
            cluster_context=cluster_context
        )

        cultural_profile["cultural_analysis"] = cultural_analysis
        cultural_profile["principles"] = cultural_engine.cultural_principles

        # ----------------------------------------------------
        # 4. Story plan (internal scaffold ONLY)
        # ----------------------------------------------------
        print("📖 Generating story plan...")
        story_plan = generate_story_plan(
            user_input=user_input,
            cultural_profile=cultural_profile
        )

        # ----------------------------------------------------
        # 5. Canonical character profile (visual anchor)
        # ----------------------------------------------------
        print("👤 Generating character profile...")
        character_profile = generate_character_profile(
            character_name=user_input.get("character_name", "Child"),
            age_range=user_input.get("age_range", "7-9"),
            character_type=user_input.get("character_type", "human"),
            character_gender=user_input.get("character_gender", "unspecified"),
            traits=traits,
            cultural_profile=cultural_profile
        )

        # ----------------------------------------------------
        # 6. Story generation
        # ----------------------------------------------------
        print("✍️ Writing story...")
        story_text = generate_story(
            story_plan=story_plan,
            cultural_profile=cultural_profile
        )

        # ----------------------------------------------------
        # 7. Validation & polish
        # ----------------------------------------------------
        print("🛡️ Validating story...")
        story_text = validate_story(
            story_text=story_text,
            cultural_profile=cultural_profile
        )

        if not story_text.strip().endswith("The End."):
            story_text = story_text.rstrip() + "\n\nThe End."

        # ----------------------------------------------------
        # 8. Image generation (STORY → IMAGE ONLY)
        # ----------------------------------------------------
        print("🎨 Generating images from story text...")
        images = generate_images_from_story(
            story_text=story_text,
            character_profile=character_profile
        )

        print("✨ MODEL B COMPLETED SUCCESSFULLY\n")

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

    except Exception as e:
        print(f"❌ MODEL B FAILURE: {e}")
        import traceback
        traceback.print_exc()
        raise
