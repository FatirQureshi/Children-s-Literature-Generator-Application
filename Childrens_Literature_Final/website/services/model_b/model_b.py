from website.services.shared.llm import call_gpt
from website.services.model_b.validation import validate_story

import json
from datetime import datetime
from typing import Dict, List, Any


# ============================================================
# UTILITIES
# ============================================================

def normalize_age_descriptor(age_value: Any) -> str:
    """
    Force age into a TEXT-ONLY descriptor.
    This value is NEVER used numerically — prompt guidance only.
    """
    if isinstance(age_value, str) and age_value.strip():
        return age_value.strip()

    if isinstance(age_value, (int, float)):
        return f"{int(age_value)} years old"

    if isinstance(age_value, dict):
        # Best-effort textualization
        min_age = age_value.get("min")
        max_age = age_value.get("max")
        if min_age and max_age:
            return f"{min_age}-{max_age}"
        if min_age:
            return f"{min_age}+"
        return "7-9"

    return "7-9"


# ============================================================
# CULTURAL INTELLIGENCE ENGINE (TEXT GUIDANCE ONLY)
# ============================================================

class CulturalIntelligenceEngine:
    """
    Cultural intelligence engine.
    Produces TEXTUAL narrative guidance only.
    """

    def __init__(self):
        self.cultural_principles = {
            "inclusive_storytelling": [
                "Show authentic cultural elements",
                "Focus on individual experiences",
                "Include positive representation",
                "Show cultural exchange and sharing",
                "Ensure personality traits are reflected through actions"
            ]
        }

    def analyze_cultural_context(
        self,
        user_input: Dict,
        user_metadata: Dict
    ) -> Dict:
        """
        Cultural analysis with personality traits.
        Age is treated as TEXTUAL GUIDANCE ONLY.
        """

        cultural_background = user_metadata.get("cultural_background", "")
        region = user_metadata.get("region", "")

        traits: List[str] = user_input.get("traits", [])
        traits_text = ", ".join(traits) if traits else "kind, curious"

        age_descriptor = user_input.get("age_descriptor", "7-9")

        prompt = f"""
Analyze this children's story request for culturally inclusive storytelling.

CHARACTER PROFILE:
- Name: {user_input.get("character_name", "Child")}
- Age guidance: {age_descriptor}
- Gender: {user_input.get("character_gender", "unspecified")}
- Personality traits: {traits_text}
- Character type: {user_input.get("character_type", "human")}

STORY CONTEXT:
- Location: {user_input.get("location", "")}
- Theme: {user_input.get("theme", "adventure")}

CULTURAL CONTEXT:
- Cultural background: {cultural_background}
- Region: {region}

TASK:
Provide guidance for creating an authentic, age-appropriate children's story where:
- Age guidance influences language complexity and tone ONLY
- Personality traits influence actions and decisions
- Cultural elements are naturally integrated
- Representation is positive and respectful

Return valid JSON only in this format:
{{
  "cultural_themes": ["themes to highlight"],
  "authentic_details": ["authentic cultural or daily-life details"],
  "trait_expression": ["ways traits should appear in behavior"],
  "age_appropriate": ["language and tone guidance for {age_descriptor} readers"]
}}
"""

        try:
            response = call_gpt(prompt, temperature=0.3)
            return json.loads(response)
        except Exception:
            return {
                "cultural_themes": ["friendship", "community"],
                "authentic_details": ["family interactions", "daily routines"],
                "trait_expression": ["show traits through choices and dialogue"],
                "age_appropriate": ["simple language", "positive messages"]
            }


# ============================================================
# MODEL B PIPELINE (AGE = TEXT FEATURE ONLY)
# ============================================================

