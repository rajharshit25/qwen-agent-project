import json, os, urllib.request
base=os.getenv("OLLAMA_BASE_URL","http://127.0.0.1:11434")
model=os.getenv("OLLAMA_MODEL","qwen2.5:3b")
payload=json.dumps({"model":model,"prompt":"Reply with exactly: QWEN_OK","stream":False}).encode()
request=urllib.request.Request(base+"/api/generate",data=payload,headers={"Content-Type":"application/json"})
try:
 with urllib.request.urlopen(request,timeout=120) as response: data=json.loads(response.read().decode())
 print("Model:",model);print("Response:",data.get("response","").strip())
except Exception as exc: raise SystemExit(f"Smoke test failed: {exc}\nCheck Ollama and model installation.")
