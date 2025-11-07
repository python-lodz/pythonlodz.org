from pyldz.models import Language

TRANSLATIONS = {
    Language.PL: {
        "invites": "ZAPRASZA",
        "tba": "TBA",
    },
    Language.EN: {
        "invites": "INVITES",
        "tba": "TBA",
    },
}


def get_text(language: Language, key: str) -> str:
    """
    Get translated text for the given language and key.

    Args:
        language: Target language (PL or EN)
        key: Translation key

    Returns:
        Translated text or the key itself if translation not found
    """
    return TRANSLATIONS.get(language, {}).get(key, key)
