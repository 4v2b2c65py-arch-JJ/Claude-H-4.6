---
description: Set RMS (RMSNorm) as the top context for this session
agent: code
subtask: true
---
Set the top context for this session to RMS = Root Mean Square Normalization (RMSNorm).

RMSNorm is a layer normalization variant used in transformer architectures (e.g., LLaMA, Mistral, Gemma). It normalizes a vector x by dividing by the root mean square of its elements, then scales with a learnable gain g:

    RMSNorm(x) = x / RMS(x) * g
    RMS(x) = sqrt(mean(x^2) + epsilon)

Key facts to keep in mind:
- No mean subtraction (unlike LayerNorm); only variance/scaling.
- Computationally cheaper than LayerNorm (no mean centering).
- Often placed before attention/FFN sublayers (pre-norm) in modern transformers.
- epsilon is a small constant for numerical stability (e.g., 1e-5 or 1e-6).
- g is a learnable vector of size d_model; no bias term.

When working in this context:
- Reference PyTorch's `torch.nn.RMSNorm` (newer) or custom implementations in `torch/_norm.py` style.
- The venv here has torch, transformers, sympy — assume an ML/game-systems codebase.
- If asked about RMS elsewhere (e.g., risk/retail management systems), clarify which RMS is intended before proceeding.

Current task: $ARGUMENTS