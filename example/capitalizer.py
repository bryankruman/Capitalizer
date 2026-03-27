import argparse
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Optional


ROOT_DIR = Path(__file__).resolve().parent
DICT_PATH = ROOT_DIR / "en_US.dic"


@lru_cache(maxsize=1)
def _load_dictionary() -> frozenset[str]:
    """
    Load the base word list from the Hunspell .dic file.

    The .dic format puts the word count on the first line, followed by
    one word per line, optionally suffixed with "/FLAGS". We only care
    about the base word before the slash.
    """
    words: set[str] = set()

    try:
        with DICT_PATH.open("r", encoding="utf-8") as f:
            first = f.readline()
            # Remaining lines are entries of the form WORD[/FLAGS]
            for line in f:
                line = line.strip()
                if not line:
                    continue
                base = line.split("/", 1)[0]
                if base:
                    words.add(base.lower())
    except FileNotFoundError:
        # In tests or environments without the dictionary file present,
        # fail fast with a clear error.
        raise RuntimeError(f"Dictionary file not found at {DICT_PATH}")

    return frozenset(words)


def _segment_into_words(token: str, dictionary: Iterable[str]) -> Optional[List[str]]:
    """
    Try to segment the lowercase token into known dictionary words.

    Returns a list of substrings covering the full token if possible,
    otherwise None. Among all valid segmentations we prefer the one
    with the *fewest* words so that a single-word dictionary match like
    "quicksilver" wins over ["quick", "silver"].
    """
    word_set = set(dictionary)
    n = len(token)
    dp: List[Optional[List[str]]] = [None] * (n + 1)
    dp[n] = []

    for i in range(n - 1, -1, -1):
        best: Optional[List[str]] = None
        for j in range(i + 1, n + 1):
            piece = token[i:j]
            if piece in word_set and dp[j] is not None:
                candidate = [piece] + dp[j]
                if best is None or len(candidate) < len(best):
                    best = candidate
        dp[i] = best

    return dp[0]


def capitalize_name(raw: str) -> str:
    """
    Capitalize a brand or domain-like name by detecting embedded English words.

    - If the core token (before any '.') is itself a dictionary word,
      we simply capitalize its first letter, e.g. "quicksilver" -> "Quicksilver".
    - Otherwise, we try to split the token into a sequence of dictionary
      words and capitalize each, e.g. "darkstoneforge" -> "DarkStoneForge".
    - If no segmentation is possible, we fall back to simple title-casing
      the token, e.g. "packora" -> "Packora".
    - Any trailing extension like ".com" or ".org" is preserved as-is.
    """
    if not raw:
        return raw

    dictionary = _load_dictionary()

    # Split off a simple extension (e.g. ".com", ".org") if present.
    core, dot, ext = raw.partition(".")
    core_lower = core.lower()

    # If the whole core is a known word, prefer treating it as a single word.
    if core_lower in dictionary:
        capitalized_core = core_lower.capitalize()
        return capitalized_core + (dot + ext if dot else "")

    # Otherwise attempt segmentation.
    segments = _segment_into_words(core_lower, dictionary)
    if segments and len(segments) >= 2 and all(len(seg) >= 4 for seg in segments):
        capitalized_core = "".join(seg.capitalize() for seg in segments)
    else:
        # Fallback: just title-case the core token to avoid over-segmentation
        # for coined or short-brand names like "packora" or "savvio".
        capitalized_core = core_lower.capitalize()

    return capitalized_core + (dot + ext if dot else "")


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Capitalize brand and domain names by detecting embedded "
            "English dictionary words."
        )
    )
    parser.add_argument(
        "names",
        nargs="+",
        help="Space-separated brand or domain names to capitalize.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = _parse_args(argv)
    for name in args.names:
        print(capitalize_name(name))


if __name__ == "__main__":
    main()

