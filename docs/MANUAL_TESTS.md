# Manual smoke tests
1. `GET /health` returns service status.
2. `GET /api/health` returns model configuration.
3. `POST /api/chat` returns a session ID and answer with Ollama running.
4. Repeat chat with the returned session ID and inspect context.
5. `POST /api/agent` with `Calculate 19 * 23` should use the calculator or safely answer.
6. `POST /api/summarize` returns summary text.
7. Upload a short document and query a distinctive phrase.
8. Load extension unpacked and summarize an ordinary article.
9. Stop Ollama; API should return 503 instead of a traceback.
10. Run `pytest -q`.
