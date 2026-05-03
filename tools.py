"""
tools.py — File system tools: organize and create.

Safety improvement: /organize now shows a dry-run preview and asks
for confirmation before moving anything — prevents accidental data loss.
"""

from __future__ import annotations
import os
from profile import t


# ── organize_files ────────────────────────────────────────────────────────────

def organize_files(folder_path: str = ".") -> str:
    """
    Group files in a folder into subfolders by extension.
    Shows a preview first and asks for confirmation.
    """
    folder_path = folder_path.strip() or "."

    if not os.path.isdir(folder_path):
        return t(f"❌ Folder tidak ditemukan: '{folder_path}'",
                 f"❌ Folder not found: '{folder_path}'")

    # Build the move plan
    plan: list[tuple[str, str, str]] = []   # (filename, ext, target_folder)
    for entry in os.listdir(folder_path):
        full_path = os.path.join(folder_path, entry)
        if os.path.isfile(full_path):
            ext    = os.path.splitext(entry)[1].lower().lstrip(".") or "lainnya"
            target = os.path.join(folder_path, ext)
            new_path = os.path.join(target, entry)
            if full_path != new_path:
                plan.append((entry, ext, target))

    if not plan:
        return t(f"✅ Tidak ada file yang perlu dirapihkan di '{folder_path}'.",
                 f"✅ No files need organizing in '{folder_path}'.")

    # Show dry-run preview
    print(t("\n📋 RENCANA ORGANISASI FILE:", "\n📋 FILE ORGANIZATION PLAN:"))
    for filename, ext, target in plan:
        print(f"   {filename}  →  {os.path.basename(target)}/")

    confirm = input(t("\n   Lanjutkan? (y/n): ", "\n   Proceed? (y/n): ")).strip().lower()
    if confirm != "y":
        return t("⚠️  Dibatalkan.", "⚠️  Cancelled.")

    # Execute
    moved, errors = [], []
    for filename, ext, target in plan:
        full_path = os.path.join(folder_path, filename)
        new_path  = os.path.join(target, filename)
        try:
            os.makedirs(target, exist_ok=True)
            os.replace(full_path, new_path)
            moved.append(filename)
        except OSError as e:
            errors.append(f"{filename}: {e}")

    lines = [f"✅ {len(moved)} file dipindahkan."]
    if errors:
        lines.append(t("⚠️  Gagal:", "⚠️  Failed:"))
        lines.extend(f"   {e}" for e in errors)
    return "\n".join(lines)


# ── create_file ───────────────────────────────────────────────────────────────

def create_file(file_path: str) -> str:
    """Create an empty file (with a header comment) at the given path."""
    file_path = file_path.strip()
    if not file_path:
        return t("Gunakan: /newfile <path>", "Usage: /newfile <path>")

    dir_part = os.path.dirname(file_path)
    if dir_part:
        os.makedirs(dir_part, exist_ok=True)

    if os.path.exists(file_path):
        return t(f"⚠️  File sudah ada: {file_path}",
                 f"⚠️  File already exists: {file_path}")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# File dibuat oleh J.A.M.A.L\n")
        return t(f"✅ File baru dibuat: {file_path}",
                 f"✅ New file created: {file_path}")
    except OSError as e:
        return t(f"❌ Gagal membuat file: {e}",
                 f"❌ Failed to create file: {e}")
