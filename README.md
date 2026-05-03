# J.A.M.A.L
### Just Advanced Machine Artificial Logic

> A local AI agent powered by Ollama — with real-time web search, smart memory, streaming output, and file tools. Runs fully offline on a 3B model.

---

## Features

- **Real-time web search** — auto-detects when a question needs live data and searches DuckDuckGo with retry logic and fallback queries
- **Streaming output** — responses print cleanly as they generate, no frozen terminal
- **Smart memory** — conversation history is compressed (not just dropped) when the buffer fills, so early context isn't lost
- **File tools** — organize files by extension with a dry-run preview, or create new files from the terminal
- **Bilingual** — switch between Indonesian and English at any time with `/lang`
- **Modular codebase** — split into focused modules, easy to extend or swap components

---

## Project Structure

```
jamal/
├── agent.py      # Entry point — main loop & command routing
├── profile.py    # AI identity, prompt builders, language config
├── memory.py     # Conversation history with smart compression
├── llm.py        # LLM instance, streaming, response generators
├── search.py     # Web search pipeline (DuckDuckGo + retry logic)
├── tools.py      # File tools: organize & newfile
└── ui.py         # Terminal UI: styled boxes, prompts, streaming
```

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) running locally

---

## Installation

**1. Clone the repo**
```bash
git clone https://github.com/yourusername/jamal.git
cd jamal
```

**2. Install Python dependencies**
```bash
pip install -r requirements.txt
```

**3. Pull the model**
```bash
ollama pull qwen2.5-coder:3b
```

**4. Run**
```bash
python agent.py
```

---

## Commands

| Command | Description |
|---|---|
| `/search <question>` | Search the web for real-time information |
| `/code <question>` | Ask for a code solution |
| `/organize [folder]` | Sort files in a folder by extension (shows preview first) |
| `/newfile <path>` | Create a new empty file at the given path |
| `/lang id\|en` | Switch response language |
| `/clear` | Wipe conversation history |
| `/help` | Show command list |
| `exit` | Quit |

---

## How It Works

### Web Search
When you ask something, JAMAL first checks a keyword heuristic list (`terbaru`, `berita`, `harga`, `gempa`, `today`, `latest`, etc.). If it matches, web search fires immediately — no extra LLM round-trip. For ambiguous queries, a lightweight classifier call decides. Searches retry automatically with a simplified query if the first attempt returns thin results.

### Memory Compression
The conversation buffer holds up to 12 turns. When it fills up, the oldest turns are summarized into a compact paragraph by the LLM and stored as a rolling summary — so context from early in the conversation is never completely lost.

### Streaming
Responses are buffered silently while a progress indicator (`....`) shows the terminal isn't frozen. Once the full response is ready, it prints cleanly line by line — no extra blank lines between numbered lists or paragraphs.

---

## Configuration

To change the model, edit `llm.py`:
```python
_llm = OllamaLLM(model="qwen2.5-coder:3b", temperature=0.2)
```

Any model available in Ollama works. Larger models (7B+) will give noticeably better reasoning and web synthesis.

---

## Dependencies

```
langchain-ollama>=0.2.0
duckduckgo-search>=6.0.0
```

---

## License

MIT
