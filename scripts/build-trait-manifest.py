#!/usr/bin/env python3
"""Scan assets/traits and build traits-manifest.json for the Character Creator."""
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAITS_DIR = ROOT / "assets" / "traits"
MANIFEST_PATH = ROOT / "assets" / "traits-manifest.json"
BASE_PATH = "assets/traits"

FOLDER_TO_SLOT = {
    "BACKGROUNDS": "background",
    "BG BLUR": "backgroundblur",
    "BEHINDBACK": "behindback",
    "SKIN": "skin",
    "EYES": "eyes",
    "MOUTH": "mouth",
    "CLOTHING": "clothing",
    "HAIR": "hair",
    "GLASSES": "accessories",
    "HATS": "hat",
    "HOODIES": "hoodies",
    "ABOVE HEAD": "goo",
    "OPEN HAND": "hand",
    "CLOSED HAND": "hand2",
    "OPEN H ITEMS": "ball",
    "CLOSED H ITEM": "ball2",
}

SKIN_KEYWORDS = [
    "TAN", "LIGHT", "DARK", "BROWN", "PALE", "BLACK",
    "GINGER", "BLONDE", "WHITE", "CHROME",
]

SKIP_DIRS = {"ARCHIVED", ".DS_Store", "__MACOSX"}
SKIP_FILE_PATTERNS = re.compile(r"^\.|\.ds_store$", re.I)


def clean_folder_name(name: str) -> str:
    return re.sub(r"\s*[✅❌]\s*$", "", name).strip()


def trait_name_from_file(filename: str) -> str:
    name = filename
    for ext in (".png", ".PNG", ".Png"):
        if name.endswith(ext):
            name = name[: -len(ext)]
            break
    name = name.replace("_", " ")
    return " ".join(name.split())


def normalized_name(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def extract_skin_tone(text: str):
    upper = text.upper()
    for kw in SKIN_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", upper):
            return kw.title() if kw != "BLACK" else "Black"
    return None


def extract_variant_group(trait_name: str, slot: str):
    if slot not in ("ball", "ball2", "hand", "hand2"):
        return None
    for prefix in ("Baseball Bat", "Hockey Stick", "Microphone"):
        if trait_name.startswith(prefix):
            return prefix
    return None


def is_remove_trait(trait_name: str, filename: str) -> bool:
    u = (trait_name + " " + filename).upper()
    return "NO HAND" in u or trait_name.upper() in ("REMOVE", "NONE", "CLEAR")


def build_manifest():
    traits = []
    if not TRAITS_DIR.is_dir():
        raise SystemExit(f"Missing traits directory: {TRAITS_DIR}")

    for folder in sorted(TRAITS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        category = folder.name
        slot = FOLDER_TO_SLOT.get(category)
        if not slot:
            print(f"  skip unknown folder: {category}")
            continue

        for dirpath, dirnames, filenames in os.walk(folder):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not SKIP_FILE_PATTERNS.search(d)]
            if "ARCHIVED" in Path(dirpath).parts:
                continue
            for filename in filenames:
                if SKIP_FILE_PATTERNS.search(filename):
                    continue
                if not filename.lower().endswith(".png"):
                    continue
                rel = Path(dirpath).relative_to(TRAITS_DIR) / filename
                path = f"{BASE_PATH}/{rel.as_posix()}"
                trait_name = trait_name_from_file(filename)
                skin_tone = extract_skin_tone(trait_name)
                if slot in ("hand", "hand2") and " - " in trait_name:
                    part = trait_name.split(" - ", 1)[-1].strip()
                    skin_tone = extract_skin_tone(part) or skin_tone
                entry = {
                    "category": category,
                    "slot": slot,
                    "file": filename,
                    "path": path,
                    "traitName": trait_name,
                    "normalizedName": normalized_name(trait_name),
                    "variantGroup": extract_variant_group(trait_name, slot),
                    "skinTone": skin_tone,
                    "gender": "Unisex",
                    "isRemove": is_remove_trait(trait_name, filename),
                }
                traits.append(entry)

    manifest = {
        "version": 1,
        "generatedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "basePath": BASE_PATH,
        "traits": traits,
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {len(traits)} traits to {MANIFEST_PATH}")


if __name__ == "__main__":
    build_manifest()
