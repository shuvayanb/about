---
layout: page
title: "nanoGPT"
permalink: /research/llm_and_agentic_ai/nanoGPT/
---

*Author: Shuvayan Brahmachary — Sep 21, 2025*

---

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


### Step 1: Raw Text

> We start with a small piece of text from enwik8 (character-level LM):

```text
"the quick brown fox jumps over the lazy dog."
```


### Step 2: Assumptions

Before we process further, let’s define the setup:

`B = 1` → batch size (we handle one sequence at a time).

`T = 32` → sequence length (we truncate or pad every text to 32 characters).

`d_model = 16` → embedding dimension (each token will be represented by a 16-dim vector).


### Step 3: Token IDs (X)

Each character is mapped to an integer ID from the vocabulary (size V = 205 for enwik8).

Example mapping (deterministic but arbitrary here for illustration):

```text
t → 19, h → 8, e → 5,   q → 42, u → 53, i → 12, c → 7, k → 28, ...
```

### Step 4: Embedding Table (Wte)


The vocabulary IDs in **X** are just integers.  
To make them useful for the model, each ID is mapped to a **vector representation** via an embedding table:

- **Shape:** `(V, d_model)` = `(205, 16)`  
- Each of the 205 rows corresponds to one token in the vocabulary.  
- Each row is a learnable 16-dimensional vector.  

```text
Wte: (205, 16)
Row 0 → [ 0.01, -0.02,  0.03, ... ]   # token id 0
Row 1 → [-0.04,  0.02,  0.05, ... ]   # token id 1
...
Row 205 → [ ... ]                     # token id 204
```

### Step 5: Token Embeddings (TokEmb)


Looking up the IDs from X in Wte gives us token embeddings:

`TokEmb = Wte[X]`

**Shape:** `(B, T, d_model)` = `(1, 32, 16)`

Each of the 32 characters in the sequence is now represented as a 16-dimensional vector.

```text
TokEmb: (1, 32, 16)
TokEmb[0,0,:] = [ 0.02, -0.01,  0.05, ... ]
TokEmb[0,1,:] = [ 0.01,  0.04, -0.03, ... ]
TokEmb[0,2,:] = [-0.05,  0.02,  0.01, ... ]
TokEmb[0,3,:] = [ 0.03,  0.01, -0.02, ... ]
```

### Step 6: Positional Table (Wpe)

Token embeddings alone have no sense of order in the sequence.
We add order information via positional embeddings:

**Shape:** `(T_max, d_model)` = `(32, 16)`

Each row corresponds to a unique position index (0 → 31).

These are also learnable parameters (in nanoGPT’s absolute PE version).


```text
Wpe: (32, 16)
pos=0 → [ 0.00,  0.01, -0.03, ... ]
pos=1 → [ 0.02, -0.04,  0.05, ... ]
pos=2 → [ 0.01,  0.03, -0.02, ... ]
pos=3 → [ 0.05, -0.01,  0.02, ... ]
...
```

### Step 7: Broadcasted Positional Embeddings (PosEmb)


For our batch and sequence length:

`PosEmb = Wpe[0:T]`


**Shape:** `(B, T, d_model)` = `(1, 32, 16)`

Each token in the sequence gets the vector for its position.

```text
PosEmb: (1, 32, 16)
PosEmb[0,0,:] = [ 0.00,  0.01, -0.03, ... ]
PosEmb[0,1,:] = [ 0.02, -0.04,  0.05, ... ]
PosEmb[0,2,:] = [ 0.01,  0.03, -0.02, ... ]
PosEmb[0,3,:] = [ 0.05, -0.01,  0.02, ... ]
```

### Step 8: Final Input (TokIn)

`TokIn = TokEmb + PosEmb`

**Shape:** `(B, T, d_model)` = `(1, 32, 16)`

Now each token’s vector carries both:

What it is (semantics from TokEmb)

Where it is (position from PosEmb)


