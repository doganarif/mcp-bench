#!/usr/bin/env python3
"""
Multi-Model Cross-Domain MCP Orchestration Benchmark v2
7 models: GPT-5.4, DeepSeek R1, Mistral Large 3, Llama 4 Maverick, Gemini 2.5 Flash, Claude Sonnet 4.5, Claude Haiku 4.5
"""

import json, time, sys, re
from pathlib import Path

# ── Cross-domain data from real MCP servers ──
CROSS_DOMAIN_DATA = {
    "source_arxiv": {
        "server": "arxiv-mcp-server", "domain": "CS/AI",
        "papers": [
            {"id": "2505.15715", "title": "PsyLLM: DSM/ICD diagnostic + CBT/ACT therapeutic reasoning", "claim": "No clinical trial conducted"},
            {"id": "2411.10681", "title": "SuDoSys: WHO PM+ guidelines chatbot", "claim": "Stage-aware dialogue, no RCT"},
            {"id": "2509.04183", "title": "MAGneT: Multi-agent synthetic counseling", "claim": "77.2% expert preference"},
            {"id": "2410.22446", "title": "CounselingBench: 22 LLMs evaluated", "claim": "Frontier models fail expert-level empathy"},
            {"id": "2601.14780", "title": "RECAP: Client resistance detection", "claim": "91.25% F1, tested with 62 counselors"},
        ]
    },
    "source_pubmed": {
        "server": "pubmed-mcp-server", "domain": "Clinical Medicine",
        "papers": [
            {"pmid": "41313175", "title": "AI Chatbot Meta-Analysis for Adolescent Mental Health", "finding": "Systematic review of chatbot efficacy"},
            {"pmid": "40882177", "title": "CBT Chatbot RCT: Depression in University Students", "finding": "Randomized controlled trial with financial stress moderation"},
            {"pmid": "38631422", "title": "AI Chatbot Meta-Analysis: Depression/Anxiety Short-term", "finding": "Evidence for short-course therapeutic effectiveness"},
        ]
    },
    "source_firecrawl": {
        "server": "firecrawl", "domain": "Web Intelligence",
        "data": [
            {"finding": "MCP Registry: 106 official servers (March 2026)"},
            {"finding": "MCP (Anthropic) = tool exposure; A2A (Google) = agent collaboration; complementary protocols"},
        ]
    },
    "source_context7": {
        "server": "context7", "domain": "Developer Documentation",
        "data": [
            {"finding": "LangChain MultiServerMCPClient enables connecting multiple MCP servers simultaneously"},
            {"finding": "No composition PATTERNS documented — only connection mechanism"},
        ]
    }
}

PROMPT = """You are given real data from 4 MCP servers (arXiv, PubMed, Firecrawl, Context7).

DATA:
{data}

Task: Identify CROSS-DOMAIN insights visible only by combining 2+ sources.

Return valid JSON:
{{
  "insights": [
    {{"id": 1, "text": "...", "sources": ["arxiv", "pubmed"], "confidence": "high|medium|low"}}
  ],
  "research_gap": "...",
  "knowledge_graph": {{
    "entities": [{{"name": "...", "type": "..."}}],
    "relations": [{{"from": "...", "to": "...", "relation": "..."}}]
  }}
}}

Rules: Exactly 5 insights. Each must use 2+ sources. Include confidence. JSON only, no markdown."""

def call_azure(name, deployment, prompt, data_str, endpoint, key, api_version="2025-04-01-preview"):
    import urllib.request, urllib.error
    url = f"{endpoint}openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    payload = {
        "messages": [
            {"role": "system", "content": "You are a research analyst. Respond only in valid JSON."},
            {"role": "user", "content": prompt.format(data=data_str)}
        ],
        "temperature": 0.3,
    }
    if "gpt" in deployment:
        payload["max_completion_tokens"] = 4000
    else:
        payload["max_tokens"] = 4000
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('api-key', key)
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return {"model": name, "status": "success", "latency": round(time.time()-start, 2),
                    "tokens": result.get('usage',{}).get('total_tokens',0),
                    "response": result['choices'][0]['message']['content']}
    except Exception as e:
        return {"model": name, "status": "error", "latency": round(time.time()-start, 2),
                "error": str(e)[:200]}

