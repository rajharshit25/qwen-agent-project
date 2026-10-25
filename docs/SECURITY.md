# Security checklist
1. Bind to 127.0.0.1. Do not port-forward.
2. Treat model output, webpages, retrieved passages, and tool observations as untrusted.
3. Validate tool names/arguments independently of the model.
4. Never expose arbitrary shell, Python, or filesystem execution as an LLM tool.
5. URL fetching (not included yet) needs strict URL parsing, DNS/IP checks, redirect revalidation, private/loopback/link-local blocking, content-type and response-size limits.
6. Require explicit confirmation for consequential actions.
7. CORS is not authentication. Configure only trusted origins if needed.
8. Avoid logging sensitive page/document content.
9. Add authentication/rate limits before any non-local exposure.
10. This educational baseline has not been professionally audited.
