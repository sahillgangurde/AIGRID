"""
Anonymous Alias Generator — Hypear AI v2.0.

Generates professional, memorable codenames for creators operating anonymously.
Examples: "Studio Phantom", "Archive Collective", "Mosaic Signal", "Prism Works"

Design Rules:
  - Two-word combinations: [Adjective] + [Noun]
  - Professional, industry-adjacent vocabulary
  - No random numbers in the base alias (cleaner UX)
  - Numeric suffix (#xxx) only as last-resort fallback
  - Uniqueness enforced against the 'profiles' table
  - 30-day cooldown before regeneration (enforced by router)

Usage:
    from server.services.alias_generator import AliasGenerator
    alias = AliasGenerator.generate_unique(db)
"""

import random
import logging

logger = logging.getLogger(__name__)

# ── Word Banks ────────────────────────────────────────────────

ADJECTIVES = [
    # Studio / Production language
    "Studio", "Archive", "Frame", "Mosaic", "Prism", "Signal",
    "Cipher", "Canvas", "Layer", "Render", "Vector", "Sequence",
    # Evocative / Aesthetic
    "Lucid", "Vortex", "Apex", "Ghost", "Nova", "Dusk", "Ember",
    "Atlas", "Zenith", "Solar", "Onyx", "Sage", "Flux", "Lumen",
    "Null", "Axon", "Orbit", "Quartz", "Slate", "Echo", "Helix",
    # Premium / Luxury
    "Aura", "Veil", "Myth", "Dawn", "Neon", "Frost", "Cobalt",
    "Mire", "Bale", "Arch", "Edge", "Core", "Pure", "Dark",
]

NOUNS = [
    # Production / Creative
    "Phantom", "Collective", "Forge", "Signal", "Lens", "Draft",
    "Render", "Layer", "Node", "Pulse", "Form", "Unit", "Works",
    "Lab", "House", "Studio", "Guild", "Vault", "Stack", "Grid",
    # Evocative
    "Echo", "Shift", "Bloom", "Trace", "Fold", "Weave", "Cast",
    "Line", "Mark", "Tone", "Haze", "Glow", "Rush", "Flow",
    # Tech / Futurism
    "Circuit", "Mesh", "Array", "Core", "Block", "Frame", "Shard",
    "Thread", "Index", "Module", "Kernel", "Matrix", "Loop",
]

# Ensure combinations look good (avoid same word twice)
_BANNED_PAIRS = {("Studio", "Studio"), ("Frame", "Frame"), ("Core", "Core"), ("Echo", "Echo")}


class AliasGenerator:
    """Generates and manages anonymous creator aliases."""

    @staticmethod
    def generate() -> str:
        """Generate a single alias (not guaranteed unique)."""
        for _ in range(20):
            adj = random.choice(ADJECTIVES)
            noun = random.choice(NOUNS)
            if (adj, noun) not in _BANNED_PAIRS and adj != noun:
                return f"{adj} {noun}"
        return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"

    @classmethod
    def generate_unique(cls, db, max_attempts: int = 100) -> str:
        """
        Generate an alias guaranteed to be unique in the database.
        Falls back to alias + numeric suffix after max_attempts.
        """
        from server.db.models import Profile

        for attempt in range(max_attempts):
            alias = cls.generate()
            exists = db.query(Profile).filter(Profile.masked_alias == alias).first()
            if not exists:
                logger.debug(f"Unique alias found after {attempt + 1} attempt(s): '{alias}'")
                return alias

        # Last resort: numeric suffix
        for _ in range(20):
            alias = f"{cls.generate()} #{random.randint(100, 9999)}"
            exists = db.query(Profile).filter(Profile.masked_alias == alias).first()
            if not exists:
                logger.warning(f"Used numeric fallback alias: '{alias}'")
                return alias

        # Should never reach here with 40 total attempts on ~2000+ combinations
        raise RuntimeError("Could not generate a unique alias — alias pool exhausted. Expand word banks.")

    @classmethod
    def assign_to_profile(cls, db, profile_id: str) -> str:
        """
        Generate and assign a unique alias to a profile.
        Returns the assigned alias string.
        """
        from server.db.models import Profile

        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")

        alias = cls.generate_unique(db)
        profile.masked_alias = alias
        db.commit()
        logger.info(f"Alias '{alias}' assigned to profile {profile_id}")
        return alias

    @staticmethod
    def public_name(profile) -> str:
        """
        Return the safe public display name for a profile.
        If anonymous_mode is on → return masked_alias.
        Otherwise → return display_name.
        """
        if profile.anonymous_mode and profile.masked_alias:
            return profile.masked_alias
        return profile.display_name

    @staticmethod
    def total_combinations() -> int:
        """Utility: total unique alias combinations in the word bank."""
        pairs = len(ADJECTIVES) * len(NOUNS)
        banned = len(_BANNED_PAIRS)
        same_word = sum(1 for a in ADJECTIVES if a in NOUNS)
        return pairs - banned - same_word

    get_public_name = public_name


AliasGeneratorService = AliasGenerator