def call_gemini(name, prompt, data_str, api_key):
    import urllib.request, urllib.error
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    body = json.dumps({
        "contents": [{"parts": [{"text": f"System: You are a research analyst. Respond only in valid JSON.\n\nUser: {prompt.format(data=data_str)}"}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4000}
    }).encode()
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            text = result['candidates'][0]['content']['parts'][0]['text']
            tokens = result.get('usageMetadata', {}).get('totalTokenCount', 0)
            return {"model": name, "status": "success", "latency": round(time.time()-start, 2),
                    "tokens": tokens, "response": text}
    except Exception as e:
        return {"model": name, "status": "error", "latency": round(time.time()-start, 2),
                "error": str(e)[:200]}

def call_bedrock_claude(name, model_id, prompt, data_str):
    import subprocess, tempfile
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4000,
        "temperature": 0.3,
        "system": "You are a research analyst. Respond only in valid JSON.",
        "messages": [{"role": "user", "content": prompt.format(data=data_str)}]
    })
    start = time.time()
    try:
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as tf:
            outpath = tf.name
        result = subprocess.run([
            "aws", "bedrock-runtime", "invoke-model",
            "--model-id", model_id,
            "--body", body,
            "--content-type", "application/json",
            "--accept", "application/json",
            "--profile", "bedrock",
            "--region", "us-east-1",
            outpath
        ], capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return {"model": name, "status": "error", "latency": round(time.time()-start, 2),
                    "error": result.stderr[:200]}
        with open(outpath) as f:
            resp = json.load(f)
        import os; os.unlink(outpath)
        text = resp.get('content', [{}])[0].get('text', '')
        tokens = resp.get('usage', {}).get('input_tokens', 0) + resp.get('usage', {}).get('output_tokens', 0)
        return {"model": name, "status": "success", "latency": round(time.time()-start, 2),
                "tokens": tokens, "response": text}
    except Exception as e:
        return {"model": name, "status": "error", "latency": round(time.time()-start, 2),
                "error": str(e)[:200]}

def parse_json(raw):
    if not raw: return None
    text = raw.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
        if text.endswith("```"): text = text[:-3]
    try: return json.loads(text)
    except: pass
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try: return json.loads(m.group())
        except: pass
    return None

def score(parsed):
    if not parsed: return {"valid": False, "insights": 0, "xdomain": 0, "kg_e": 0, "kg_r": 0, "gap": False, "high_conf": 0}
    ins = parsed.get("insights", [])
    xd = [i for i in ins if len(i.get("sources", [])) >= 2]
    hc = [i for i in ins if i.get("confidence") == "high"]
    kg = parsed.get("knowledge_graph", {})
    gap = parsed.get("research_gap", "")
    return {"valid": True, "insights": len(ins), "xdomain": len(xd), "high_conf": len(hc),
            "kg_e": len(kg.get("entities", [])), "kg_r": len(kg.get("relations", [])),
            "gap": bool(gap and len(gap) > 20)}

def main():
    AZURE_EP = "https://janni-mi0k87jn-swedencentral.cognitiveservices.azure.com/"
    AZURE_KEY = "REDACTED"
    GEMINI_KEY = "REDACTED"

    data_str = json.dumps(CROSS_DOMAIN_DATA, indent=2)
    results = {}

    models = [
        ("GPT-5.4", "azure", {"deployment": "gpt-5.4", "endpoint": AZURE_EP, "key": AZURE_KEY}),
        ("DeepSeek-R1", "azure", {"deployment": "deepseek-r1", "endpoint": AZURE_EP, "key": AZURE_KEY}),
        ("Mistral-Large-3", "azure", {"deployment": "mistral-large-3", "endpoint": AZURE_EP, "key": AZURE_KEY}),
        ("Llama-4-Maverick", "azure", {"deployment": "llama-4-maverick", "endpoint": AZURE_EP, "key": AZURE_KEY}),
        ("Gemini-2.5-Flash", "gemini", {"key": GEMINI_KEY}),
        ("Claude-Sonnet-4.5", "bedrock", {"model_id": "us.anthropic.claude-sonnet-4-5-20250929-v1:0"}),
        ("Claude-Haiku-4.5", "bedrock", {"model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0"}),
    ]

    print("=" * 70)
    print("MULTI-MODEL CROSS-DOMAIN MCP SYNTHESIS BENCHMARK v2")
    print(f"Models: {len(models)} | Data sources: 4 MCP servers | Date: 2026-03-09")
    print("=" * 70)

    for name, provider, config in models:
        print(f"\n[{name}] Calling via {provider}...", end=" ", flush=True)

        if provider == "azure":
            r = call_azure(name, config["deployment"], PROMPT, data_str, config["endpoint"], config["key"])
        elif provider == "gemini":
            r = call_gemini(name, PROMPT, data_str, config["key"])
        elif provider == "bedrock":
            r = call_bedrock_claude(name, config["model_id"], PROMPT, data_str)

        if r["status"] == "success":
            parsed = parse_json(r.get("response", ""))
            r["evaluation"] = score(parsed)
            r["parsed"] = parsed
            ev = r["evaluation"]
            print(f"OK ({r['latency']}s, {r.get('tokens',0)} tok)")
            print(f"  Insights:{ev['insights']} XDomain:{ev['xdomain']} HighConf:{ev['high_conf']} KG:{ev['kg_e']}e/{ev['kg_r']}r Gap:{'Y' if ev['gap'] else 'N'}")
        else:
            print(f"FAIL ({r['latency']}s)")
            print(f"  {r.get('error','?')[:120]}")
            r["evaluation"] = score(None)

        results[name] = r
        time.sleep(1)

    # ── Save ──
    out = Path("/Users/arif/Documents/mcp-paper/benchmark-results.json")
    # Remove raw responses for clean output
    clean = {}
    for k, v in results.items():
        clean[k] = {kk: vv for kk, vv in v.items() if kk != "response" and kk != "parsed"}
        if v.get("parsed"):
            clean[k]["insights_text"] = [i.get("text","")[:100] for i in v["parsed"].get("insights",[])]
            clean[k]["research_gap"] = v["parsed"].get("research_gap","")[:200]
    with open(out, 'w') as f:
        json.dump(clean, f, indent=2, default=str)

    # ── Final Table ──
    print("\n" + "=" * 90)
    print(f"{'Model':<22} {'Status':<7} {'Latency':>8} {'Tokens':>7} {'Insights':>8} {'XDomain':>8} {'HiConf':>7} {'KG-E':>5} {'KG-R':>5} {'Gap':>4}")
    print("-" * 90)
    for name, r in results.items():
        ev = r["evaluation"]
        print(f"{name:<22} {r['status']:<7} {r['latency']:>7}s {r.get('tokens',0):>7} {ev['insights']:>8} {ev['xdomain']:>8} {ev['high_conf']:>7} {ev['kg_e']:>5} {ev['kg_r']:>5} {'Y' if ev['gap'] else 'N':>4}")

    # ── Summary stats ──
    successful = [r for r in results.values() if r['status'] == 'success']
    print(f"\n{'='*90}")
    print(f"Models tested: {len(models)} | Successful: {len(successful)} | Failed: {len(models)-len(successful)}")
    if successful:
        avg_latency = sum(r['latency'] for r in successful) / len(successful)
        avg_insights = sum(r['evaluation']['insights'] for r in successful) / len(successful)
        avg_kg = sum(r['evaluation']['kg_e'] for r in successful) / len(successful)
        print(f"Avg latency: {avg_latency:.1f}s | Avg insights: {avg_insights:.1f} | Avg KG entities: {avg_kg:.1f}")
        best_kg = max(successful, key=lambda r: r['evaluation']['kg_e'])
        print(f"Richest KG: {best_kg['model']} ({best_kg['evaluation']['kg_e']}e/{best_kg['evaluation']['kg_r']}r)")
    print(f"\nResults: {out}")

if __name__ == "__main__":
    main()
