# Qwen-Based Agentic AI System for Intelligent Web Assistance
**PCU, School of Engineering & Technology · Academic Year 2026–27**

This is an educational, local-first baseline featuring a FastAPI backend, Ollama client, bounded custom agent loop, allowlisted tools, SQLite chat history/document chunks, basic lexical retrieval, pytest checks, and a Chrome Manifest V3 popup.

## Important truth about scope
This ZIP is a runnable **starter baseline**, not a claim that all Phase 0–17 acceptance criteria are completed or verified on your laptop. Not yet implemented: true streaming, embedding/vector RAG, external web search, URL fetch/SSRF-hardened retrieval, complete security testing, Qwen-Agent comparison, Docker, and measured evaluation results. Do not present these as completed features.

## Requirements
Windows 11, Python 3.11/3.12 recommended, Git, Chrome, Ollama. 16 GB RAM assumed; no dedicated GPU assumed. `qwen2.5:3b` is the default starter tag, not a universal recommendation. Verify model tag/availability in the current Ollama library before pulling.

## Windows PowerShell quick start
```powershell
py --version
git --version
node --version
ollama --version
ollama list
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
If activation is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, or use `.venv\Scripts\python.exe` directly.

Install the model after checking disk space:
```powershell
ollama pull qwen2.5:3b
ollama run qwen2.5:3b
```
Exit the model session and smoke test:
```powershell
python scripts/ollama_smoke_test.py
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Then visit http://127.0.0.1:8000/docs. Keep the API bound to `127.0.0.1`; do not expose it to a network.

## API examples
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/chat -Method Post -ContentType "application/json" -Body '{"message":"Explain agentic AI simply"}'
Invoke-RestMethod http://127.0.0.1:8000/api/agent -Method Post -ContentType "application/json" -Body '{"goal":"Calculate (12 + 8) / 4"}'
Invoke-RestMethod http://127.0.0.1:8000/api/summarize -Method Post -ContentType "application/json" -Body '{"text":"A sample text. Another sentence."}'
```
Document endpoints: `POST /api/documents` with `{ "name":"notes.txt", "text":"..." }`, then `POST /api/documents/query` with `{ "message":"question" }`. This is SQLite `LIKE` lexical retrieval, **not** vector/embedding RAG. History: `GET /api/history/{session_id}` and `DELETE /api/history/{session_id}`.

## Load the Chrome extension
1. Start Ollama and the backend.
2. Navigate to `chrome://extensions`, turn on Developer mode.
3. Click **Load unpacked** and choose this repository's `extension` folder.
4. Open a normal HTTP/HTTPS page and click the extension.
5. Click **Summarize page**, or enter a question and click **Ask Qwen**.
Restricted Chrome pages cannot be extracted. User-triggered actions send page text to the local backend.

## Tests
```powershell
pytest -q
```
These tests cover basic tools only; they are not a full integration/security suite.

## Architecture
Chrome popup → FastAPI → (Ollama/Qwen or custom AgentEngine) → validated allowlisted tool → observation/trace. SQLite stores chat history and document chunks. The model proposes actions; application code validates them. No model-generated Python or shell commands are executed.

## Phase status at archive creation
- Phase 0: **Not verified on your PC** (inspect local tools first).
- Phase 1: **Not verified** (requires installed Ollama/model).
- Phase 2: implemented, not machine-verified.
- Phase 3: partial; prompt strings are currently inline.
- Phase 4: baseline bounded custom loop implemented, not integration-verified.
- Phase 5: partial (calculator, text parser, webpage text analyzer; no search/URL retrieval).
- Phase 6: basic observable trace implemented.
- Phase 7: SQLite history implemented; retention/context controls need more work.
- Phase 8: lexical retrieval baseline only; embeddings/vector store not implemented.
- Phase 9: basic FastAPI routes implemented.
- Phase 10: streaming not implemented.
- Phase 11: extension popup/content script implemented, needs browser test.
- Phase 12: local integration implemented, needs end-to-end test.
- Phase 13: basic bounded tool loop; fixed task suite not implemented.
- Phase 14: partial security controls; not audited.
- Phase 15: not measured; no results invented.
- Phase 16: Qwen-Agent comparison not implemented.
- Phase 17: documentation baseline; Docker and full academic deliverables remain.

## Security notes
- Bind only to loopback and do not port-forward.
- Model output, webpage text, and documents are untrusted.
- Tool allowlist and restricted arithmetic AST reduce risk but do not make the full application secure.
- No URL-fetch tool exists in this baseline; if added, implement private-IP/loopback blocking, DNS and redirect revalidation, response limits, and SSRF tests.
- Chats/documents are local but unencrypted. Do not store secrets.
- CORS is disabled by default. If the browser blocks extension requests, configure the exact extension origin based on the browser's reported origin; don't use unrestricted `*` as a production fix.
- Educational prototype only; not professionally security-audited.

## Official documentation
- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- Ollama models: https://ollama.com/library
- FastAPI: https://fastapi.tiangolo.com/
- Chrome extensions: https://developer.chrome.com/docs/extensions/develop/
- Qwen: https://github.com/QwenLM
- Qwen-Agent: https://github.com/QwenLM/Qwen-Agent
- ReAct: https://arxiv.org/abs/2210.03629
