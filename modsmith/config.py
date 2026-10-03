"""ModSmith global configuration: centralized version numbers and defaults."""

# ============================================================
# Target Minecraft version configuration
# Change only here when upgrading
# ============================================================

MINECRAFT_VERSION = "26.1.2"
FABRIC_LOADER_VERSION = "0.19.5"
LOOM_VERSION = "1.17-SNAPSHOT"
FABRIC_API_VERSION = "0.155.2+26.1.2"
JAVA_VERSION = 25

# ============================================================
# Default mod metadata
# ============================================================

DEFAULT_MOD_VERSION = "0.1.0"
DEFAULT_AUTHOR = "ModSmith User"
DEFAULT_DESCRIPTION = "A ModSmith generated mod"


def default_context() -> dict:
    """Return the default context (version-related fields) for template rendering.

    These values are overridden by fields of the same name in the blueprint,
    but if the blueprint does not provide them, the defaults here are used.
    """
    return {
        "minecraft_version": MINECRAFT_VERSION,
        "fabric_loader_version": FABRIC_LOADER_VERSION,
        "loom_version": LOOM_VERSION,
        "fabric_api_version": FABRIC_API_VERSION,
        "mod_version": DEFAULT_MOD_VERSION,
        "author": DEFAULT_AUTHOR,
        "mod_description": DEFAULT_DESCRIPTION,
    }