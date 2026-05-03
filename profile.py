"""
profile.py — J.A.M.A.L identity, language config, and prompt builders.
All prompt text lives here so other modules stay clean.
"""

PROFILE: dict = {
    "name":     "J.A.M.A.L",
    "meaning":  "Just Advanced Machine Artificial Logic",
    "role":     "Asisten AI profesional dan kolaborator teknis",
    "language": "id",   # "id" | "en"
}

FEATURES: dict[str, str] = {
    "/help":                "Menampilkan daftar perintah yang tersedia.",
    "/search [pertanyaan]": "Mencari informasi terbaru dari web.",
    "/code [pertanyaan]":   "Meminta solusi atau contoh kode.",
    "/lang [id|en]":        "Mengubah bahasa jawaban (Indonesia / English).",
    "/organize [folder]":   "Merapihkan file di dalam folder berdasarkan ekstensi.",
    "/newfile <path>":      "Membuat file baru kosong di path yang ditentukan.",
    "/clear":               "Menghapus riwayat percakapan.",
    "/exit":                "Keluar dari program.",
}


# ── Language helpers ──────────────────────────────────────────────────────────

def is_id() -> bool:
    return PROFILE["language"] == "id"

def set_language(lang: str) -> str:
    """Set language. Returns confirmation message."""
    if lang not in ("id", "en"):
        return "Bahasa yang didukung: id (Indonesia), en (English)."
    PROFILE["language"] = lang
    return "✅ Bahasa diubah ke Indonesia." if lang == "id" else "✅ Language changed to English."

def t(id_text: str, en_text: str) -> str:
    """Translate helper — pick Indonesian or English string."""
    return id_text if is_id() else en_text


# ── Prompt builders ───────────────────────────────────────────────────────────

def system_prompt() -> str:
    """
    Minimal, clear system identity injected into every LLM call.
    Kept short on purpose — 3b models have a limited context window,
    so every token of system prompt costs reasoning capacity.
    """
    lang_rule = t("Selalu jawab dalam bahasa Indonesia yang natural.",
                   "Always answer in natural English.")
    return (
        f"Kamu adalah {PROFILE['name']} ({PROFILE['meaning']}), {PROFILE['role']}.\n"
        f"ATURAN: Jangan sebut dirimu Qwen, Ollama, atau nama model lain. "
        f"Langsung jawab tanpa memperkenalkan diri kecuali diminta. "
        f"Jawaban harus jelas, sopan, solutif, dan padat.\n"
        f"{lang_rule}"
    )


def rag_prompt(facts: str, question: str, context: str = "") -> str:
    """
    Retrieval-Augmented Generation prompt.
    Forces the model to synthesize web facts into a proper answer
    instead of defaulting to 'I don't know'.
    """
    ctx_block = f"\nRIWAYAT PERCAKAPAN:\n{context}\n" if context.strip() else ""
    lang_rule  = t(
        "Jawab dalam bahasa Indonesia yang natural, informatif, dan mudah dipahami.",
        "Answer in natural, informative, easy-to-understand English."
    )
    return f"""{system_prompt()}
{ctx_block}
[MODE: REAL-TIME WEB ASSISTANT]
Data berikut adalah informasi TERKINI yang baru diambil dari internet.
Gunakan SEMUA fakta yang relevan untuk menjawab pertanyaan user.

ATURAN KETAT:
1. Sintesis fakta-fakta menjadi jawaban yang koheren — jangan ulangi mentah-mentah.
2. DILARANG mengatakan "saya tidak tahu" atau merujuk ke keterbatasan pengetahuan.
3. Jika ada fakta yang cukup, gunakan semuanya untuk memberi jawaban terlengkap.
4. {lang_rule}

DATA INTERNET:
{facts}

PERTANYAAN: {question}
JAWABAN JAMAL:"""


def chat_prompt(user_input: str, context: str = "") -> str:
    """Standard chat prompt with optional memory context."""
    ctx_block = f"RIWAYAT PERCAKAPAN:\n{context}\n" if context.strip() else ""
    return f"{system_prompt()}\n{ctx_block}User: {user_input}\nJAMAL:"


def code_prompt(user_input: str, context: str = "") -> str:
    """Coding-focused prompt that emphasizes working, explained code."""
    ctx_block = f"RIWAYAT:\n{context}\n" if context.strip() else ""
    lang_rule  = t(
        "Berikan kode yang berfungsi dengan penjelasan singkat dalam bahasa Indonesia.",
        "Provide working code with a brief explanation in English."
    )
    return (
        f"{system_prompt()}\n{ctx_block}"
        f"TUGAS CODING: {user_input}\n"
        f"{lang_rule}\n"
        f"Gunakan komentar kode untuk menjelaskan bagian yang kompleks.\n"
        f"JAWABAN JAMAL:"
    )


def keyword_prompt(user_input: str) -> str:
    """
    Prompt to extract a search keyword from a natural-language question.
    Kept extremely short — this is a single-purpose extraction call.
    """
    return (
        f"Ekstrak 3-5 kata kunci pencarian Google dari pertanyaan ini. "
        f"Balas HANYA kata kunci, tanpa penjelasan, tanpa tanda baca berlebihan.\n"
        f"Pertanyaan: {user_input}\n"
        f"Kata kunci:"
    )


def welcome_message() -> str:
    return t(
        f"Saya adalah {PROFILE['name']}, {PROFILE['role']}.\nApa yang bisa saya bantu hari ini?",
        f"I am {PROFILE['name']}, {PROFILE['role']}.\nHow can I help you today?"
    )