def run_model_b(
    user_input: Dict,
    user_metadata: Dict,
    cluster_context: Dict
) -> Dict:
    """
    Model B pipeline with:
    - Text-only age semantics
    - Narrative-first generation
    - No structural interpretation of age
    """

    print("\n" + "=" * 60)
    print("🚀 MODEL B: Cultural + Trait-Aware Generation")
    print("=" * 60)

    try:
        # ----------------------------------------------------
        # 1. Normalize traits
        # ----------------------------------------------------
        traits = user_input.get("traits", [])

        if isinstance(traits, str):
            traits = [t.strip() for t in traits.split(",") if t.strip()]
        elif not isinstance(traits, list):
            traits = []

        if not traits:
            traits = ["curious", "kind"]

        user_input["traits"] = traits
        user_input["traits_text"] = ", ".join(traits)

        print(f"🧠 Traits locked in: {traits}")

        # ----------------------------------------------------
        # 2. Normalize age (TEXT ONLY)
        # ----------------------------------------------------
        user_input["age_descriptor"] = normalize_age_descriptor(
            user_input.get("age_range")
        )

        print(f"🧒 Age guidance: {user_input['age_descriptor']}")

        # ----------------------------------------------------
        # 3. Cultural analysis
        # ----------------------------------------------------
        cultural_engine = CulturalIntelligenceEngine()
        print("🔍 Analyzing cultural + personality context...")

        cultural_analysis = cultural_engine.analyze_cultural_context(
            user_input=user_input,
            user_metadata=user_metadata
        )

        print("   ✓ Cultural analysis completed")

        # ----------------------------------------------------
        # 4. Build cultural profile (TEXT-ONLY AGE)
        # ----------------------------------------------------
        print("📝 Building cultural profile...")

        cultural_profile = {
            "user_context": {
                "background": user_metadata.get("cultural_background", ""),
                "region": user_metadata.get("region", "")
            },
            "story_context": {
                "location": user_input.get("location", ""),
                "theme": user_input.get("theme", "adventure"),
                "character_name": user_input.get("character_name", "Child"),
                "age_descriptor": user_input["age_descriptor"],
                "character_gender": user_input.get("character_gender", "unspecified"),
                "traits": traits
            },
            "cluster_context": cluster_context,
            "cultural_analysis": cultural_analysis,
            "principles": cultural_engine.cultural_principles
        }

        # ----------------------------------------------------
        # 5. Story plan
        # ----------------------------------------------------
        print("📖 Generating story plan...")
        from website.services.model_b.story_plan import generate_story_plan

        story_plan = generate_story_plan(
            user_input=user_input,
            cultural_profile=cultural_profile
        )

        print(f"   ✓ Story plan created: {story_plan.get('title', 'Untitled')}")

        # ----------------------------------------------------
        # 6. Character profile (age as descriptive text only)
        # ----------------------------------------------------
        print("👤 Creating character profile...")
        from website.services.model_b.character_profile import generate_character_profile

        character_profile = generate_character_profile(
            character_name=user_input.get("character_name", "Child"),
            age_range=user_input["age_descriptor"],  # TEXT ONLY
            character_type=user_input.get("character_type", "human"),
            character_gender=user_input.get("character_gender", "unspecified"),
            traits=traits,
            cultural_profile=cultural_profile
        )

        cultural_profile["character_profile"] = character_profile
        print("   ✓ Character profile created")

        # ----------------------------------------------------
        # 7. Story generation
        # ----------------------------------------------------
        print("✍️ Writing story...")
        from website.services.model_b.story_generation import generate_story

        story_text = generate_story(
            story_plan=story_plan,
            cultural_profile=cultural_profile
        )

        print(f"   ✓ Story written ({len(story_text)} chars)")

        # ----------------------------------------------------
        # 8. Validation
        # ----------------------------------------------------
        print("🛡️ Validating story...")

        try:
            story_text = validate_story(
                story_text=story_text,
                cultural_profile=cultural_profile
            )
            print("   ✓ Story validated and polished")
        except Exception as e:
            print(f"   ⚠️ Validation skipped: {e}")

        if not story_text.strip().endswith("The End."):
            story_text = story_text.rstrip() + "\n\nThe End."

        # ----------------------------------------------------
        # 9. Image generation (no age semantics beyond text)
        # ----------------------------------------------------
        print("🎨 Generating images...")
        from website.services.model_b.image_generation import generate_images_from_story

        images = generate_images_from_story(
                story_text=story_text,
          character_profile=character_profile
        )

        print(f"   ✓ Images generated: {len(images)}")
        print("\n✨ MODEL B: Completed successfully!\n")

        return {
            "story_text": story_text,
            "images": images,
            "character_profile": character_profile,
            "cultural_profile": cultural_profile,
            "story_plan": story_plan,
            "metadata": {
                "model": "B",
                "traits": traits,
                "age_descriptor": user_input["age_descriptor"],
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        print(f"❌ Error in Model B: {e}")
        import traceback
        traceback.print_exc()
        raise

