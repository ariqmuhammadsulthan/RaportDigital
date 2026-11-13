"""Presentation presets; storage IDs and progression stay in domain.py."""
import json
import os
from pathlib import Path

from .domain import CLASSES


def profiles(education="school", names=None):
    if education not in ("school", "equivalency"):
        raise ValueError("RAPOR_EDUCATION must be school or equivalency.")
    names = {} if names is None else names
    if (not isinstance(names, dict) or names.keys() - CLASSES.keys()
            or any(not isinstance(n, str) or not n.strip() or len(n) > 120 for n in names.values())):
        raise ValueError("Program names must map known IDs to nonempty strings (maximum 120 characters).")
    equivalent = education == "equivalency"
    labels = ("Paket A", "Paket B", "Paket C IPA", "Paket C IPS") if equivalent else ("SD", "SMP", "SMA IPA", "SMA IPS")
    covers = ("PROGRAM PAKET A SETARA SD", "PROGRAM PAKET B SETARA SMP", "PROGRAM PAKET C SETARA SMA", "PROGRAM PAKET C SETARA SMA")
    return {
        code: {
            "name": names.get(code, label).strip(),
            "cover": names[code].strip() if code in names else (covers[i] if equivalent else label),
            "track": (" MIA" if code == "c-ipa" else " IIS") if equivalent and code.startswith("c-") else "",
            "equivalency": equivalent,
        }
        for i, (code, label) in enumerate(zip(CLASSES, labels))
    }


def configured_profiles(education=None, names=None):
    if names is None and (path := os.environ.get("RAPOR_PROGRAM_NAMES")):
        names = json.loads(Path(path).expanduser().read_text(encoding="utf-8-sig"))
        if not isinstance(names, dict):
            raise ValueError("RAPOR_PROGRAM_NAMES must contain a JSON object of program names.")
    return profiles(education if education is not None else os.environ.get("RAPOR_EDUCATION", "school"), names)


def issued_profile(state, program):
    # Archives predating presets were all rendered as equivalency reports.
    return state.get("reportProfile") or {**profiles("equivalency")[program], "legacy": True}
