# AI Email Assistant

AI-powered Gmail assistant built with **LangChain, Gemini, FastAPI and Next.js**. Chat with your inbox to sort, summarize, search (RAG with Qdrant) and draft replies in your own tone. Sending always needs your approval, and the app guards against instructions hidden inside emails.

> The full phased plan is in [docs/AI_Email_Assistant_Plan.pdf](docs/AI_Email_Assistant_Plan.pdf).

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | Next.js (App Router, TypeScript, Tailwind) on Vercel |
| Backend | FastAPI (Python) on Render |
| AI | LangChain + Google Gemini (chat + embeddings) |
| Vector DB | Qdrant Cloud |
| App DB | Neon Postgres |
| Email | Gmail API + Google OAuth 2.0 |

## Project structure

```
ai-email-assistant/
├── backend/    # FastAPI + LangChain
├── frontend/   # Next.js
└── docs/       # plan and notes
```

## Local setup

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in values
uvicorn app.main:app --reload --port 8000
```
Check it at http://localhost:8000/health

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
Open http://localhost:3000. The page shows whether the backend is reachable.

### Tests
```bash
cd backend && pytest
```

## Roadmap

- [x] Phase 0: Project setup
- [ ] Phase 1: Google auth and Gmail core
- [ ] Phase 2: Smart sorting
- [ ] Phase 3: Thread summaries
- [ ] Phase 4: Reply drafting and safe sending
- [ ] Phase 5: RAG search over past emails
- [ ] Phase 6: Agent and chat
- [ ] Phase 7: Hardening and deployment