```text 
TokIn[0,0,:] = TokEmb[0,0,:] + PosEmb[0,0,:]
TokIn[0,1,:] = TokEmb[0,1,:] + PosEmb[0,1,:]
```



### Step 9: Transformer Block Internals 

We now pass `TokIn` into a Transformer block.  
Our running assumptions:

- **B = 1** (batch size)  
- **T = 32** (sequence length)  
- **d_model = 16** (hidden size)  
- **n_head = 1** (number of attention heads, chosen small for simplicity)  
- **d_head = d_model / n_head = 16** (dimension per head)

**What happens here?**  
LayerNorm standardizes each token vector (subtract mean, divide by std-dev), then rescales with learnable parameters.  
This stabilizes training and ensures each token vector has comparable scale.


#### 9.1 Layer Normalization (pre-norm)

- **Input:**  
  `TokIn ∈ R^(B×T×d_model) = R^(1×32×16)`

- **Output:**  
  `H0 = LN(TokIn) ∈ R^(1×32×16)`

---

#### 9.2 Linear Projections (Q, K, V)

**What happens here?**  
Each token vector in `H0` is linearly projected into three different spaces:  
- **Q (query):** what information this token is asking for.  
- **K (key):** what information this token can provide.  
- **V (value):** the actual information content to be shared.  

These projections are done with independent weight matrices.

- **Symbols:**  
  - `H0` → normalized input, shape `(1×32×16)`  
  - `W_Q, W_K, W_V ∈ R^(16×16)` → learned weight matrices  
  - `b_Q, b_K, b_V ∈ R^16` → learned biases  
  - `Q_lin, K_lin, V_lin` → projected outputs before splitting into heads


- **Projections:**  
  `Q_lin = H0 @ W_Q + b_Q  ∈ R^(1×32×16)`  
  `K_lin = H0 @ W_K + b_K  ∈ R^(1×32×16)`  
  `V_lin = H0 @ W_V + b_V  ∈ R^(1×32×16)`

- **Interpretation:**  
- `Q_lin` = “questions” each token asks  
- `K_lin` = “labels” each token advertises  
- `V_lin` = “content” each token carries

---


#### 9.3 Reshape into Heads

**What happens here?**  
We split each projection into multiple heads so the model can attend to different aspects of the sequence in parallel.  
For simplicity, we use `n_head = 1` here.

- **Symbols:**  
  - `n_head = 1` → number of attention heads  
  - `d_head = d_model / n_head = 16` → size per head  
  - `Q, K, V` → reshaped versions of `Q_lin, K_lin, V_lin`

- **Operation:**  
  `Q = reshape(Q_lin) ∈ R^(1×1×32×16)` <br>
  `K = reshape(K_lin) ∈ R^(1×1×32×16)` <br>
  `V = reshape(V_lin) ∈ R^(1×1×32×16)`


---

### Step 10: Transformer Block Internals

We now use `Q, K, V` to compute how each token attends to all previous tokens in the sequence.



#### 10.1 Attention Scores

**What happens here?**  
We measure similarity between queries and keys. This tells us *how much one token should attend to another*.

- **Symbols:**  
  - `Q ∈ R^(1×1×32×16)` → queries  
  - `K ∈ R^(1×1×32×16)` → keys  
  - `d_head = 16` → per-head dimension  
  - `scores ∈ R^(1×1×32×32)` → attention scores <br>

- **Operation:** `scores = (Q @ K^T) / sqrt(d_head)`

- **Shape:**  `scores ∈ R^(1×1×32×32)`

- **Interpretation:**  
  - Each row `i` contains how much token *i* (as a query) matches all tokens *j* (as keys).  
  - Division by `sqrt(d_head)` prevents large dot products from destabilizing training.


---

#### 10.2 Causal Masking

**What happens here?**  
In language modeling, tokens cannot “see the future.”  
So we mask out positions `j > i` (future tokens) by setting their score to `−∞`.

