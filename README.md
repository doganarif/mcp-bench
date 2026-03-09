# MCP in the Wild: Cross-Domain Knowledge Discovery through Multi-Server Orchestration

The first empirical study of multi-server MCP orchestration with a 7-model cross-domain synthesis benchmark.

## Key Findings

- **17 real MCP tool calls** across 6 servers, 0% failure rate, 9 cross-domain insights
- **7 LLMs benchmarked** (GPT-5.4, DeepSeek R1, Mistral Large 3, Llama 4 Maverick, Gemini 2.5 Flash, Claude Sonnet 4.5, Claude Haiku 4.5) — all achieved 100% task completion
- **All 7 models independently identified the same gap**: composition patterns for multi-server MCP workflows are undocumented
- **5 composition patterns** documented: Sequential Pipeline, Parallel Fan-Out, Cross-Reference Verification, Iterative Refinement, Domain Bridging

## Benchmark Results

| Model | Latency | Tokens | KG Entities | KG Relations |
|---|---|---|---|---|
| GPT-5.4 | 54.7s | 2,352 | **14** | **15** |
| DeepSeek R1 | 33.9s | 4,296 | 6 | 4 |
| Mistral Large 3 | 6.5s | 1,857 | 9 | 8 |
| Llama 4 Maverick | **3.0s** | 1,374 | 3 | 3 |
| Gemini 2.5 Flash | 15.6s | 4,592 | 12 | 11 |
| Claude Sonnet 4.5 | 21.3s | 2,411 | 13 | 11 |
| Claude Haiku 4.5 | 9.3s | 2,136 | 8 | 6 |

## Composition Patterns

1. **Sequential Pipeline** — Server A → LLM reasoning → Server B
2. **Parallel Fan-Out** — Same query to multiple servers simultaneously
3. **Cross-Reference Verification** — Validate findings across servers
4. **Iterative Refinement** — Cross-server context guides query refinement
5. **Domain Bridging** — Synthesize insights from unrelated domains

## MCP Servers Used

All open-source, no API keys required:

```bash
uvx arxiv-mcp-server                            # Academic preprints
npx @cyanheads/pubmed-mcp-server                # Biomedical literature
npx @modelcontextprotocol/server-memory          # Knowledge graph
npx firecrawl-mcp                                # Web search & scrape
npx @upstash/context7-mcp                        # Library documentation
npx @modelcontextprotocol/server-filesystem      # File operations
```

## Reproduce

### Run the 7-model benchmark

```bash
# Set your API keys
export AZURE_API_KEY="your-azure-key"
export GEMINI_API_KEY="your-gemini-key"
# AWS Bedrock must be configured for Claude models

python benchmark.py
```

### Paper

The paper is available as `paper.pdf` in this repo. Preprint: [arXiv:XXXX.XXXXX](https://arxiv.org/) *(link will be updated after submission)*

## Citation

```bibtex
@article{dogan2026mcp,
  title={MCP in the Wild: Cross-Domain Knowledge Discovery through Multi-Server Orchestration},
  author={Dogan, Arif},
  journal={arXiv preprint},
  year={2026}
}
```

## License

MIT
