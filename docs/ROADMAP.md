# Phase acceptance checklist
Do not mark a phase Verified until the test is run on the target PC and evidence is recorded.

- [ ] 0 Environment inspection, venv and dependencies work.
- [ ] 1 Qwen responds in Ollama terminal; record tag, latency, RAM.
- [ ] 2 Python Ollama smoke test succeeds.
- [ ] 3 Summarization prompt handles untrusted source text.
- [ ] 4 Valid action schema, bounded loop and termination tested.
- [ ] 5 Safe calculator, parser and webpage analyzer tested.
- [ ] 6 Trace contains action/status/result without hidden reasoning.
- [ ] 7 Session isolation and deletion verified.
- [ ] 8 Retrieval relevance and source references evaluated.
- [ ] 9 API malformed/oversized inputs tested.
- [ ] 10 Streaming completion/errors/disconnections tested.
- [ ] 11 Extension loads and extracts regular pages.
- [ ] 12 Popup/backend page summary works.
- [ ] 13 Fixed multi-tool tasks pass within limits.
- [ ] 14 Adversarial, SSRF, CORS, and size-limit tests pass.
- [ ] 15 Dataset metrics measured and recorded.
- [ ] 16 Custom agent compared with Qwen-Agent on same tasks.
- [ ] 17 Clean setup reproduces documented workflow.
For each run record date, OS, Python/dependency versions, model tag, hardware, command, output, status, issue and next action.