- **Operation:** `for j > i: scores[..., i, j] = -INF`


- **Interpretation:**  
  - Token at position 5 can only attend to positions ≤ 5.  
  - This enforces left-to-right generation.

---

#### 10.3 Attention Weights

**What happens here?**  
Convert scores into probabilities via softmax.

- **Symbols:**  
  - `weights ∈ R^(1×1×32×32)` → attention distribution

- **Operation:** `weights = softmax(scores, axis=-1)`

- **Shape:**  `weights ∈ R^(1×1×32×32)`


- **Interpretation:**  
  - Each row is a probability distribution over all valid (past) tokens.  
  - Rows sum to 1.

---

#### 10.4 Attention Output

**What happens here?**  
Use the attention weights to take a weighted sum of the value vectors (`V`).  
This gives each token a new representation that blends information from its context.

- **Symbols:**  
  - `V ∈ R^(1×1×32×16)`  
  - `AttnOut ∈ R^(1×1×32×16)`

- **Operation:**  `AttnOut = weights @ V`

- **Shape:**  `AttnOut ∈ R^(1×1×32×16)`

- **Interpretation:**  
  - Each token’s new vector is a mix of other tokens’ values, weighted by relevance.  
  - This is the heart of the attention mechanism.

---


#### 10.5 Merge Heads & Output Projection

**What happens here?**  
We merge the outputs of all heads (here only 1 head) and apply a learned linear projection.  
This mixes information from different heads and aligns it back to the model dimension.

- **Symbols:**  
  - `AttnOut ∈ R^(1×1×32×16)`  
  - `W_O ∈ R^(16×16)`, `b_O ∈ R^16`  
  - `AttnProj ∈ R^(1×32×16)`

- **Operation:**  

`merge_heads(AttnOut) → R^(1×32×16) # since n_head = 1` <br>
`AttnProj = AttnOut_merged @ W_O + b_O`


- **Shape:**  `AttnProj ∈ R^(1×32×16)`

---

#### 10.6 Residual Connection (after attention)

**What happens here?**  
Add the attention projection back to the block’s input (`TokIn`).  
This preserves the original signal and stabilizes gradients.

- **Operation:**  `H1 = TokIn + AttnProj`



- **Shape:**  `H1 ∈ R^(1×32×16)`

---

#### 10.7 Feed-Forward Network (position-wise MLP)

**What happens here?**  
Each token independently passes through a 2-layer MLP with expansion → nonlinearity → projection back.

- **Symbols:**  
  - `LN` params: `gamma2, beta2 ∈ R^16`  
  - Hidden size: `d_ff = 4×d_model = 64`  
- **Weights:**  
  - `W1 ∈ R^(16×64)`, `b1 ∈ R^64`  
  - `W2 ∈ R^(64×16)`, `b2 ∈ R^16`

- **Operation:**  

`H2_in = LN(H1) ∈ R^(1×32×16)` <br>
`MLP_hid = GELU(H2_in @ W1 + b1) ∈ R^(1×32×64)` <br>
`MLP_out = MLP_hid @ W2 + b2 ∈ R^(1×32×16)`



- **Interpretation:**  
Expanding to `d_ff` allows richer nonlinear transformations before projecting back down.

---

#### 10.8 Residual Connection (after MLP)

**What happens here?**  
Add the MLP output back to its input.

- **Operation:**  `H2 = H1 + MLP_out`



- **Shape:**  `H2 ∈ R^(1×32×16)`

---

#### 10.9 Final LayerNorm (block output)

**What happens here?**  
Normalize once more so the representation is well-scaled before feeding into the vocab projection.

- **Operation:**  `Hf = LN(H2)`


- **Shape:**  `Hf ∈ R^(1×32×16)`

- **Interpretation:**  
`Hf` is the **output of the Transformer block**, and the input to the vocabulary projection.

