# Intelligent Model Selection & Token Optimization

## Overview

The HyperKit Agent includes **automatic model selection** that optimizes for:
1. **Token Usage**: Selects the cheapest model that can handle the task
2. **Cost Efficiency**: Prefers Gemini Flash-Lite models (cheaper)
3. **Automatic Fallback**: Falls back to more capable models when needed

## Integration Points

### ✅ Integrated Commands/Operations

1. **Contract Generation** (`services/generation/generator.py`)
   - Uses `HybridLLMRouter` with intelligent model selection
   - Automatically selects cheapest Gemini Flash-Lite model
   - Falls back to direct API calls if router fails

2. **LLM Router** (`core/llm/router.py`)
   - Primary routing system with model selector
   - All `route()` calls use intelligent selection
   - Tracks token usage per model

### ⚠️ Alith SDK Operations (Separate System)

- **Alith SDK** (`services/core/ai_agent.py`) uses its own model management
- Uses OpenAI GPT models via Alith SDK (separate from model selector)
- This is intentional - Alith SDK has its own optimization

### 📝 Future Integration Opportunities

If you want model selection for:
- **Direct API calls** (not using router)
- **Fallback scenarios** (when Alith unavailable)
- **Custom AI operations** (analysis, optimization prompts)

Add this pattern:
```python
from core.llm.router import HybridLLMRouter

router = HybridLLMRouter(config=your_config)
response = router.route(
    prompt=your_prompt,
    task_type="code",  # or "analysis", "general"
    expected_output_length=2000  # optional
)
```

## Supported Models

### Gemini Models (Preferred - Cheaper)

| Model                  | Input Tokens   | Output Tokens  | Tier  | Priority |
|------------------------|----------------|----------------|-------|----------|
| Gemini 2.0 Flash-Lite  | 4,000,000,000  | 1,000,000,000  | LITE  | 1 (Best) |
| Gemini 2.5 Flash-Lite  | 3,000,000,000  | 750,000,000    | LITE  | 1 (Best) |
| Gemini 2.0 Flash       | 2,000,000,000  | 500,000,000    | FLASH | 2        |
| Gemini 2.5 Flash       | 1,000,000,000  | 120,000,000    | FLASH | 2        |
| Gemini 2.5 Pro         | 240,000,000    | 30,000,000     | PRO   | 3        |

### OpenAI Models (Fallback)

| Model          | Input Tokens | Output Tokens | Tier  | Priority |
|----------------|--------------|---------------|-------|----------|
| GPT-4o-mini    | 128,000      | 16,000        | FLASH | 4        |
| GPT-3.5-turbo  | 16,385       | 4,096         | LITE  | 5        |

## How It Works

### Automatic Selection Process

1. **Token Estimation**: Estimates input/output tokens based on prompt length and task type
2. **Model Filtering**: Filters models that can handle the token requirements
3. **Cost Optimization**: Selects cheapest suitable model (prioritizes Gemini Flash-Lite)
4. **Usage Tracking**: Records actual token usage for statistics

### Selection Logic

```python
# Priority order:
1. Gemini 2.0/2.5 Flash-Lite (highest priority - cheapest)
2. Gemini 2.0/2.5 Flash (balanced)
3. Gemini 2.5 Pro (most capable, fallback)
4. OpenAI GPT-4o-mini (if Gemini unavailable)
5. OpenAI GPT-3.5-turbo (last resort)
```

## Configuration

The system automatically detects available models from:
- Environment variables: `GOOGLE_API_KEY`, `OPENAI_API_KEY`
- Config file: `config.yaml` → `ai_providers.google.api_key`

## Usage Statistics

Track token usage per model:
```python
router = HybridLLMRouter(config)
stats = router.get_model_stats()
# Returns: {model_name: {total_requests, avg_tokens, total_tokens, ...}}
```

## Cost Savings

By using Gemini Flash-Lite models:
- **90%+ cost reduction** vs GPT-4
- **Automatic optimization** - no manual selection needed
- **Smart fallback** - upgrades only when necessary

## Integration Status

### ✅ Fully Integrated

- Contract generation via `ContractGenerator.generate()`
- All LLM router calls
- Model selector initialized on startup

### 🔄 Partially Integrated

- Direct API calls in `generator.py` (has fallback)
- Workflow orchestrator (uses router indirectly)

### ⚠️ Not Integrated (By Design)

- Alith SDK operations (uses its own model management)
- Static analysis tools (no LLM needed)

## Manual Override

If you need to force a specific model:
```python
selector = router.get_model_selector()
model_name, spec = selector.select_best_model(
    estimated_input_tokens=1000,
    estimated_output_tokens=500,
    task_type="code",
    prefer_cheap=False  # Use more capable models
)
```
