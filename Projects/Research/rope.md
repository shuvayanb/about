---
layout: page
title: "Rotary Positional Embeddings in nanoGPT"
permalink: /research/llm_and_agentic_ai/rope/
---

*Author: Shuvayan Brahmachary — Sep 21, 2025*

---

## Introduction

Language models require not only learning the relationship between tokens but also capturing their **order**. In character-level modeling tasks, where the unit is a single character, the ability to represent sequential positions becomes even more crucial.  

For this study, I use the **enwik8 dataset** — a standard 100M character benchmark widely used in compression and modeling tasks. The metric of interest is **Bits per Character (BPC)**, which directly measures predictive performance: lower BPC means better compression and thus stronger modeling ability.  


<div class="note-background" markdown="1">

### Example: Prediction as Compression

Let’s walk through a simple example with only two characters: `A` and `B`.

If we know nothing about the text, we have to treat them equally. That means we assign **the same cost** to each character, for example **1 bit each**. On average, every character in the dataset costs 1 bit to store.

Now suppose our dataset looks very skewed: `A` appears **90% of the time** and `B` only **10% of the time**. A language model trained on this dataset quickly picks up that pattern and starts predicting:

- `p(A) = 0.9`
- `p(B) = 0.1`

Here’s the key idea: if something is very **likely** (like `A`), it doesn’t need much space to describe, because the model already expects it. In contrast, if something is **rare** (like `B`), it requires a longer description to make sure we don’t confuse it with `A`. This trade-off — short for common, long for rare — reduces the *average* cost.

When we do the math:

- `A` works out to about **0.47 bits per occurrence**
- `B` works out to about **3.32 bits per occurrence**
- Weighted by frequency, the overall cost is  
  `0.9 × 0.47 + 0.1 × 3.32 ≈ 0.8 bits per character`

So instead of 1.0 bits per character, the model only needs about **0.8 bits per character** on average.

This is exactly what **Bits per Character (BPC)** measures: the *average number of bits required to store text when compressed using the model’s predictions*. Better prediction leads to fewer wasted bits, which means lower BPC.

</div>


