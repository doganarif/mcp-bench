# MCP in the Wild: Cross-Domain Knowledge Discovery through Multi-Server Orchestration

The first empirical study of multi-server [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) orchestration with a 7-model cross-domain synthesis benchmark.

## What is MCP?

**Model Context Protocol (MCP)** is an open standard by Anthropic (released late 2024) that lets LLM agents discover and invoke external tools via JSON-RPC. Think of it as a USB-C for AI: any MCP server exposes tools that any LLM agent can use, regardless of language or platform. As of March 2026, there are 106 official server integrations (GitHub, Postgres, Slack, Docker, etc.) and 50+ academic papers studying the protocol.

This paper asks: **what happens when you connect multiple MCP servers simultaneously for cross-domain tasks?**

## Key Findings

- **17 real MCP tool calls** across 6 servers, 0% failure rate, 9 cross-domain insights
- **7 LLMs benchmarked** (GPT-5.4, DeepSeek R1, Mistral Large 3, Llama 4 Maverick, Gemini 2.5 Flash, Claude Sonnet 4.5, Claude Haiku 4.5) on identical MCP-collected data
- **All 7 models independently identified the same gap**: composition patterns for multi-server MCP workflows are undocumented
- **5 composition patterns** proposed: Sequential Pipeline, Parallel Fan-Out, Cross-Reference Verification, Iterative Refinement, Domain Bridging

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

1. **Sequential Pipeline** -- Server A output feeds Server B query
2. **Parallel Fan-Out** -- Same query to multiple servers at once
3. **Cross-Reference Verification** -- Validate findings across servers
4. **Iterative Refinement** -- Cross-server context guides query refinement
5. **Domain Bridging** -- Synthesize insights from unrelated domains

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

The paper is available as `paper.pdf` in this repo.

- Zenodo: [10.5281/zenodo.18917784](https://doi.org/10.5281/zenodo.18917784)
- SSRN: Abstract ID 6374760

## Citation

```bibtex
@article{dogan2026mcp,
  title={MCP in the Wild: Cross-Domain Knowledge Discovery through Multi-Server Orchestration},
  author={Dogan, Arif},
  journal={Zenodo},
  doi={10.5281/zenodo.18917784},
  year={2026}
}
```

## License

MIT
