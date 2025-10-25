# Using Local LLMs with Scenario Lab

Scenario Lab now supports running scenarios with local LLM models via Ollama, enabling **cost-free batch runs** and complete privacy for sensitive policy scenarios.

## Quick Start

### 1. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com/download
```

### 2. Pull a Model

```bash
# Recommended models for policy scenarios:
ollama pull llama3.1:70b      # High quality, requires ~40GB VRAM
ollama pull qwen2.5:72b        # Excellent reasoning, ~40GB VRAM
ollama pull llama3.1:8b        # Fast, lower quality, ~5GB VRAM
ollama pull mistral:latest     # Good balance, ~4GB VRAM
```

### 3. Update Your Actor Configuration

In your `actor.yaml` files, use the `ollama/` prefix:

```yaml
name: "United States"
model: "ollama/llama3.1:70b"  # ← Use local model
```

Or for validation:

```yaml
validation_model: "ollama/qwen2.5:72b"
```

That's it! No API keys needed for local models.

## Model Selection Guide

### For Actor Decision-Making

| Model | VRAM | Quality | Speed | Best For |
|-------|------|---------|-------|----------|
| `ollama/llama3.1:70b` | 40GB | Excellent | Slow | Main actors in important scenarios |
| `ollama/qwen2.5:72b` | 40GB | Excellent | Slow | Complex reasoning, policy analysis |
| `ollama/llama3.1:8b` | 5GB | Good | Fast | Supporting actors, testing |
| `ollama/mistral:latest` | 4GB | Good | Fast | Validation, batch runs |

### For World State Synthesis

Recommended: `ollama/llama3.1:70b` or `ollama/qwen2.5:72b`

World state synthesis requires strong reasoning to synthesize multiple actor actions coherently.

### For QA Validation

Recommended: `ollama/llama3.1:8b` or `ollama/mistral:latest`

Validation checks are simpler and can use faster, smaller models to save time.

## Mixed Configurations

You can mix local and cloud models in the same scenario:

```yaml
# scenario.yaml
world_state_model: "openai/gpt-4o-mini"  # Cloud for quality
actors:
  - united-states    # Uses ollama/llama3.1:70b (local)
  - european-union   # Uses openai/gpt-4o-mini (cloud)
```

This lets you:
- Use local models for actors (save $$$ on repeated decisions)
- Use cloud models for world state (ensure quality)
- Test local model quality against cloud baselines

## Cost Comparison

### OpenRouter (Cloud)
- **gpt-4o-mini**: ~$0.41 per 5-turn scenario
- **100 scenarios**: ~$41

### Ollama (Local)
- **Any model**: $0 per scenario
- **100 scenarios**: $0
- **Only cost**: Hardware (one-time)

**Break-even**: Running ~5-10 batch scenarios pays for the electricity of running local models.

## Configuration

### Custom Ollama URL

If Ollama is running on a different machine or port:

```bash
export OLLAMA_BASE_URL=http://192.168.1.100:11434
```

Or in your `.env` file:

```
OLLAMA_BASE_URL=http://192.168.1.100:11434
```

### Model Naming

The framework supports two prefixes for local models:

- `ollama/model-name` - Standard Ollama models
- `local/model-name` - Alternative prefix (also routes to Ollama)

Both work identically.

## Performance Tips

### 1. GPU Acceleration

Ensure Ollama uses your GPU:

```bash
# Check Ollama is using GPU
ollama ps
```

You should see GPU memory usage. If not, check your GPU drivers.

### 2. Concurrent Requests

Ollama handles concurrent requests well. You can run multiple scenarios in parallel:

```bash
# Run 4 scenarios in parallel
for i in {1..4}; do
    python src/run_scenario.py scenarios/my-scenario &
done
wait
```

### 3. Model Loading

First request to a model is slow (loads into VRAM). Subsequent requests are fast. Keep Ollama running between scenarios:

```bash
# Keep model loaded
ollama run llama3.1:70b
# Press Ctrl+D to exit chat but keep model loaded
```

## Hardware Requirements

| Model Size | Min VRAM | Recommended VRAM | Typical Speed |
|------------|----------|------------------|---------------|
| 7-8B | 5GB | 8GB | ~20-30 tokens/sec |
| 70-72B | 40GB | 48GB+ | ~5-10 tokens/sec |
| 405B | 200GB+ | Multiple GPUs | ~1-2 tokens/sec |

**For most scenarios**: A 24GB GPU (RTX 3090, RTX 4090) can run 8B models very well, or 70B models with quantization.

## Troubleshooting

### "Connection refused" errors

Ollama isn't running. Start it:

```bash
ollama serve
```

### Slow performance

1. Check GPU usage: `nvidia-smi` or `ollama ps`
2. Try a smaller model: `ollama pull llama3.1:8b`
3. Ensure model is already loaded (first request is always slow)

### Out of memory

Model too large for your GPU. Try:

```bash
# Use quantized version
ollama pull llama3.1:70b-q4  # 4-bit quantization, ~20GB
```

## Quality Comparison

Based on testing with AI policy scenarios:

| Model | Cloud Equivalent | Notes |
|-------|------------------|-------|
| `llama3.1:70b` | GPT-3.5 Turbo | Very good for policy scenarios |
| `qwen2.5:72b` | GPT-4o-mini | Excellent reasoning |
| `llama3.1:8b` | GPT-3.5 | Good for simpler tasks |

**Recommendation**: For research-grade scenarios, start with cloud models (gpt-4o-mini) to establish baseline, then test if local models achieve similar quality.

## Advanced: llama.cpp Support

The framework is designed to support llama.cpp in the future. Current status: **Not yet implemented**.

To add llama.cpp support:

1. Run llama.cpp server with OpenAI-compatible API
2. Set `OLLAMA_BASE_URL` to your llama.cpp server URL
3. Use `ollama/` or `local/` prefix

This works because both Ollama and llama.cpp use OpenAI-compatible APIs.

## Examples

### Example 1: Fully Local Scenario

```yaml
# scenario.yaml
name: "AI Policy Negotiation (Local)"
world_state_model: "ollama/llama3.1:70b"
actors:
  - united-states
  - european-union
```

```yaml
# actors/united-states.yaml
name: "United States"
model: "ollama/llama3.1:70b"
```

```yaml
# validation-rules.yaml
validation_model: "ollama/mistral:latest"
```

**Cost**: $0

### Example 2: Hybrid Configuration

Use local for actors (many calls), cloud for world state (few calls, need quality):

```yaml
# scenario.yaml
world_state_model: "openai/gpt-4o-mini"  # Cloud for quality
```

```yaml
# actors/united-states.yaml
model: "ollama/llama3.1:70b"  # Local for volume
```

**Cost**: ~$0.10 (only world state updates use API)

## Future Enhancements

Planned improvements for local LLM support:

- [ ] Automatic model download if not present
- [ ] Model quantization selection
- [ ] llama.cpp native support
- [ ] Performance benchmarking tools
- [ ] Quality comparison tools (local vs cloud)
- [ ] Batch optimization for local models

## Questions?

See the main [README.md](../README.md) for general framework documentation.

For Ollama-specific questions, visit [ollama.com/docs](https://ollama.com/docs).