My baseline is [nanoGPT](https://github.com/karpathy/nanoGPT), a minimal GPT implementation by Andrej Karpathy.  
I introduce [Rotary Positional Embeddings (RoPE)](https://arxiv.org/abs/2104.09864) into this architecture and evaluate whether it improves model efficiency under a fixed parameter budget (~44M parameters).


### Character-Level Language Models
A character-level LM predicts the next character given a sequence of previous characters. Unlike word-level models, it must capture both fine-grained patterns (e.g., “th” → “e”) and long-range dependencies across thousands of characters.

### Why Positional Embeddings Matter
Transformers process sequences in parallel, so they need explicit positional information.

- **Absolute embeddings**: add a learned or sinusoidal vector to each token embedding.  
- **Relative embeddings**: represent positions by differences, allowing generalization to unseen lengths.  
- **RoPE (Rotary Positional Embedding)**, introduced by [Su et al. in RoFormer (2021)](https://arxiv.org/abs/2104.09864), provides a neat trick: instead of adding positional vectors, it rotates the query and key vectors inside self-attention. This ensures dot products naturally reflect relative positions.


<div class="note-background" markdown="1">

### nanoGPT in a Nutshell
[nanoGPT](https://github.com/karpathy/nanoGPT) is a **minimal GPT implementation** by Andrej Karpathy.  
It keeps just the essentials for autoregressive text modeling:

- **Token & Positional Embeddings** – turn characters into vectors  
- **Transformer Blocks** (12 in this study), each with  
  - LayerNorm  
  - Multi-Head Self-Attention  
  - Feed-Forward MLP  
- **Final Linear Layer** – maps hidden states back to vocabulary logits

Despite its simplicity, nanoGPT is strong enough to train on enwik8 and makes a clean research baseline.

</div>

<div class="note-background" markdown="1">

### What enwik8 text looks like

enwik8 is the **raw** Wikipedia dump: 

<doc id="12" url="https://en.wikipedia.org/wiki/Alan_Turing" title="Alan Turing">
'''Alan Mathison Turing''' (23 June 1912 – 7 June 1954) was an English mathematician,
computer scientist, logician, cryptanalyst, philosopher, and theoretical biologist.

== Early life ==
Turing was born in Maida Vale, London, and educated at Sherborne School.
* Interests included mathematics and chemistry.
* He read papers by Einstein while still at school.
<ref name="hodges">Hodges, Andrew (1983). ''Alan Turing: The Enigma''.</ref>

See also: [[Church–Turing thesis]] and [[Bombe]]
</doc>



**Why it matters:**  
- The model sees *every single character* (letters, digits, whitespace, punctuation, markup).  
- Vocabulary is small `(~205 symbols: alphabets (A-Z), digits (0-9), punctuations (.,!?;:"'()[]{}…)`, but sequences are **long and structured**, testing whether the LM can capture dependencies across thousands of characters.  

</div>


<div class="note-background" markdown="1">

```text
raw text
  ↓ tokenize (char → id, per your vocab)
X: (B, T) = (1, 32)           e.g. [19, 8, 5, 3, 42, 53, 12, ...]
  # integers in [0..V-1]

  ↓ token embedding lookup (row-wise table lookup)
Embedding table Wte: (V, d_model) = (205, 16)
TokEmb = Wte[X]: (B, T, d_model) = (1, 32, 16)

  ↓ positional information (Absolute Positional Embeddings)
Positional table Wpe: (T_max, d_model) = (32, 16)      
PosEmb = broadcast Wpe[0:T] → (B, T, d_model) = (1, 32, 16)

  ↓ add position to token representation (the block’s input)
TokIn = TokEmb + PosEmb        # (1, 32, 16)

  ↓ Transformer Block (×1 layer in your run)
    - LayerNorm over last dim (per token)
      H0 = LN(TokIn)                             # (1, 32, 16)

    - Self-Attention (per head)
      # Linear projections from H0
      Q_lin = H0 @ W_Q + b_Q                     # (1, 32, 16)
      K_lin = H0 @ W_K + b_K                     # (1, 32, 16)
      V_lin = H0 @ W_V + b_V                     # (1, 32, 16)

      # reshape to heads
      Q = reshape(Q_lin) → (B, n_head, T, d_head) = (1, 1, 32, 16)
      K = reshape(K_lin) → (1, 1, 32, 16)
      V = reshape(V_lin) → (1, 1, 32, 16)

      # scaled dot-product attention with causal mask
      scores = Q @ K^T / sqrt(d_head)            # (1, 1, 32, 32)
      scores[j > i] = -inf (causal mask)
      weights = softmax(scores, axis=-1)         # (1, 1, 32, 32)

      AttnOut = weights @ V                      # (1, 1, 32, 16)
      merge heads → concat over head dim         # (1, 32, 16)

      # output projection
      AttnProj = AttnOut @ W_O + b_O             # (1, 32, 16)

      # residual connection
      H1 = TokIn + AttnProj                      # (1, 32, 16)

    - MLP (position-wise feed-forward: GELU + Linear)
      H2_in = LN(H1)                             # (1, 32, 16)
      MLP_hidden = GELU(H2_in @ W1 + b1)         # (1, 32, d_ff)
      MLP_out    = MLP_hidden @ W2 + b2          # (1, 32, 16)
      H2 = H1 + MLP_out                          # (1, 32, 16)

  ↓ final LayerNorm
Hf = LN(H2)                                      # (1, 32, 16)

  ↓ linear head to vocab logits
Logits = Hf @ W_vocab + b_vocab                  # (1, 32, V) = (1, 32, 205)

  ↓ cross-entropy vs next-token targets Y
# Y is X shifted left by 1 position (teacher forcing)
loss = CE(Logits, Y)                             # scalar
```

</div>
