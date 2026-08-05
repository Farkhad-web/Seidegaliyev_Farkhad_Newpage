# Chat With Your Docs

A small RAG app — upload some PDFs/text files, ask questions about them, get answers with citations back to the exact page they came from. Built as a take-home style project: FastAPI backend, React frontend, Claude for the actual answering.

![Chat](docs/screenshots/chat.png)

|                                          |                                                            |
| ---------------------------------------- | ---------------------------------------------------------- |
| ![Empty state](docs/screenshots/empty-state.png) | ![Observability](docs/screenshots/observability.png) |

## Quick start

```bash
cp .env.example .env        # add your ANTHROPIC_API_KEY
docker compose up --build
```

- Frontend: http://localhost:8080
- Backend docs: http://localhost:8000/docs

First build takes a few minutes — it downloads the embedding model into the image so it doesn't have to fetch it on every request.

Local dev without Docker:

```bash
# backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ANTHROPIC_API_KEY=sk-ant-... uvicorn app.main:app --reload

# frontend, separate terminal
cd frontend && npm install && npm run dev
```

Tests (offline, no API key needed):

```bash
cd backend && source .venv/bin/activate && pytest
```

## How this came together

Spent about two days on this, on and off. First pass was getting the actual RAG loop working end to end — parsing and chunking documents, getting retrieval to actually find the right passage, wiring that into Claude with a prompt that makes it cite sources instead of just answering from general knowledge. That part took the most thought: I went with a hybrid retrieval setup (vector search plus plain keyword/BM25 search, combined) rather than vector-only, because a small local embedding model misses exact terms — model numbers, names, specific phrases — way more often than people expect. Keyword search catches what the embeddings miss.

Chunking is done page-by-page so every citation points at a real page number, which felt more important than squeezing out slightly better recall from a global sliding window. Embeddings run locally instead of through an API — one less key to manage, no per-request cost, and it's good enough for a project this size. Claude does two jobs: a cheap Haiku call rewrites follow-up questions so "what about its side effects?" actually means something on its own, and Sonnet writes the real answer, grounded in whatever got retrieved.

Once the core loop worked, I added the boring-but-necessary stuff: tests around the chunker and retrieval logic, a confidence flag so low-quality matches get surfaced to the user instead of silently guessed at, basic rate limiting, Docker so it's not a pain to run somewhere else. There's also a small observability tab in the UI — every question logs what got retrieved, the scores, and how long each step took, mostly so I could debug retrieval quality myself without digging through logs.

The second chunk of time went into the UI. It started out pretty plain — functional, not much thought put into it. I went back and did a proper pass: rebuilt it around Tailwind + Radix primitives, added a document preview panel (with an actual PDF viewer for PDF sources), cleaned up the chat streaming so it doesn't render in choppy bursts, made the whole thing work on mobile with the sidebar collapsing into a drawer. I used Claude Code as a pair-programming tool through all of this — wrote most of the actual code with it, leaned on it hardest for the UI redesign and for writing this README, and did the usual back-and-forth of reviewing what it produced, running the tests, and fixing what wasn't right before moving on. It's a tool I use like any other in my workflow, not something that replaces deciding what to build or why.

## What's not done

- No OCR — scanned PDFs with no text layer won't extract anything.
- Chunks don't cross page boundaries, so a sentence split across two pages can lose a bit of context.
- Long conversations just drop older history instead of summarizing it.
- No auth / multi-user support — fine for personal use, not for sharing with a team as-is.
- Rate limiting and the keyword index are in-memory, single-process — would move both to something shared (Redis, etc.) before running this for real.
- Chunk size, overlap, and the confidence threshold are reasonable starting numbers, not tuned against a real eval set yet. There's a small `eval/` script for sanity-checking retrieval after changes; scaling that up is the natural next step.
