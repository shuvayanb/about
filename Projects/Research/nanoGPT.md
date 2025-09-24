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


<!-- === Interactive: Tokenisation (Step 3) — light theme, V fixed to 205 === -->
<div class="nano-card" id="nano-tokeniser" data-T="32">
  <div class="nano-head">
    <h4 style="margin:0">Interactive · Tokenisation (Step 3)</h4>
    <div class="nano-sub">V = 205 (fixed), PAD = 0 · Map characters → IDs, then truncate/pad to T.</div>
  </div>

  <div class="nano-row">
    <label class="nano-label">Text</label>
    <textarea class="nano-input" id="nano-text" rows="2">the quick brown fox jumps over the lazy dog.</textarea>
  </div>

  <div class="nano-row nano-grid">
    <div>
      <label class="nano-label">T (sequence length)</label>
      <input class="nano-num" id="nano-T" type="number" min="4" value="32">
    </div>
    <div class="nano-actions">
      <button class="nano-btn" id="nano-build">Build IDs</button>
      <button class="nano-btn ghost" id="nano-reset">Reset</button>
    </div>
  </div>

  <div class="nano-section">
    <div class="nano-label">Characters (pre-processing)</div>
    <div class="nano-tiles" id="nano-chars"></div>
    <div class="nano-note">We lowercase the text (toy char-level LM).</div>
  </div>

  <div class="nano-arrow">↓ tokenize (char → id)</div>

  <div class="nano-section">
    <div class="nano-label">Token IDs (X) · shape (B,T) = (1,<span id="nano-T-label">32</span>)</div>
    <div class="nano-code" id="nano-X"></div>
    <div class="nano-note">If shorter than T → pad with <code>0</code>. If longer → truncate.</div>
  </div>

  <div class="nano-section">
    <div class="nano-label">Mapping Table (unique chars in this sample)</div>
    <div class="nano-map" id="nano-map"></div>
  </div>
</div>

<style>
  /* Light theme */
  .nano-card{
    --bg:#f8fafc; --fg:#0b0e14; --muted:#4b5563; --accent:#2563eb;
    --line:#e5e7eb; --tile:#ffffff;
    border:1px solid var(--line); background:var(--bg); color:var(--fg);
    border-radius:16px; padding:18px; box-shadow:0 4px 18px rgba(0,0,0,.07); margin:1.25rem 0
  }
  .nano-head{display:flex; align-items:baseline; gap:.75rem}
  .nano-sub{color:var(--muted); font-size:.95rem}
  .nano-row{margin-top:12px}
  .nano-label{display:block; font-size:.9rem; color:var(--muted); margin-bottom:6px}
  .nano-input{width:100%; background:var(--tile); color:var(--fg); border:1px solid var(--line); border-radius:10px; padding:10px 12px; font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
  .nano-num{width:130px; background:var(--tile); color:var(--fg); border:1px solid var(--line); border-radius:10px; padding:8px 10px; font-family:inherit}
  .nano-grid{display:flex; gap:12px; align-items:end; flex-wrap:wrap}
  .nano-actions{margin-left:auto; display:flex; gap:8px}
  .nano-btn{background:var(--accent); color:#fff; border:none; border-radius:10px; padding:8px 12px; font-weight:600; cursor:pointer}
  .nano-btn.ghost{background:transparent; color:var(--fg); border:1px solid var(--line)}
  .nano-section{margin-top:16px}
  .nano-tiles{display:flex; flex-wrap:wrap; gap:8px; background:var(--tile); border:1px solid var(--line); padding:10px; border-radius:12px}
  .nano-tile{background:#f3f4f6; border:1px solid var(--line); border-radius:10px; padding:6px 10px; min-width:30px; text-align:center; font-family:ui-monospace,monospace; position:relative}
  .nano-tile::after{content:attr(data-i); position:absolute; top:-8px; right:-8px; font-size:.7rem; color:var(--muted); background:var(--tile); border:1px solid var(--line); padding:2px 6px; border-radius:999px}
  .nano-arrow{margin:14px 0; text-align:center; color:var(--muted)}
  .nano-code{font-family:ui-monospace,Menlo,monospace; background:#fbfbfd; border:1px solid var(--line); padding:12px; border-radius:12px; white-space:pre-wrap; word-break:break-word}
  .nano-map{display:grid; grid-template-columns: repeat(auto-fit,minmax(140px,1fr)); gap:8px}
  .nano-rowmap{background:#fbfbfd; border:1px solid var(--line); border-radius:10px; padding:8px 10px; display:flex; justify-content:space-between; font-family:ui-monospace,monospace}
  .nano-note{margin-top:6px; color:var(--muted); font-size:.9rem}
  .nano-pulse{animation:pulse .5s ease-out}
  @keyframes pulse{0%{transform:scale(.98)}100%{transform:scale(1)}}
</style>

<script>
(function(){
  const root = document.getElementById('nano-tokeniser');
  const textEl = document.getElementById('nano-text');
  const XEl = document.getElementById('nano-X');
  const charsEl = document.getElementById('nano-chars');
  const mapEl = document.getElementById('nano-map');
  const TEl = document.getElementById('nano-T');
  const TLabel = document.getElementById('nano-T-label');
  const btn = document.getElementById('nano-build');
  const reset = document.getElementById('nano-reset');

  const V = 205;           // fixed vocab size
  const PAD_ID = 0;        // padding token id

  // Deterministic char → id in [1 .. V-1]
  function idForChar(ch){
    let h = 2166136261;
    for (let i=0;i<ch.length;i++){
      h ^= ch.charCodeAt(i);
      h = (h * 16777619) >>> 0;
    }
    return 1 + (h % (V-1));
  }

  function build(){
    let T = Math.max(4, parseInt(TEl.value || root.dataset.T, 10));
    TLabel.textContent = T;

    // normalize text (lowercase)
    let s = (textEl.value || '').toLowerCase();

    // render character tiles
    charsEl.innerHTML = '';
    Array.from(s).forEach((ch, i)=>{
      const d = document.createElement('div');
      d.className = 'nano-tile nano-pulse';
      d.textContent = ch === ' ' ? '␠' : ch;
      d.setAttribute('data-i', i);
      charsEl.appendChild(d);
    });

    // unique chars & mapping
    const uniq = Array.from(new Set(Array.from(s)));
    const map = new Map();
    uniq.forEach(ch => map.set(ch, idForChar(ch)));

    // sequence shaping: truncate/pad
    const arr = Array.from(s).slice(0, T).map(ch => map.get(ch) ?? idForChar(ch));
    while (arr.length < T) arr.push(PAD_ID);

    // render X
    XEl.textContent = `[ ${arr.join(', ')} ]`;

    // render mapping table
    mapEl.innerHTML = '';
    uniq.sort().forEach(ch=>{
      const row = document.createElement('div');
      row.className = 'nano-rowmap nano-pulse';
      const left = document.createElement('div');
      left.textContent = (ch === ' ' ? '␠' : ch);
      const right = document.createElement('div');
      right.textContent = '→ ' + map.get(ch);
      row.appendChild(left); row.appendChild(right);
      mapEl.appendChild(row);
    });
  }

  btn.addEventListener('click', build);
  reset.addEventListener('click', ()=>{
    textEl.value = 'the quick brown fox jumps over the lazy dog.';
    TEl.value = 32; build();
  });

  // initial render
  build();
})();
</script>




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

<!-- === Interactive: Embedding Lookup (Wte → TokEmb) — wide Wte, tall TokEmb === -->
<div class="nano-card" id="nano-embed" data-V="205" data-dmodel="16">
  <div class="nano-head">
    <h4 style="margin:0">Interactive · Embedding Lookup (Wte → TokEmb)</h4>
    <div class="nano-sub">
      Wte (shown <em>transposed</em>): rows = d_model (16), cols = ids (205). <br>
      TokEmb: rows = T (e.g., 32), cols = d_model (16).
    </div>
  </div>

  <div class="nano-row">
    <label class="nano-label">Token IDs (X) · shape (B,T) = (1,T)</label>
    <textarea class="nano-input" id="emb-x" rows="2" placeholder="[19, 8, 5, 42, ...]"></textarea>
    <div class="nano-note">Auto-fills from Tokenisation viz if present.</div>
  </div>

  <div class="nano-row nano-actions">
    <button class="nano-btn" id="emb-build">Build Wte & Preview</button>
    <button class="nano-btn" id="emb-play">Play Lookup</button>
    <button class="nano-btn ghost" id="emb-step">Step</button>
    <button class="nano-btn ghost" id="emb-reset">Reset</button>
    <div class="nano-note" style="margin-left:auto">Index: <span id="emb-idx">–</span> / <span id="emb-T">–</span></div>
  </div>

  <div class="nano-section">
    <div class="nano-label">Embedding Table Wte — <em>wide</em> (rows = d_model, cols = ids)</div>
    <div class="wte-viewport">
      <div class="wte-scale">
        <div class="wte-grid" id="wte"></div>
      </div>
    </div>
    <div class="nano-note">Blue ≈ negative, red ≈ positive. Top header = id 0..204. Left header = d0..d15.</div>
  </div>

  <div class="nano-arrow">↓ TokEmb = Wte[X] (copy selected ID column into row t)</div>

  <div class="nano-section">
    <div class="nano-label">TokEmb — <em>tall</em> (rows = T, cols = d_model = <span id="tok-dm">16</span>)</div>
    <div class="tok-wrap" id="tokemb"></div>
  </div>
</div>

<style>
  .nano-card{--bg:#f8fafc; --fg:#0b0e14; --muted:#4b5563; --accent:#2563eb; --line:#e5e7eb; --tile:#ffffff;
    border:1px solid var(--line); background:var(--bg); color:var(--fg);
    border-radius:16px; padding:18px; box-shadow:0 4px 18px rgba(0,0,0,.07); margin:1.25rem 0}
  .nano-head{display:flex; align-items:baseline; gap:.75rem}
  .nano-sub{color:var(--muted); font-size:.95rem}
  .nano-row{margin-top:12px}
  .nano-label{display:block; font-size:.9rem; color:var(--muted); margin-bottom:6px}
  .nano-input{width:100%; background:var(--tile); color:var(--fg); border:1px solid var(--line);
    border-radius:10px; padding:10px 12px; font-family:ui-monospace,Menlo,monospace}
  .nano-actions{display:flex; gap:8px; align-items:center; flex-wrap:wrap}
  .nano-btn{background:var(--accent); color:#fff; border:none; border-radius:10px; padding:8px 12px; font-weight:600; cursor:pointer}
  .nano-btn.ghost{background:transparent; color:var(--fg); border:1px solid var(--line)}
  .nano-section{margin-top:16px}
  .nano-arrow{margin:14px 0; text-align:center; color:var(--muted)}
  .nano-note{color:var(--muted); font-size:.9rem}

  /* Wte (wide) — no dead whitespace: height set dynamically via JS */
  .wte-viewport{
    border:1px solid var(--line); border-radius:12px; background:var(--tile);
    overflow:hidden; width:100%; position:relative;
  }
  .wte-scale{transform-origin: top left;}
  .wte-grid{display:grid; grid-auto-rows: 18px; font:12px ui-monospace,Menlo,monospace}
  .wte-hdr{background:#f3f4f6; border-right:1px solid var(--line); border-bottom:1px solid var(--line);
    display:flex; align-items:center; justify-content:center; height:24px}
  .wte-hdr.left{justify-content:flex-start; padding:0 6px}
  .wte-top{height:24px}
  .wte-left{background:#f6f7fb; border-right:1px solid var(--line); padding:0 6px; display:flex; align-items:center; color:#374151}
  .cell{border-right:1px solid #f0f1f5; border-bottom:1px solid #f0f1f5}
  .col-header-active{background:#dbeafe !important}

  /* TokEmb (transposed): rows = d_model, cols = T */
  .tok-wrap{ border:1px solid var(--line); border-radius:12px; background:var(--tile); padding:8px }
  .tok-grid{
    display:grid;
    grid-auto-rows: 20px;        /* row height for the 16 dims */
    width:100%;
    font:12px ui-monospace,Menlo,monospace;
  }
  .tok-hdr{
    background:#f3f4f6; border-right:1px solid var(--line); border-bottom:1px solid var(--line);
    display:flex; align-items:center; justify-content:center; height:24px
  }
  .tok-left{
    background:#f6f7fb; border-right:1px solid var(--line); padding:0 6px; display:flex; align-items:center; color:#374151
  }
  .tok-cell{ height:20px; border-right:1px solid #f0f1f5; border-bottom:1px solid #f0f1f5 }

  .pulse{animation:pulse .35s ease-out}
  @keyframes pulse{0%{transform:scale(.98)}100%{transform:scale(1)}}

</style>

<script>
(function(){
  const root = document.getElementById('nano-embed');
  const V  = parseInt(root.dataset.V, 10) || 205;
  const DM = parseInt(root.dataset.dmodel, 10) || 16;
  const PAD_ID = 0;

  const xArea   = document.getElementById('emb-x');
  const buildBtn= document.getElementById('emb-build');
  const playBtn = document.getElementById('emb-play');
  const stepBtn = document.getElementById('emb-step');
  const resetBtn= document.getElementById('emb-reset');
  const idxEl   = document.getElementById('emb-idx');
  const TEl     = document.getElementById('emb-T');

  const wteViewport = document.querySelector('.wte-viewport');
  const wteScale    = document.querySelector('.wte-scale');
  const wteEl       = document.getElementById('wte');
  const tokEl       = document.getElementById('tokemb');

  let WTE=[]; let X=[]; let T=0; let iStep=-1; let playing=null;
  let idHeaderCells=[];                 // top id headers for highlight
  let tokCells={};                      // key "t,j" -> cell node

  function charId(ch){ let h=2166136261; for (let i=0;i<ch.length;i++){ h^=ch.charCodeAt(i); h=(h*16777619)>>>0; } return 1+(h%(V-1)); }
  function vecForId(id){
    if (id===PAD_ID) return Array(DM).fill(0);
    const v=new Array(DM);
    for (let j=0;j<DM;j++){
      const x=Math.sin(id*12.9898 + (j+1)*78.233)*43758.5453; const f=x-Math.floor(x);
      v[j]=(f*2-1);
    }
    return v;
  }
  function valColor(a){
    const v=Math.max(-1,Math.min(1,a));
    const hue=v<0?210:10, sat=60*Math.abs(v)+20, light=92-40*Math.abs(v);
    return `hsl(${hue} ${sat}% ${light}%)`;
  }

  // Fit Wte to container width; set viewport height to exact scaled grid height
  function updateScale(){
    const natW = wteEl.scrollWidth;
    const natH = wteEl.scrollHeight;
    const boxW = wteViewport.clientWidth;
    const s = boxW / natW;                               // fit width
    wteScale.style.transform = `scale(${s})`;
    wteViewport.style.height = Math.ceil(natH * s) + 'px'; // exact, no dead space
  }

  function buildWTE(){
    WTE = Array.from({length: V}, (_, id)=>vecForId(id));

    // columns: 56px (left labels) + V * 18px (id columns)
    wteEl.style.gridTemplateColumns = '56px ' + '18px '.repeat(V);
    wteEl.innerHTML = '';
    idHeaderCells = [];

    // top-left corner
    const corner=document.createElement('div'); corner.className='wte-hdr left wte-top'; corner.textContent='dim/id';
    wteEl.appendChild(corner);
    // top headers: ids
    for (let id=0; id<V; id++){
      const h=document.createElement('div'); h.className='wte-hdr wte-top'; h.textContent=id;
      wteEl.appendChild(h); idHeaderCells[id]=h;
    }
    // rows: dims
    for (let j=0; j<DM; j++){
      const left=document.createElement('div'); left.className='wte-left'; left.textContent='d'+j; wteEl.appendChild(left);
      for (let id=0; id<V; id++){
        const c=document.createElement('div'); c.className='cell';
        c.style.background= id===PAD_ID ? '#eef2f7' : valColor(WTE[id][j]);
        wteEl.appendChild(c);
      }
    }
    updateScale();
  }

  function autofillX(){
    const xPrev=document.getElementById('nano-X');
    if (xPrev && xPrev.textContent.trim()){ xArea.value=xPrev.textContent.trim(); return; }
    const s='the quick brown fox jumps over the lazy dog.'.toLowerCase();
    const arr=Array.from(s).map(ch=> ch===' '?charId(' '):charId(ch));
    xArea.value=`[ ${arr.slice(0,32).join(', ')} ]`;
  }

  function parseX(){
    const nums=(xArea.value||'').match(/-?\d+/g);
    return nums?nums.map(n=>parseInt(n,10)).filter(n=>!Number.isNaN(n)):[];
  }

  function clearTok(){ tokEl.innerHTML=''; tokCells={}; }

  // TokEmb grid: tall (rows=T, cols=DM). Top headers = d0..d15; left labels = t0..t(T-1)
  function buildTokGrid(){
    clearTok();
    const grid=document.createElement('div'); grid.className='tok-grid';
    grid.style.gridTemplateColumns = '56px ' + '18px '.repeat(DM);

    // top-left corner
    const corner=document.createElement('div'); corner.className='tok-hdr'; corner.textContent='t/d';
    grid.appendChild(corner);
    // top headers: dims
    for (let j=0;j<DM;j++){ const h=document.createElement('div'); h.className='tok-hdr'; h.textContent='d'+j; grid.appendChild(h); }

    // rows: tokens t
    for (let t=0;t<T;t++){
      const left=document.createElement('div'); left.className='tok-left'; left.textContent='t'+t; grid.appendChild(left);
      for (let j=0;j<DM;j++){
        const d=document.createElement('div'); d.className='tok-cell'; d.id=`tok-${t}-${j}`;
        grid.appendChild(d); tokCells[`${t},${j}`]=d;
      }
    }

    tokEl.appendChild(grid);
    document.getElementById('tok-dm').textContent = DM;
  }

  function paintTokRow(t, vec){
    for (let j=0;j<DM;j++){
      const d = tokCells[`${t},${j}`]; if (!d) continue;
      d.style.background = valColor(vec[j]);
      d.classList.remove('pulse'); void d.offsetWidth; d.classList.add('pulse');
    }
  }

  function clearIdHighlights(){ idHeaderCells.forEach(h=>h && h.classList.remove('col-header-active')); }
  function highlightIdColumn(id){ const h=idHeaderCells[id]; if (h) h.classList.add('col-header-active'); }

  function stepOnce(){
    if (T===0) return;
    iStep = Math.min(iStep+1, T-1);
    idxEl.textContent = iStep+1;

    const id = X[iStep] ?? PAD_ID;
    clearIdHighlights(); highlightIdColumn(id);
    const vec = WTE[id];
    paintTokRow(iStep, vec);

    if (iStep>=T-1 && playing){ clearInterval(playing); playing=null; playBtn.textContent='Play Lookup'; }
  }

  function play(){
    if (playing){ clearInterval(playing); playing=null; playBtn.textContent='Play Lookup'; return; }
    playBtn.textContent='Pause'; playing=setInterval(stepOnce, 300);
  }

  function reset(){
    if (playing){ clearInterval(playing); playing=null; }
    iStep=-1; idxEl.textContent='–'; clearIdHighlights();
    Object.values(tokCells).forEach(c => c.style.background = '#fbfbfd');
  }

  function buildAll(){
    if (!WTE.length) buildWTE();
    X = parseX(); T = X.length; TEl.textContent = T;
    buildTokGrid(); reset();
  }

  buildBtn.addEventListener('click', buildAll);
  playBtn .addEventListener('click', play);
  stepBtn .addEventListener('click', stepOnce);
  resetBtn.addEventListener('click', reset);
  window.addEventListener('resize', updateScale);

  // init
  autofillX(); buildAll();
})();
</script>




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


<!-- === Interactive: Positional Encoding (Steps 6–8) — TokEmb + PosEmb → TokIn === -->
<div class="nano-card" id="nano-posenc" data-dmodel="16" data-tmax="32" data-tlimit="32">
  <div class="nano-head">
    <h4 style="margin:0">Interactive · Positional Encoding (Absolute)</h4>
    <div class="nano-sub">
      Wpe shape (T<sub>max</sub>, d_model) = (32, 16). We broadcast Wpe[0:T′] to match T′ tokens and add:
      <code>TokIn[t] = TokEmb[t] + PosEmb[t]</code>
    </div>
  </div>

  <div class="nano-row">
    <div class="nano-grid">
      <div>
        <label class="nano-label">Token index t (0 … <span id="pe-T">0</span>)</label>
        <input id="pe-slider" type="range" min="0" max="0" value="0" style="width:240px">
      </div>
      <div class="nano-actions">
        <button class="nano-btn" id="pe-play">Play</button>
        <button class="nano-btn ghost" id="pe-step">Step</button>
        <button class="nano-btn ghost" id="pe-reset">Reset</button>
        <label class="nano-label" style="margin-left:.75rem">
          <input type="checkbox" id="pe-values"> show values
        </label>
      </div>
    </div>
  </div>

  <div class="nano-section">
    <div class="nano-label">Dimensions d0…d15 (d_model = <span id="pe-dm">16</span>)</div>
    <div class="pe-dims" id="pe-dims"></div>
  </div>

  <div class="nano-section">
    <div class="rowtitle"><span class="dot blue"></span> TokEmb[t]  ·  shape (16)</div>
    <div class="bars" id="bars-emb"></div>
  </div>

  <div class="nano-section">
    <div class="rowtitle"><span class="dot orange"></span> PosEmb[t] = Wpe[t]  ·  shape (16)</div>
    <div class="bars" id="bars-pos"></div>
  </div>

  <div class="nano-section">
    <div class="rowtitle"><span class="dot purple"></span> TokIn[t] = TokEmb[t] + PosEmb[t]  ·  shape (16)</div>
    <div class="bars" id="bars-sum"></div>
  </div>
</div>

<style>
  .nano-card{--bg:#f8fafc; --fg:#0b0e14; --muted:#4b5563; --accent:#2563eb; --line:#e5e7eb; --tile:#ffffff;
    --blue:#3b82f6; --orange:#f59e0b; --purple:#8b5cf6;
    border:1px solid var(--line); background:var(--bg); color:var(--fg);
    border-radius:16px; padding:18px; box-shadow:0 4px 18px rgba(0,0,0,.07); margin:1.25rem 0}
  .nano-head{display:flex; align-items:baseline; gap:.75rem}
  .nano-sub{color:var(--muted); font-size:.95rem}
  .nano-row{margin-top:12px}
  .nano-label{display:block; font-size:.9rem; color:var(--muted); margin-bottom:6px}
  .nano-section{margin-top:14px}
  .nano-grid{display:flex; gap:16px; align-items:end; flex-wrap:wrap}
  .nano-actions{margin-left:auto; display:flex; align-items:center; gap:8px}
  .nano-btn{background:var(--accent); color:#fff; border:none; border-radius:10px; padding:8px 12px; font-weight:600; cursor:pointer}
  .nano-btn.ghost{background:transparent; color:var(--fg); border:1px solid var(--line)}
  .rowtitle{font-weight:600; margin:6px 0 6px 2px; display:flex; align-items:center; gap:.5rem}
  .dot{display:inline-block; width:10px; height:10px; border-radius:999px}
  .dot.blue{background:var(--blue)} .dot.orange{background:var(--orange)} .dot.purple{background:var(--purple)}

  /* dimension labels */
  .pe-dims{display:grid; grid-template-columns: 40px repeat(16, 1fr); gap:0}
  .pe-dims div{font:12px ui-monospace,Menlo,monospace; color:#374151; text-align:center}
  .pe-dims div:first-child{text-align:left; padding-left:6px}

  /* bars area */
  .bars{
    position:relative; height:140px; border:1px solid var(--line); border-radius:10px;
    background:var(--tile); display:grid; grid-template-columns: 40px repeat(16, 1fr); gap:0; overflow:hidden
  }
  .axis0{position:absolute; left:0; right:0; top:50%; height:1px; background:#e5e7eb}
  .barcell{position:relative; display:flex; align-items:flex-end; justify-content:center}
  .barlab{font:12px ui-monospace,Menlo,monospace; color:#374151; padding-left:6px; display:flex; align-items:center}
  .bar{width:60%; border-radius:6px 6px 0 0; transition:height .25s ease, transform .25s ease, background .25s ease}
  .bar.neg{border-radius:0 0 6px 6px}
  .val{position:absolute; top:4px; font:11px ui-monospace,Menlo,monospace; color:#111827; background:#ffffffbf; border:1px solid #e5e7eb; padding:0 4px; border-radius:6px; display:none}
  .showvals .val{display:block}
  /* colors */
  .bar.blue{background:var(--blue)} .bar.orange{background:var(--orange)} .bar.purple{background:var(--purple)}
</style>

<script>
(function(){
  const root = document.getElementById('nano-posenc');
  const DM   = parseInt(root.dataset.dmodel, 10) || 16;
  const TMAX = parseInt(root.dataset.tmax, 10) || 32;
  const TLIM = parseInt(root.dataset.tlimit, 10) || 8;
  const PAD_ID = 0;

  const slider = document.getElementById('pe-slider');
  const TOut   = document.getElementById('pe-T');
  const DMOut  = document.getElementById('pe-dm');
  const playBtn= document.getElementById('pe-play');
  const stepBtn= document.getElementById('pe-step');
  const resetBtn=document.getElementById('pe-reset');
  const showVals=document.getElementById('pe-values');

  const dimsEl = document.getElementById('pe-dims');
  const embBars= document.getElementById('bars-emb');
  const posBars= document.getElementById('bars-pos');
  const sumBars= document.getElementById('bars-sum');

  let playing=null, t=0, T=0, X=[], WTE=[], WPE=[];

  /* --- helpers: same deterministic choices as earlier blocks --- */
  function charId(ch){ let h=2166136261; for (let i=0;i<ch.length;i++){ h^=ch.charCodeAt(i); h=(h*16777619)>>>0; } return 1+(h%(205-1)); }
  function vecForId(id){
    if (id===PAD_ID) return Array(DM).fill(0);
    const v=new Array(DM);
    for (let j=0;j<DM;j++){
      const x=Math.sin(id*12.9898 + (j+1)*78.233)*43758.5453; const f=x-Math.floor(x);
      v[j]=(f*2-1);
    }
    return v;
  }
  // Absolute PE (toy deterministic, smoothly varying with t and j)
  function peVec(t){
    const v=new Array(DM);
    for (let j=0;j<DM;j++){
      const a=Math.sin((t+1)*0.35 + (j+1)*0.55);
      const b=Math.cos((t+1)*0.12 + (j+1)*0.18);
      v[j]=0.6*a + 0.4*b;       // in [-1,1] approximately
    }
    return v;
  }

  function valClip(x){ return Math.max(-1, Math.min(1, x)); }
  function fmt(x){ return (Math.round(x*100)/100).toFixed(2); }

  /* --- build static dimension headers --- */
  function buildDimHeader(){
    dimsEl.innerHTML='';
    const lab=document.createElement('div'); lab.textContent='dim:'; dimsEl.appendChild(lab);
    for (let j=0;j<DM;j++){ const d=document.createElement('div'); d.textContent='d'+j; dimsEl.appendChild(d); }
  }

  /* --- build bar rows (3 stacks) --- */
  function buildBars(container, color){
    container.innerHTML='';
    // left label column
    const lab=document.createElement('div'); lab.className='barlab'; lab.textContent='';
    container.appendChild(lab);
    // axis 0 line
    const axis=document.createElement('div'); axis.className='axis0'; container.appendChild(axis);
    for (let j=0;j<DM;j++){
      const cell=document.createElement('div'); cell.className='barcell';
      const bar=document.createElement('div'); bar.className='bar '+color;
      const val=document.createElement('div'); val.className='val'; val.textContent='0.00';
      cell.appendChild(bar); cell.appendChild(val); container.appendChild(cell);
    }
  }

  function setRowLabel(container, text){ container.querySelector('.barlab').textContent=text; }

  function paintBars(container, vec, color){
    const cells=[...container.querySelectorAll('.barcell')];
    for (let j=0;j<DM;j++){
      const v=valClip(vec[j]);
      const bar=cells[j].querySelector('.bar');
      const val=cells[j].querySelector('.val');
      const h=Math.abs(v)*100;    // % of half-height (we stretch around center)
      if (v>=0){
        bar.classList.remove('neg');
        bar.style.transform='translateY('+ (50 - h/2) +'%)';
        bar.style.height = (h/2)+'%';
      } else {
        bar.classList.add('neg');
        bar.style.transform='translateY(50%)';
        bar.style.height = (h/2)+'%';
      }
      bar.classList.remove('blue','orange','purple'); bar.classList.add(color);
      val.textContent = fmt(v);
    }
  }

  function toggleValues(){
    [embBars,posBars,sumBars].forEach(el=>{
      el.classList[showVals.checked ? 'add':'remove']('showvals');
    });
  }

  /* --- derive X, WTE, WPE --- */
  function loadX(){
    const xPrev=document.getElementById('nano-X');
    let arr=[];
    if (xPrev && xPrev.textContent.trim()){
      const nums=xPrev.textContent.match(/-?\d+/g);
      if (nums) arr=nums.map(n=>parseInt(n,10));
    } else {
      const s='the quick brown fox jumps over the lazy dog.'.toLowerCase();
      arr=Array.from(s).map(ch=> ch===' '?charId(' '):charId(ch));
    }
    X = arr.slice(0, TLIM);
    T = X.length; slider.max = Math.max(0, T-1); slider.value=0;
    TOut.textContent = T-1; // max index
  }

  function buildTables(){
    WTE = Array.from({length:205}, (_,id)=>vecForId(id));
    WPE = Array.from({length:TMAX}, (_,tt)=>peVec(tt));
  }

  function refresh(){
    // vectors at current t
    const id = X[t] ?? 0;
    const emb = WTE[id];
    const pos = WPE[t];
    const sum = emb.map((e,j)=> valClip(e + pos[j]));
    paintBars(embBars, emb, 'blue');
    paintBars(posBars, pos, 'orange');
    paintBars(sumBars, sum, 'purple');
    setRowLabel(embBars, `TokEmb[t=${t}]  (id=${id})`);
    setRowLabel(posBars, `PosEmb[t=${t}]`);
    setRowLabel(sumBars, `TokIn[t=${t}]`);
  }

  function step(){
    t = Math.min(t+1, T-1);
    slider.value = t;
    refresh();
  }
  function play(){
    if (playing){ clearInterval(playing); playing=null; playBtn.textContent='Play'; return; }
    playBtn.textContent='Pause';
    playing = setInterval(()=>{ if (t>=T-1){ clearInterval(playing); playing=null; playBtn.textContent='Play'; return; } step(); }, 350);
  }
  function reset(){
    if (playing){ clearInterval(playing); playing=null; playBtn.textContent='Play'; }
    t = 0; slider.value=0; refresh();
  }

  /* init */
  buildDimHeader();
  buildBars(embBars, 'blue'); buildBars(posBars, 'orange'); buildBars(sumBars, 'purple');
  loadX();
  buildTables();
  DMOut.textContent = DM;
  refresh();

  /* events */
  slider.addEventListener('input', e=>{ t=parseInt(e.target.value,10)||0; refresh(); });
  stepBtn.addEventListener('click', step);
  playBtn.addEventListener('click', play);
  resetBtn.addEventListener('click', reset);
  showVals.addEventListener('change', toggleValues);
})();
</script>



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



<!-- === Interactive: Self-Attention (Steps 9–10) — Scores/Weights + Mask + Arrows === -->
<div class="nano-card" id="nano-attn" data-dmodel="16" data-dhead="16" data-tlimit="8">
  <div class="nano-head">
    <h4 style="margin:0">Interactive · Self-Attention (1 head)</h4>
    <div class="nano-sub">
      Q,K ∈ ℝ<sup>T×d_head</sup> · scores = QKᵀ/√d<sub>head</sub> → softmax(row-wise). Toggle <b>mask</b> to enforce j &le; i.
    </div>
  </div>

  <div class="nano-row nano-grid">
    <div>
      <label class="nano-label">Query index i</label>
      <input id="attn-slider" type="range" min="0" max="0" value="0" style="width:240px">
    </div>
    <div class="nano-actions">
      <button class="nano-btn" id="attn-play">Play</button>
      <button class="nano-btn ghost" id="attn-step">Step</button>
      <label class="nano-label"><input type="checkbox" id="attn-mask" checked> causal mask</label>
      <label class="nano-label"><input type="radio" name="attn-mode" value="scores"> scores</label>
      <label class="nano-label"><input type="radio" name="attn-mode" value="weights" checked> weights</label>
    </div>
  </div>

  <!-- Tokens row + arrows -->
  <div class="nano-section">
    <div class="nano-label">Tokens (T′ ≤ 8). Thick arrows = higher attention weight.</div>
    <div class="attn-tokens" id="attn-tokens">
      <svg id="attn-svg" class="attn-svg" preserveAspectRatio="none"></svg>
    </div>
  </div>

  <!-- Heatmap -->
  <div class="nano-section">
    <div class="nano-label">Attention Matrix (rows = queries i, cols = keys j)</div>
    <div class="attn-grid" id="attn-grid"></div>
    <div class="nano-note">
      Masked cells (j &gt; i) are dark. Switch between <b>scores</b> (diverging colors, ±) and <b>weights</b> (0..1, light→dark).
    </div>
  </div>
</div>

<style>
  .nano-card{--bg:#f8fafc; --fg:#0b0e14; --muted:#4b5563; --accent:#2563eb; --line:#e5e7eb; --tile:#ffffff;
    border:1px solid var(--line); background:var(--bg); color:var(--fg);
    border-radius:16px; padding:18px; box-shadow:0 4px 18px rgba(0,0,0,.07); margin:1.25rem 0}
  .nano-head{display:flex; align-items:baseline; gap:.75rem}
  .nano-sub{color:var(--muted); font-size:.95rem}
  .nano-row{margin-top:12px}
  .nano-label{display:inline-flex; gap:.35rem; align-items:center; font-size:.9rem; color:var(--muted); margin-bottom:6px}
  .nano-grid{display:flex; gap:16px; align-items:end; flex-wrap:wrap}
  .nano-actions{margin-left:auto; display:flex; align-items:center; gap:10px; flex-wrap:wrap}
  .nano-btn{background:var(--accent); color:#fff; border:none; border-radius:10px; padding:8px 12px; font-weight:600; cursor:pointer}
  .nano-btn.ghost{background:transparent; color:var(--fg); border:1px solid var(--line)}
  .nano-section{margin-top:16px}
  .nano-note{color:var(--muted); font-size:.9rem}

  /* Tokens + arrows */
  .attn-tokens{position:relative; border:1px solid var(--line); border-radius:12px; background:var(--tile); padding:12px}
  .attn-token{position:absolute; transform:translate(-50%, -50%); font:12px ui-monospace,Menlo,monospace;
    background:#f3f4f6; border:1px solid #e5e7eb; border-radius:8px; padding:3px 6px}
  .attn-token.active{background:#dbeafe; border-color:#bfdbfe}
  .attn-svg{width:100%; height:120px; display:block}
  .attn-arrow{fill:none; stroke:#7c3aed; opacity:.7}
  .attn-arrow.dim{opacity:.25}
  .attn-arrow.hl{stroke:#dc2626; opacity:.95}

  /* Heatmap (T'×T') + headers */
  .attn-grid{
    --cell:28px;
    display:grid;
    grid-template-columns: 44px repeat(var(--T), var(--cell));
    grid-auto-rows: var(--cell);
    width:100%; border:1px solid var(--line); border-radius:12px; overflow:hidden; background:var(--tile);
    font:12px ui-monospace,Menlo,monospace;
  }
  .ag-hdr{background:#f3f4f6; border-right:1px solid var(--line); border-bottom:1px solid var(--line);
    display:flex; align-items:center; justify-content:center}
  .ag-left{background:#f6f7fb; border-right:1px solid var(--line); display:flex; align-items:center; justify-content:center}
  .ag-cell{border-right:1px solid #f0f1f5; border-bottom:1px solid #f0f1f5; cursor:pointer}
  .masked{background:#0b0e14 !important}
  .ag-cell.hl{outline:2px solid #0ea5e9; outline-offset:-2px}
</style>

<script>
(function(){
  const root = document.getElementById('nano-attn');
  const DM   = parseInt(root.dataset.dmodel, 10) || 16;
  const DH   = parseInt(root.dataset.dhead, 10) || DM;
  const TLIM = parseInt(root.dataset.tlimit, 10) || 8;

  const slider = document.getElementById('attn-slider');
  const playBtn= document.getElementById('attn-play');
  const stepBtn= document.getElementById('attn-step');
  const maskChk= document.getElementById('attn-mask');
  const modeRad= [...document.querySelectorAll('input[name="attn-mode"]')];

  const tokensBox = document.getElementById('attn-tokens');
  const svg       = document.getElementById('attn-svg');
  const grid      = document.getElementById('attn-grid');

  let X=[], T=0, i=0, playing=null;
  let Q=[], K=[], scores=[], weights=[];
  let tokenNodes=[], cellNodes=[], idToCell={};

  /* ---------- Helpers: deterministic vectors & weights ---------- */
  function charId(ch){ let h=2166136261; for (let i=0;i<ch.length;i++){ h^=ch.charCodeAt(i); h=(h*16777619)>>>0; } return 1+(h%(205-1)); }
  function wte(id,j){ if (id===0) return 0; const x=Math.sin(id*12.9898 + (j+1)*78.233)*43758.5453; return ((x-Math.floor(x))*2-1); }
  function wpe(t,j){ const a=Math.sin((t+1)*0.35 + (j+1)*0.55), b=Math.cos((t+1)*0.12 + (j+1)*0.18); return 0.6*a+0.4*b; }

  // simple layer norm
  function layerNorm(v){ const m=v.reduce((a,b)=>a+b,0)/v.length; const c=v.map(x=>x-m); const varr=c.reduce((a,b)=>a+b*b,0)/v.length; const s=Math.sqrt(varr+1e-5); return c.map(x=>x/s); }

  // seeded PRNG for WQ/WK
  let seed=12345; function rnd(){ seed = (1664525*seed + 1013904223)>>>0; return (seed/4294967296); }
  const WQ=Array.from({length:DM},()=>Array.from({length:DH},()=> (rnd()*2-1)*0.7));
  const WK=Array.from({length:DM},()=>Array.from({length:DH},()=> (rnd()*2-1)*0.7));

  function matVec(M, v){ // (DM×DH)ᵀ? Here M is DM×DH, v is DM
    const out=new Array(DH).fill(0);
    for (let d=0; d<DH; d++){
      let s=0; for (let j=0;j<DM;j++) s += v[j]*M[j][d];
      out[d]=s;
    }
    return out;
  }
  function dot(a,b){ let s=0; for (let k=0;k<a.length;k++) s+=a[k]*b[k]; return s; }
  function softmaxRow(arr, maskUpTo){ // maskUpTo = i (only j<=i kept)
    const vals=arr.map((x,j)=> j<=maskUpTo ? x : -Infinity);
    const m=Math.max(...vals);
    const ex=vals.map(x=>x>-1e9 ? Math.exp(x-m) : 0);
    const Z=ex.reduce((a,b)=>a+b,0)||1;
    return ex.map(e=>e/Z);
  }

  // Colors: diverging for scores, sequential for weights
  function colDiverge(x, maxAbs){ // normalize to [-1,1]
    if (maxAbs<=1e-8) return '#eee';
    const v=Math.max(-1, Math.min(1, x/maxAbs));
    const hue=v<0?210:10, sat=60*Math.abs(v)+20, light=92-40*Math.abs(v);
    return `hsl(${hue} ${sat}% ${light}%)`;
  }
  function colSequential(w){ // 0..1 purple scale
    const v=Math.max(0, Math.min(1, w));
    const light=96 - 60*v; const sat=25 + 60*v;
    return `hsl(265 ${sat}% ${light}%)`;
  }

  /* ---------- Build data from X ---------- */
  function getX(){
    const prev=document.getElementById('nano-X');
    let arr=[];
    if (prev && prev.textContent.trim()){
      const nums=prev.textContent.match(/-?\d+/g);
      if (nums) arr=nums.map(n=>parseInt(n,10));
    } else {
      const s='the quick brown fox jumps over the lazy dog.'.toLowerCase();
      arr=Array.from(s).map(ch=> ch===' '?charId(' '):charId(ch));
    }
    X = arr.slice(0, TLIM);
    T = X.length;
  }

  function buildQK(){
    Q=Array.from({length:T}, ()=>Array(DH).fill(0));
    K=Array.from({length:T}, ()=>Array(DH).fill(0));
    for (let t=0;t<T;t++){
      const emb=Array.from({length:DM}, (_,j)=> wte(X[t], j));
      const pos=Array.from({length:DM}, (_,j)=> wpe(t, j));
      const h0 = layerNorm( emb.map((e,j)=> e + pos[j]) );
      Q[t] = matVec(WQ, h0);
      K[t] = matVec(WK, h0);
    }
  }

  function buildScoresWeights(){
    const srs = Array.from({length:T}, ()=>Array(T).fill(0));
    let maxAbs=1e-9;
    for (let a=0;a<T;a++){
      for (let b=0;b<T;b++){
        srs[a][b] = dot(Q[a], K[b]) / Math.sqrt(DH);
        maxAbs = Math.max(maxAbs, Math.abs(srs[a][b]));
      }
    }
    scores = srs;
    weights = srs.map((row,i)=> softmaxRow(row, maskChk.checked ? i : T-1));
    return maxAbs;
  }

  /* ---------- Tokens row + SVG arrows ---------- */
  function tokensLayout(){
    tokensBox.querySelectorAll('.attn-token').forEach(n=>n.remove());
    const W = tokensBox.clientWidth;
    const H = 120;
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.innerHTML = '';
    const y1 = H*0.15, y2 = H*0.85;

    const xs = [];
    for (let t=0;t<T;t++){
      const x = (W*(t+1))/(T+1);
      xs.push(x);
      // token nodes (top for query i, bottom for keys j)
      const top = document.createElement('div');
      top.className = 'attn-token' + (t===i ? ' active':'');
      top.style.left = x+'px'; top.style.top = (y1)+'px';
      top.textContent = `t${t}`;
      tokensBox.appendChild(top);

      const bot = document.createElement('div');
      bot.className = 'attn-token';
      bot.style.left = x+'px'; bot.style.top = (y2)+'px';
      bot.textContent = `t${t}`;
      tokensBox.appendChild(bot);
    }

    // draw arrows for current i
    for (let j=0;j<T;j++){
      const w = weights[i][j];
      const masked = maskChk.checked && j>i;
      const sw = Math.max(1, 10 * w);
      const path = document.createElementNS('http://www.w3.org/2000/svg','path');
      const x1 = xs[i], x2 = xs[j];
      const c1 = x1, c2 = x2;
      const d = `M ${x1} ${y1+10} C ${c1} ${H*0.5}, ${c2} ${H*0.5}, ${x2} ${y2-10}`;
      path.setAttribute('d', d);
      path.setAttribute('class', 'attn-arrow' + ((masked)?' dim':''));
      path.setAttribute('stroke-width', sw.toFixed(2));
      svg.appendChild(path);
    }
  }

  /* ---------- Heatmap ---------- */
  function buildGrid(){
    grid.style.setProperty('--T', T);
    grid.innerHTML = '';
    // corner
    const corner = document.createElement('div'); corner.className='ag-hdr'; corner.textContent='i\\j';
    grid.appendChild(corner);
    // top headers j
    for (let j=0;j<T;j++){ const h=document.createElement('div'); h.className='ag-hdr'; h.textContent=j; grid.appendChild(h); }
    // rows
    cellNodes=[]; idToCell={};
    let maxAbs = buildScoresWeights();
    const mode = document.querySelector('input[name="attn-mode"]:checked').value;

    for (let r=0;r<T;r++){
      const left=document.createElement('div'); left.className='ag-left'; left.textContent=r; grid.appendChild(left);
      for (let c=0;c<T;c++){
        const cell=document.createElement('div'); cell.className='ag-cell';
        const masked = maskChk.checked && c>r;
        let color;
        if (mode === 'scores'){
          color = masked ? '#0b0e14' : colDiverge(scores[r][c], maxAbs);
        } else {
          color = masked ? '#0b0e14' : colSequential(weights[r][c]);
        }
        cell.style.background = color;
        cell.dataset.i = r; cell.dataset.j = c;
        cell.addEventListener('mouseenter', ()=>highlightCell(r,c));
        cell.addEventListener('mouseleave', ()=>clearHighlight());
        grid.appendChild(cell);
        cellNodes.push(cell);
        idToCell[`${r},${c}`]=cell;
      }
    }
  }

  function refreshAll(){
    buildScoresWeights();
    tokensLayout();
    buildGrid();
  }

  function highlightCell(ri,rj){
    // heatmap highlight
    const cell = idToCell[`${ri},${rj}`];
    if (cell) cell.classList.add('hl');
    // set query index to ri and redraw arrows emphasizing edge (ri→rj)
    i = ri; slider.value=i;
    tokensLayout();
    // emphasize one arrow
    const arrows = svg.querySelectorAll('.attn-arrow');
    arrows.forEach((p,idx)=>{
      const j = idx; // appended in order j=0..T-1
      if (j===rj) p.classList.add('hl'); else p.classList.remove('hl');
    });
  }

  function clearHighlight(){
    cellNodes.forEach(c=>c.classList.remove('hl'));
    tokensLayout();
  }

  /* ---------- Controls ---------- */
  function step(){
    i = Math.min(i+1, T-1);
    slider.value = i;
    tokensLayout();
  }
  function play(){
    if (playing){ clearInterval(playing); playing=null; playBtn.textContent='Play'; return; }
    playBtn.textContent='Pause';
    playing = setInterval(()=>{ if (i>=T-1){ clearInterval(playing); playing=null; playBtn.textContent='Play'; return; } step(); }, 450);
  }

  modeRad.forEach(r=>r.addEventListener('change', refreshAll));
  maskChk.addEventListener('change', refreshAll);
  stepBtn.addEventListener('click', step);
  playBtn.addEventListener('click', play);
  slider.addEventListener('input', e=>{ i=parseInt(e.target.value,10)||0; tokensLayout(); });

  /* ---------- Init ---------- */
  function init(){
    getX();
    T = X.length;
    i = 0;
    slider.max = Math.max(0, T-1);
    slider.value = 0;
    buildQK();
    refreshAll();
    window.addEventListener('resize', tokensLayout);
  }
  init();
})();
</script>




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

<!-- === Interactive: Residual & MLP — equal-height middle panel (no whitespace) === -->
<div class="nano-card" id="nano-resmlp" data-dmodel="16" data-dff="64" data-tlimit="8">
  <div class="nano-head">
    <h4 style="margin:0">Interactive · Residual & MLP (position-wise)</h4>
    <div class="nano-sub">
      All grids are rendered as <b>rows = dimension</b>, <b>cols = T′</b>. We keep T′ = 8 for clarity.
    </div>
  </div>

  <div class="nano-row nano-grid">
    <div>
      <label class="nano-label">Token index t (0 … <span id="rm-Tmax">0</span>)</label>
      <input id="rm-slider" type="range" min="0" max="0" value="0" style="width:240px">
    </div>
    <div class="nano-actions">
      <button class="nano-btn" id="rm-play">Play</button>
      <button class="nano-btn ghost" id="rm-step">Step</button>
      <button class="nano-btn ghost" id="rm-reset">Reset</button>
      <label class="nano-label" style="margin-left:.75rem">
        <input type="checkbox" id="rm-values"> show values
      </label>
    </div>
  </div>

  <!-- Residual: TokIn + AttnProj → H1 -->
  <div class="nano-section">
    <div class="rowtitle">Residual connection: <code>H1 = TokIn + AttnProj</code></div>

    <div class="rm-row">
      <div class="hm">
        <div class="hm-title">TokIn (d=16 × T′)</div>
        <div class="hm-grid hm16" id="hm-tokin"></div>
      </div>

      <div class="op-col">
        <div class="op-badge plus" id="rm-plus1">+</div>
        <div class="op-arrow">→</div>
      </div>

      <div class="hm">
        <div class="hm-title">AttnProj (d=16 × T′)</div>
        <div class="hm-grid hm16" id="hm-attnproj"></div>
      </div>

      <div class="op-col">
        <div class="op-badge eq">=</div>
        <div class="op-arrow">→</div>
      </div>

      <div class="hm">
        <div class="hm-title">H1 = TokIn + AttnProj</div>
        <div class="hm-grid hm16" id="hm-h1"></div>
      </div>
    </div>
  </div>

  <!-- MLP: equal-height middle panel -->
  <div class="nano-section">
    <div class="rowtitle">Position-wise MLP: <code>H2 = H1 + W2(GELU(LN(H1)·W1))</code></div>

    <div class="rm-row mlprow">
      <div class="hm">
        <div class="hm-title">H2_in = LN(H1)</div>
        <div class="hm-grid hm16" id="hm-h2in"></div>
      </div>

      <div class="op-col">
        <div class="op-badge op">·W1</div>
        <div class="op-arrow">→</div>
      </div>

      <div class="hm">
        <div class="hm-title">MLP_hidden (d=64 × T′)</div>
        <!-- This tall grid will be auto-scaled to match H2_in’s grid height -->
        <div class="hm-grid hm64" id="hm-mlphid"></div>
      </div>

      <div class="op-col">
        <div class="op-badge op">GELU</div>
        <div class="op-arrow">→</div>
        <div class="op-badge op">·W2</div>
        <div class="op-arrow">→</div>
      </div>

      <div class="hm">
        <div class="hm-title">MLP_out (d=16 × T′)</div>
        <div class="hm-grid hm16" id="hm-mlpout"></div>
      </div>
    </div>

    <div class="rm-row mlprow">
      <div class="hm">
        <div class="hm-title">H1 (for skip)</div>
        <div class="hm-grid hm16" id="hm-h1-skip"></div>
      </div>

      <div class="op-col">
        <div class="op-badge plus" id="rm-plus2">+</div>
        <div class="op-arrow">→</div>
      </div>

      <div class="hm">
        <div class="hm-title">H2 = H1 + MLP_out</div>
        <div class="hm-grid hm16" id="hm-h2"></div>
      </div>

      <!-- spacer cells for 5-column grid -->
      <div style="display:none"></div>
      <div style="display:none"></div>
    </div>
  </div>
</div>

<style>
  /* Card shell (light theme) */
  .nano-card{--bg:#f8fafc; --fg:#0b0e14; --muted:#4b5563; --accent:#2563eb; --line:#e5e7eb; --tile:#ffffff;
    border:1px solid var(--line); background:var(--bg); color:var(--fg);
    border-radius:16px; padding:18px; box-shadow:0 4px 18px rgba(0,0,0,.07); margin:1.25rem 0}
  .nano-head{display:flex; align-items:baseline; gap:.75rem}
  .nano-sub{color:var(--muted); font-size:.95rem}
  .nano-row{margin-top:12px}
  .nano-label{display:inline-flex; gap:.35rem; align-items:center; font-size:.9rem; color:#6b7280; margin-bottom:6px}
  .nano-grid{display:flex; gap:16px; align-items:end; flex-wrap:wrap}
  .nano-actions{margin-left:auto; display:flex; align-items:center; gap:10px; flex-wrap:wrap}
  .nano-btn{background:var(--accent); color:#fff; border:none; border-radius:10px; padding:8px 12px; font-weight:600; cursor:pointer}
  .nano-btn.ghost{background:transparent; color:#111827; border:1px solid var(--line)}
  .nano-section{margin-top:16px}
  .rowtitle{font-weight:600; margin:6px 0 8px 2px}

  /* Heatmaps */
  .rm-row{display:grid; grid-template-columns: 1fr 28px 1fr 28px 1fr; gap:12px; align-items:center}
  .rm-row.mlprow{grid-template-columns: 1.05fr 24px 1.20fr 24px 1.05fr; gap:8px}
  .hm{border:1px solid var(--line); border-radius:12px; background:var(--tile); padding:8px}
  .rm-row.mlprow .hm{padding:6px}
  .hm-title{font-size:.9rem; color:#374151; margin-bottom:6px}
  .rm-row.mlprow .hm-title{margin-bottom:4px}

  .hm-grid{display:grid; grid-auto-rows:18px; border:1px solid var(--line); border-radius:10px; overflow:hidden; background:#fff}
  .hm16{grid-template-columns: 44px repeat(var(--T), 1fr)}
  .hm64{grid-template-columns: 44px repeat(var(--T), 1fr); grid-auto-rows:5px} /* many rows → smaller natural height */
  .hm-hdr{background:#f3f4f6; border-right:1px solid var(--line); border-bottom:1px solid var(--line); display:flex; align-items:center; justify-content:center; height:22px}
  .hm-left{background:#f6f7fb; border-right:1px solid var(--line); display:flex; align-items:center; justify-content:center; font:12px ui-monospace,Menlo,monospace}
  .cell{border-right:1px solid #f0f1f5; border-bottom:1px solid #f0f1f5; position:relative}
  .flash{animation:flash .35s ease-out}
  @keyframes flash{0%{transform:scale(.98)}100%{transform:scale(1)}}

  /* Operators */
  .op-col{display:flex; flex-direction:column; align-items:center; gap:6px; min-width:24px}
  .op-badge{background:#eef2ff; color:#3f3f46; border:1px solid #e5e7eb; border-radius:999px; padding:4px 10px; font:12px ui-monospace,Menlo,monospace}
  .op-badge.plus{background:#dcfce7; border-color:#bbf7d0}
  .op-badge.eq{background:#fee2e2; border-color:#fecaca}
  .op-badge.op{background:#f1f5f9; border-color:#e2e8f0}
  .op-badge.active{box-shadow:0 0 0 6px rgba(59,130,246,.15); transform:scale(1.06); transition:.25s}
  .op-arrow{font-weight:700; color:#6b7280; text-align:center}

  /* Value overlay toggle */
  .val{display:none; position:absolute; top:2px; left:2px; font:11px ui-monospace,Menlo,monospace; color:#111827; background:#ffffffbf; border:1px solid #e5e7eb; padding:0 4px; border-radius:6px}
  .showvals .val{display:block}
</style>

<script>
(function(){
  const root = document.getElementById('nano-resmlp');
  const DM   = parseInt(root.dataset.dmodel, 10) || 16;
  const DFF  = parseInt(root.dataset.dff, 10) || 64;
  const TLIM = parseInt(root.dataset.tlimit, 10) || 8;

  const slider = document.getElementById('rm-slider');
  const playBtn= document.getElementById('rm-play');
  const stepBtn= document.getElementById('rm-step');
  const resetBtn=document.getElementById('rm-reset');
  const showVals=document.getElementById('rm-values');
  const TmaxOut = document.getElementById('rm-Tmax');

  const grids = {
    tokin:   document.getElementById('hm-tokin'),
    attnproj:document.getElementById('hm-attnproj'),
    h1:      document.getElementById('hm-h1'),
    h2in:    document.getElementById('hm-h2in'),
    mlphid:  document.getElementById('hm-mlphid'),
    mlpout:  document.getElementById('hm-mlpout'),
    h1skip:  document.getElementById('hm-h1-skip'),
    h2:      document.getElementById('hm-h2'),
  };

  const plus1 = document.getElementById('rm-plus1');
  const plus2 = document.getElementById('rm-plus2');

  let X=[], T=0, t=0, playing=null;
  let TokIn=[], H0=[], Q=[], K=[], Vv=[], weights=[], AttnOut=[], AttnProj=[], H1=[], H2_in=[], MLP_hid=[], MLP_out=[], H2=[];

  /* ---------- helpers ---------- */
  function charId(ch){ let h=2166136261; for (let i=0;i<ch.length;i++){ h^=ch.charCodeAt(i); h=(h*16777619)>>>0; } return 1+(h%(205-1)); }
  function vecForId(id){ if(id===0) return Array(DM).fill(0);
    const v=new Array(DM); for(let j=0;j<DM;j++){ const x=Math.sin(id*12.9898+(j+1)*78.233)*43758.5453; const f=x-Math.floor(x); v[j]=(f*2-1); }
    return v;
  }
  function wpe(t,j){ const a=Math.sin((t+1)*0.35+(j+1)*0.55), b=Math.cos((t+1)*0.12+(j+1)*0.18); return 0.6*a+0.4*b; }
  function layerNorm(v){ const m=v.reduce((a,b)=>a+b,0)/v.length; const c=v.map(x=>x-m); const varr=c.reduce((a,b)=>a+b*b,0)/v.length; const s=Math.sqrt(varr+1e-5); return c.map(x=>x/s); }
  function gelu(x){ return 0.5*x*(1+Math.tanh(Math.sqrt(2/Math.PI)*(x+0.044715*Math.pow(x,3)))); }
  function softmaxRow(arr){ const m=Math.max(...arr); const ex=arr.map(x=>Math.exp(x-m)); const Z=ex.reduce((a,b)=>a+b,0)||1; return ex.map(e=>e/Z); }
  function dot(a,b){ let s=0; for(let k=0;k<a.length;k++) s+=a[k]*b[k]; return s; }
  function valColor(a){ const v=Math.max(-1,Math.min(1,a)); const hue=v<0?210:10, sat=60*Math.abs(v)+20, light=92-40*Math.abs(v); return `hsl(${hue} ${sat}% ${light}%)`; }
  function clip(x){ return Math.max(-1, Math.min(1, x)); }
  function fmt(x){ return (Math.round(x*100)/100).toFixed(2); }

  // PRNG and weights for projections
  let seed=10101; function rnd(){ seed=(1664525*seed+1013904223)>>>0; return seed/4294967296; }
  const WQ=Array.from({length:DM},()=>Array.from({length:DM},()=> (rnd()*2-1)*0.7));
  const WK=Array.from({length:DM},()=>Array.from({length:DM},()=> (rnd()*2-1)*0.7));
  const WV=Array.from({length:DM},()=>Array.from({length:DM},()=> (rnd()*2-1)*0.7));
  const WO=Array.from({length:DM},()=>Array.from({length:DM},()=> (rnd()*2-1)*0.7));
  const W1=Array.from({length:DM},()=>Array.from({length:DFF},()=> (rnd()*2-1)*0.6)); // 16→64
  const W2=Array.from({length:DFF},()=>Array.from({length:DM},()=> (rnd()*2-1)*0.6)); // 64→16

  function matMulRow(v, M){ const D2=M[0].length; const out=new Array(D2).fill(0);
    for(let d=0; d<D2; d++){ let s=0; for(let j=0;j<DM;j++) s+=v[j]*M[j][d]; out[d]=s; } return out;
  }
  function matMulRowDFF(v, M){ const out=new Array(DFF).fill(0);
    for(let d=0; d<DFF; d++){ let s=0; for(let j=0;j<DM;j++) s+=v[j]*M[j][d]; out[d]=s; } return out;
  }
  function matMulRowBack(v, M){ const out=new Array(DM).fill(0);
    for(let d=0; d<DM; d++){ let s=0; for(let j=0;j<DFF;j++) s+=v[j]*M[j][d]; out[d]=s; } return out;
  }

  /* ---------- DOM builders ---------- */
  const cell = (r,c,id)=>{ const d=document.createElement('div'); d.className='cell'; d.id=id;
    d.style.background='#fbfbfd'; const v=document.createElement('div'); v.className='val'; v.textContent='0.00'; d.appendChild(v); return d; };

  function buildGrid(el, rows, cols, topLab, leftPrefix, idPrefix){
    el.style.setProperty('--T', cols);
    el.innerHTML='';
    // corner
    const corner=document.createElement('div'); corner.className='hm-hdr'; corner.textContent=topLab; el.appendChild(corner);
    // top headers: t0..t{T-1}
    for(let c=0;c<cols;c++){ const h=document.createElement('div'); h.className='hm-hdr'; h.textContent='t'+c; el.appendChild(h); }
    // rows
    for(let r=0;r<rows;r++){
      const left=document.createElement('div'); left.className='hm-left'; left.textContent=leftPrefix+(r<10?('0'+r):r); el.appendChild(left);
      for(let c=0;c<cols;c++) el.appendChild(cell(r,c,`${idPrefix}-${r}-${c}`));
    }
  }

  function paintCol(prefix, col, vec){
    for(let r=0;r<vec.length;r++){
      const d=document.getElementById(`${prefix}-${r}-${col}`); if(!d) continue;
      const x=clip(vec[r]); d.style.background=valColor(x);
      const v=d.querySelector('.val'); v.textContent=fmt(x);
      d.classList.remove('flash'); void d.offsetWidth; d.classList.add('flash');
    }
  }

  function setShowVals(on){
    Object.values(grids).forEach(el=>{
      el.querySelectorAll('.cell').forEach(c => c.classList[on?'add':'remove']('showvals'));
    });
  }

  /* === Key fix: scale the middle grid to match the left grid’s height exactly === */
  function scaleMiddleToMatch(){
    const ref = grids.h2in;      // left panel grid
    const mid = grids.mlphid;    // middle tall grid

    // measure natural heights
    const targetH = ref.getBoundingClientRect().height;   // current rendered height
    const natH    = mid.scrollHeight;                      // unscaled natural height

    // compute scale and apply; set explicit height to eliminate whitespace
    const s = (natH > 0) ? (targetH / natH) : 1;
    mid.style.transformOrigin = 'top left';
    mid.style.transform = `scale(${s})`;
    mid.style.height = Math.ceil(natH * s) + 'px';
  }

  /* ---------- tensors ---------- */
  function getX(){
    const prev=document.getElementById('nano-X');
    let arr=[];
    if(prev && prev.textContent.trim()){
      const nums=prev.textContent.match(/-?\d+/g);
      if(nums) arr=nums.map(n=>parseInt(n,10));
    } else {
      const s='the quick brown fox jumps over the lazy dog.'.toLowerCase();
      arr=Array.from(s).map(ch=> ch===' '?charId(' '):charId(ch));
    }
    X = arr.slice(0, TLIM);
    T = X.length;
  }

  function buildTokInAndH0(){
    TokIn = Array.from({length:T}, (_,tt)=> {
      const emb=vecForId(X[tt]);
      const pos=Array.from({length:DM}, (_,j)=> wpe(tt,j));
      return emb.map((e,j)=> clip(e+pos[j]));
    });
    H0 = TokIn.map(v => layerNorm(v));
  }

  function buildAttentionAndProj(){
    Q = H0.map(v => matMulRow(v, WQ));
    K = H0.map(v => matMulRow(v, WK));
    Vv= H0.map(v => matMulRow(v, WV));
    // causal scores → weights
    const scores = Array.from({length:T}, ()=>Array(T).fill(0));
    for(let i=0;i<T;i++){ for(let j=0;j<T;j++){ scores[i][j] = (i<j) ? -Infinity : (dot(Q[i],K[j]) / Math.sqrt(DM)); } }
    weights = scores.map(row => softmaxRow(row));
    // AttnOut[i] = Σ_j w[i,j] * V[j]
    AttnOut = Array.from({length:T}, ()=>Array(DM).fill(0));
    for(let i=0;i<T;i++) for(let j=0;j<T;j++){ const w = weights[i][j]; if(!w) continue; for(let d=0; d<DM; d++) AttnOut[i][d]+= w*Vv[j][d]; }
    // output projection
    AttnProj = AttnOut.map(v => matMulRow(v, WO)).map(v=> v.map(clip));
  }

  function buildH1(){
    H1 = Array.from({length:T}, (_,tt)=> {
      const v=new Array(DM);
      for(let j=0;j<DM;j++) v[j] = clip(TokIn[tt][j] + AttnProj[tt][j]);
      return v;
    });
  }

  function buildMLP(){
    H2_in   = H1.map(v => layerNorm(v));
    MLP_hid = H2_in.map(v => matMulRowDFF(v, W1)).map(v=> v.map(gelu)); // (T × DFF)
    MLP_out = MLP_hid.map(v => matMulRowBack(v, W2)).map(v=> v.map(clip)); // (T × DM)
    H2      = Array.from({length:T}, (_,tt)=> {
      const v=new Array(DM);
      for(let j=0;j<DM;j++) v[j] = clip(H1[tt][j] + MLP_out[tt][j]);
      return v;
    });
  }

  /* ---------- UI build & refresh ---------- */
  function buildAllGrids(){
    Object.values(grids).forEach(el => el.style.setProperty('--T', T));

    buildGrid(grids.tokin,    DM, T, 'dim/t', 'd', 'tokin');
    buildGrid(grids.attnproj, DM, T, 'dim/t', 'd', 'attnproj');
    buildGrid(grids.h1,       DM, T, 'dim/t', 'd', 'h1');

    buildGrid(grids.h2in,     DM, T, 'dim/t', 'd', 'h2in');
    buildGrid(grids.mlphid,   64, T, 'dim/t', 'h', 'mlphid');   // tall → scaled to match left
    buildGrid(grids.mlpout,   DM, T, 'dim/t', 'd', 'mlpout');

    buildGrid(grids.h1skip,   DM, T, 'dim/t', 'd', 'h1skip');
    buildGrid(grids.h2,       DM, T, 'dim/t', 'd', 'h2');

    // *** Equalize heights (middle to left) — removes whitespace & mismatch
    scaleMiddleToMatch();
  }

  function refreshColumn(tt){
    // Residual 1: TokIn + AttnProj → H1
    paintCol('tokin',    tt, TokIn[tt]);
    paintCol('attnproj', tt, AttnProj[tt]);
    plus1.classList.add('active'); setTimeout(()=>plus1.classList.remove('active'), 240);
    const h1col = TokIn[tt].map((x,j)=> clip(x + AttnProj[tt][j]));
    paintCol('h1', tt, h1col);
    paintCol('h1skip', tt, h1col); // for final skip

    // MLP path
    const h2in = layerNorm(h1col);
    const hid  = matMulRowDFF(h2in, W1).map(gelu);
    const out  = matMulRowBack(hid, W2).map(clip);
    paintCol('h2in',   tt, h2in);
    paintCol('mlphid', tt, hid.slice(0,64));
    paintCol('mlpout', tt, out);

    plus2.classList.add('active'); setTimeout(()=>plus2.classList.remove('active'), 240);
    const h2col = h1col.map((x,j)=> clip(x + out[j]));
    paintCol('h2', tt, h2col);
  }

  /* ---------- controls ---------- */
  function step(){
    t = Math.min(t+1, T-1);
    slider.value = t;
    refreshColumn(t);
  }
  function play(){
    if(playing){ clearInterval(playing); playing=null; playBtn.textContent='Play'; return; }
    playBtn.textContent='Pause';
    if(t===0) refreshColumn(0);
    playing = setInterval(()=>{ if(t>=T-1){ clearInterval(playing); playing=null; playBtn.textContent='Play'; return; } step(); }, 350);
  }
  function reset(){
    if(playing){ clearInterval(playing); playing=null; playBtn.textContent='Play'; }
    t=0; slider.value=0; refreshColumn(0);
  }

  showVals.addEventListener('change', ()=> setShowVals(showVals.checked));
  stepBtn.addEventListener('click', step);
  playBtn.addEventListener('click', play);
  resetBtn.addEventListener('click', reset);
  slider.addEventListener('input', e=>{ t=parseInt(e.target.value,10)||0; refreshColumn(t); });

  // Re-equalize heights on resize (keeps middle matched to left)
  window.addEventListener('resize', scaleMiddleToMatch);

  /* ---------- init ---------- */
  function init(){
    // tokens (reuse from Tokenisation viz if present)
    const prev=document.getElementById('nano-X');
    getX();
    T = X.length;
    slider.max=Math.max(0, T-1); slider.value=0; TmaxOut.textContent=T-1;

    // tensors
    buildTokInAndH0();
    buildAttentionAndProj();
    buildH1();
    buildMLP();

    // UI
    buildAllGrids();
    setShowVals(false);

    // first paint
    refreshColumn(0);
  }
  init();
})();
</script>





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



<!-- === Interactive: Final Logits & Loss — vocab projection, softmax, CE === -->
<div class="nano-card" id="nano-logits" data-dmodel="16" data-vocab="205" data-tlimit="8">
  <div class="nano-head">
    <h4 style="margin:0">Interactive · Final Logits & Loss</h4>
    <div class="nano-sub">
      Hf = LN(H2) → logits = Hf · W<sub>vocab</sub> + b → softmax → cross-entropy vs Y where Y[t] = X[t+1].
    </div>
  </div>

  <div class="nano-row nano-grid">
    <div>
      <label class="nano-label">Position t (0 … <span id="lg-max">0</span>)</label>
      <!-- last token has no next-target; slider stops at T′-2 -->
      <input id="lg-slider" type="range" min="0" max="0" value="0" style="width:260px">
    </div>
    <div class="nano-actions">
      <button class="nano-btn" id="lg-play">Play</button>
      <button class="nano-btn ghost" id="lg-step">Step</button>
      <button class="nano-btn ghost" id="lg-reset">Reset</button>
      <label class="nano-label" style="margin-left:.75rem"><input type="checkbox" id="lg-values"> show values</label>
    </div>
  </div>

  <div class="nano-row" style="display:flex; gap:16px; flex-wrap:wrap">
    <div class="stat"><div class="stat-k">target id</div><div class="stat-v" id="lg-target">–</div></div>
    <div class="stat"><div class="stat-k">p(target)</div><div class="stat-v" id="lg-ptarg">–</div></div>
    <div class="stat"><div class="stat-k">loss<sub>t</sub>=−log p</div><div class="stat-v" id="lg-losst">–</div></div>
    <div class="stat"><div class="stat-k">mean loss</div><div class="stat-v" id="lg-lossmean">–</div></div>
  </div>

  <!-- Ribbons -->
  <div class="nano-section">
    <div class="nano-label">Logits (1 × V=205) — diverging color (blue↔red)</div>
    <div class="rib-viewport"><div class="rib-scale"><div class="rib-grid" id="rib-logits"></div></div></div>
  </div>

  <div class="nano-section">
    <div class="nano-label">Softmax probabilities (1 × V) — 0→1 sequential color (light→dark). Green = target, purple = argmax.</div>
    <div class="rib-viewport"><div class="rib-scale"><div class="rib-grid" id="rib-probs"></div></div></div>
  </div>

  <!-- Top-K -->
  <div class="nano-section">
    <div class="rowtitle">Top-10 probabilities</div>
    <div id="topk" class="topk"></div>
  </div>
</div>

<style>
  .nano-card{--bg:#f8fafc; --fg:#0b0e14; --muted:#4b5563; --accent:#2563eb; --line:#e5e7eb; --tile:#ffffff;
    --purple:#8b5cf6; --green:#10b981;
    border:1px solid var(--line); background:var(--bg); color:var(--fg);
    border-radius:16px; padding:18px; box-shadow:0 4px 18px rgba(0,0,0,.07); margin:1.25rem 0}
  .nano-head{display:flex; align-items:baseline; gap:.75rem}
  .nano-sub{color:var(--muted); font-size:.95rem}
  .nano-row{margin-top:12px}
  .nano-label{display:inline-flex; gap:.35rem; align-items:center; font-size:.9rem; color:#6b7280; margin-bottom:6px}
  .nano-grid{display:flex; gap:16px; align-items:end; flex-wrap:wrap}
  .nano-actions{margin-left:auto; display:flex; align-items:center; gap:10px; flex-wrap:wrap}
  .nano-btn{background:var(--accent); color:#fff; border:none; border-radius:10px; padding:8px 12px; font-weight:600; cursor:pointer}
  .nano-btn.ghost{background:transparent; color:#111827; border:1px solid var(--line)}
  .nano-section{margin-top:14px}
  .rowtitle{font-weight:600; margin:6px 0 6px 2px}

  /* Stats */
  .stat{background:#fff; border:1px solid var(--line); border-radius:10px; padding:8px 10px; min-width:120px}
  .stat-k{font-size:.8rem; color:#6b7280} .stat-v{font-weight:700}

  /* Ribbons (auto-scale to width; no dead whitespace) */
  .rib-viewport{border:1px solid var(--line); border-radius:12px; background:#fff; overflow:hidden; width:100%; position:relative}
  .rib-scale{transform-origin: top left;}
  .rib-grid{display:grid; grid-template-columns: repeat(205, 12px); grid-auto-rows: 28px}
  .rib-cell{border-right:1px solid #f0f1f5}
  .rib-cell.last{border-right:none}
  .hl-target{outline:2px solid var(--green); outline-offset:-2px}
  .hl-argmax{outline:2px solid var(--purple); outline-offset:-2px}

  /* Top-K bar list */
  .topk{display:grid; grid-template-columns: 70px 1fr 80px; gap:8px; align-items:center; border:1px solid var(--line); border-radius:12px; background:#fff; padding:10px}
  .tk-id{font:12px ui-monospace,Menlo,monospace; color:#374151}
  .tk-bar{height:16px; background:#ede9fe; border-radius:8px; position:relative; overflow:hidden}
  .tk-fill{position:absolute; left:0; top:0; bottom:0; width:0%; background:var(--purple)}
  .tk-val{font:12px ui-monospace,Menlo,monospace; text-align:right}
  .tk-target .tk-fill{background:var(--green)}
  .tk-target .tk-id{color:#065f46; font-weight:700}
  .valtag{display:none; position:absolute; top:2px; left:2px; font:11px ui-monospace,Menlo,monospace; color:#111827; background:#ffffffbf; border:1px solid #e5e7eb; padding:0 4px; border-radius:6px}
  .showvals .valtag{display:block}
</style>

<script>
(function(){
  const root = document.getElementById('nano-logits');
  const DM   = parseInt(root.dataset.dmodel, 10) || 16;
  const V    = parseInt(root.dataset.vocab, 10) || 205;
  const TLIM = parseInt(root.dataset.tlimit, 10) || 8;

  const slider = document.getElementById('lg-slider');
  const playBtn= document.getElementById('lg-play');
  const stepBtn= document.getElementById('lg-step');
  const resetBtn=document.getElementById('lg-reset');
  const showVals=document.getElementById('lg-values');
  const maxIdx = document.getElementById('lg-max');

  const ribLog  = document.getElementById('rib-logits');
  const ribProb = document.getElementById('rib-probs');

  const statTarget = document.getElementById('lg-target');
  const statPtarg  = document.getElementById('lg-ptarg');
  const statLosst  = document.getElementById('lg-losst');
  const statMean   = document.getElementById('lg-lossmean');

  const topkEl = document.getElementById('topk');

  let X=[], T=0, Tuse=0, Y=[], Hf=[], Wv=[], bv=[], playing=null, t=0;
  let logitsRow=[], probsRow=[];
  let logCells=[], probCells=[], idToProbCell={};

  /* ---------- helpers (deterministic pipeline, consistent with earlier blocks) ---------- */
  function charId(ch){ let h=2166136261; for (let i=0;i<ch.length;i++){ h^=ch.charCodeAt(i); h=(h*16777619)>>>0; } return 1+(h%(V-1)); }
  function vecForId(id){ if(id===0) return Array(DM).fill(0);
    const v=new Array(DM); for(let j=0;j<DM;j++){ const x=Math.sin(id*12.9898+(j+1)*78.233)*43758.5453; const f=x-Math.floor(x); v[j]=(f*2-1); }
    return v;
  }
  function wpe(t,j){ const a=Math.sin((t+1)*0.35+(j+1)*0.55), b=Math.cos((t+1)*0.12+(j+1)*0.18); return 0.6*a+0.4*b; }
  function layerNorm(v){ const m=v.reduce((a,b)=>a+b,0)/v.length; const c=v.map(x=>x-m); const varr=c.reduce((a,b)=>a+b*b,0)/v.length; const s=Math.sqrt(varr+1e-5); return c.map(x=>x/s); }
  function dot(a,b){ let s=0; for(let k=0;k<a.length;k++) s+=a[k]*b[k]; return s; }
  function softmax(arr){
    const m=Math.max(...arr);
    const ex=arr.map(x=>Math.exp(x-m)); const Z=ex.reduce((a,b)=>a+b,0)||1;
    return ex.map(e=>e/Z);
  }
  function colDiverge(x, maxAbs){ // logits
    if (maxAbs<=1e-8) return '#eee';
    const v=Math.max(-1, Math.min(1, x/maxAbs));
    const hue=v<0?210:10, sat=60*Math.abs(v)+20, light=92-40*Math.abs(v);
    return `hsl(${hue} ${sat}% ${light}%)`;
  }
  function colSequential(w){ // probs
    const v=Math.max(0, Math.min(1, w));
    const light=96 - 60*v; const sat=25 + 60*v;
    return `hsl(265 ${sat}% ${light}%)`;
  }
  function fmt3(x){ return (Math.round(x*1000)/1000).toFixed(3); }
  function fmt2(x){ return (Math.round(x*100)/100).toFixed(2); }

  // PRNG for Wv,bv
  let seed=777; function rnd(){ seed=(1664525*seed+1013904223)>>>0; return seed/4294967296; }

  /* ---------- ribbons: scale to width, zero whitespace ---------- */
  function fitRibbon(gridEl){
    const viewport = gridEl.closest('.rib-viewport');
    const scaler   = viewport.querySelector('.rib-scale');
    const natW = gridEl.scrollWidth;
    const natH = gridEl.scrollHeight;
    const boxW = viewport.clientWidth;
    const s = boxW / natW;
    scaler.style.transform = `scale(${s})`;
    viewport.style.height = Math.ceil(natH * s) + 'px';
  }

  function buildRibbon(gridEl, storeArr){
    gridEl.innerHTML='';
    const arr=[];
    for(let i=0;i<V;i++){
      const d=document.createElement('div');
      d.className='rib-cell' + (i===V-1?' last':'');
      gridEl.appendChild(d);
      arr.push(d);
    }
    storeArr.splice(0, storeArr.length, ...arr);
    fitRibbon(gridEl);
  }

  function highlightVocab(targetId, argmaxId){
    logCells.forEach((c,idx)=>{ c.classList.remove('hl-target','hl-argmax'); if(idx===targetId) c.classList.add('hl-target'); if(idx===argmaxId) c.classList.add('hl-argmax'); });
    probCells.forEach((c,idx)=>{ c.classList.remove('hl-target','hl-argmax'); if(idx===targetId) c.classList.add('hl-target'); if(idx===argmaxId) c.classList.add('hl-argmax'); idToProbCell[idx]=c; });
  }

  function paintLogitsAndProbs(){
    // logits
    const maxAbs = Math.max(...logitsRow.map(x=>Math.abs(x))) || 1;
    for(let v=0; v<V; v++){ logCells[v].style.background = colDiverge(logitsRow[v], maxAbs); }
    // probs
    for(let v=0; v<V; v++){ probCells[v].style.background = colSequential(probsRow[v]); }
  }

  function renderTopK(targetId){
    const pairs = probsRow.map((p,id)=>({id,p})).sort((a,b)=>b.p-a.p).slice(0,10);
    topkEl.innerHTML='';
    pairs.forEach(({id,p})=>{
      const row=document.createElement('div'); row.className='tk';
      if (id===targetId) row.classList.add('tk-target');
      const idDiv=document.createElement('div'); idDiv.className='tk-id'; idDiv.textContent='id '+id;
      const bar=document.createElement('div'); bar.className='tk-bar';
      const tag=document.createElement('div'); tag.className='valtag'; tag.textContent=fmt3(p);
      const fill=document.createElement('div'); fill.className='tk-fill'; fill.style.width=(p*100).toFixed(1)+'%';
      bar.appendChild(fill); bar.appendChild(tag);
      const val=document.createElement('div'); val.className='tk-val'; val.textContent=fmt3(p);
      row.appendChild(idDiv); row.appendChild(bar); row.appendChild(val);
      topkEl.appendChild(row);
    });
    topkEl.classList[showVals.checked ? 'add' : 'remove']('showvals');
  }

  /* ---------- pipeline to Hf and logits ---------- */
  function getX(){
    const prev=document.getElementById('nano-X');
    if (prev && prev.textContent.trim()){
      const nums=prev.textContent.match(/-?\d+/g);
      X = nums ? nums.map(n=>parseInt(n,10)) : [];
    } else {
      const s='the quick brown fox jumps over the lazy dog.';
      X = Array.from(s).map(ch=> charId(ch));
    }
    X = X.slice(0, TLIM);
    T = X.length;
    Tuse = Math.max(0, T-1); // positions with targets
    Y = X.slice(1);          // shift left
  }

  // Minimal single-block forward to Hf (same deterministic choices as before)
  function forwardToHf(){
    // TokIn
    const TokIn = Array.from({length:T}, (_,tt)=> {
      const emb=vecForId(X[tt]);
      const pos=Array.from({length:DM}, (_,j)=> wpe(tt,j));
      return emb.map((e,j)=> e+pos[j]);
    });
    // H1 via attention (1 head equivalent, but compact: we reuse deterministic projections)
    // Build LayerNorm(H0), projections, etc. (same as earlier blocks)
    const H0 = TokIn.map(v => layerNorm(v));
    // seed the same projections as earlier sections
    let seed2=10101; function rnd2(){ seed2=(1664525*seed2+1013904223)>>>0; return seed2/4294967296; }
    const WQ=Array.from({length:DM},()=>Array.from({length:DM},()=> (rnd2()*2-1)*0.7));
    const WK=Array.from({length:DM},()=>Array.from({length:DM},()=> (rnd2()*2-1)*0.7));
    const WV=Array.from({length:DM},()=>Array.from({length:DM},()=> (rnd2()*2-1)*0.7));
    const WO=Array.from({length:DM},()=>Array.from({length:DM},()=> (rnd2()*2-1)*0.7));
    function matMulRow(v, M){ const D2=M[0].length; const out=new Array(D2).fill(0); for(let d=0; d<D2; d++){ let s=0; for(let j=0;j<DM;j++) s+=v[j]*M[j][d]; out[d]=s; } return out; }
    function softmaxMasked(row,i){ const m=Math.max(...row.map((x,j)=> j<=i ? x : -Infinity)); const ex=row.map((x,j)=> j<=i?Math.exp(x-m):0); const Z=ex.reduce((a,b)=>a+b,0)||1; return ex.map(e=>e/Z); }
    function dot(a,b){ let s=0; for(let k=0;k<a.length;k++) s+=a[k]*b[k]; return s; }

    const Q = H0.map(v => matMulRow(v, WQ));
    const K = H0.map(v => matMulRow(v, WK));
    const Vv= H0.map(v => matMulRow(v, WV));

    // attention
    const weights = [];
    const AttnOut = Array.from({length:T}, ()=>Array(DM).fill(0));
    for(let i=0;i<T;i++){
      const row = new Array(T);
      for(let j=0;j<T;j++){ row[j] = (i<j) ? -Infinity : dot(Q[i],K[j]) / Math.sqrt(DM); }
      const w = softmaxMasked(row, i);
      weights.push(w);
      for(let j=0;j<T;j++){ const wij = w[j]; if(!wij) continue; for(let d=0; d<DM; d++) AttnOut[i][d]+= wij*Vv[j][d]; }
    }
    const AttnProj = AttnOut.map(v => matMulRow(v, WO));

    const H1 = Array.from({length:T}, (_,tt)=> {
      const v=new Array(DM);
      for(let j=0;j<DM;j++) v[j] = TokIn[tt][j] + AttnProj[tt][j];
      return v;
    });

    // MLP
    let seed3=202; function rnd3(){ seed3=(1664525*seed3+1013904223)>>>0; return seed3/4294967296; }
    const W1=Array.from({length:DM},()=>Array.from({length:DM*4},()=> (rnd3()*2-1)*0.6));
    const W2=Array.from({length:DM*4},()=>Array.from({length:DM},()=> (rnd3()*2-1)*0.6));
    function gelu(x){ return 0.5*x*(1+Math.tanh(Math.sqrt(2/Math.PI)*(x+0.044715*Math.pow(x,3)))); }
    function matMulRowTo(v, M, outDim){ const out=new Array(outDim).fill(0); const D1=v.length; for(let d=0; d<outDim; d++){ let s=0; for(let j=0;j<D1;j++) s+=v[j]*M[j][d]; out[d]=s; } return out; }

    const H2in   = H1.map(v => layerNorm(v));
    const Hid    = H2in.map(v => matMulRowTo(v, W1, DM*4)).map(v => v.map(gelu));
    const MLPout = Hid.map(v => matMulRowTo(v, W2, DM));

    const H2 = Array.from({length:T}, (_,tt)=> {
      const v=new Array(DM); for(let j=0;j<DM;j++) v[j] = H1[tt][j] + MLPout[tt][j]; return v;
    });

    Hf = H2.map(v => layerNorm(v));
  }

  function buildVocabHead(){
    // Wv (DM×V) and b (V)
    Wv = Array.from({length:DM},()=>Array.from({length:V},()=> (rnd()*2-1)*0.8));
    bv = Array.from({length:V}, ()=> (rnd()*2-1)*0.2);
  }

  function logitsAt(t){
    const out=new Array(V).fill(0);
    for(let v=0; v<V; v++){
      let s=bv[v]; for(let j=0;j<DM;j++) s += Hf[t][j]*Wv[j][v];
      out[v]=s;
    }
    return out;
  }

  /* ---------- build UI ---------- */
  function buildUI(){
    // ribbons
    buildRibbon(ribLog,  logCells);
    buildRibbon(ribProb, probCells);
    window.addEventListener('resize', ()=>{ fitRibbon(ribLog); fitRibbon(ribProb); });

    // slider range (last token has no target)
    slider.max = Math.max(0, Tuse-1);
    maxIdx.textContent = Math.max(0, Tuse-1);
  }

  function refresh(){
    // compute logits & probs at t
    logitsRow = logitsAt(t);
    probsRow  = softmax(logitsRow);
    const yid = Y[t] ?? 0;
    const argmax = probsRow.indexOf(Math.max(...probsRow));

    // paint ribbons
    paintLogitsAndProbs();
    highlightVocab(yid, argmax);

    // stats
    const pt = probsRow[yid] || 1e-12;
    const lt = -Math.log(pt);
    statTarget.textContent = yid;
    statPtarg.textContent  = fmt3(pt);
    statLosst.textContent  = fmt3(lt);

    // mean loss across all t with targets
    let sum=0; for(let i=0;i<Tuse;i++){ const lr = softmax(logitsAt(i)); const yy = Y[i]; sum += -Math.log(lr[yy]||1e-12); }
    statMean.textContent = fmt3(sum / Math.max(1,Tuse));

    // top-k
    renderTopK(yid);

    // values overlay (only on top-k bars)
    topkEl.classList[showVals.checked ? 'add' : 'remove']('showvals');
  }

  /* ---------- controls ---------- */
  function step(){ t = Math.min(t+1, Tuse-1); slider.value=t; refresh(); }
  function play(){
    if(playing){ clearInterval(playing); playing=null; playBtn.textContent='Play'; return; }
    playBtn.textContent='Pause';
    playing = setInterval(()=>{ if(t>=Tuse-1){ clearInterval(playing); playing=null; playBtn.textContent='Play'; return; } step(); }, 400);
  }
  function reset(){ if(playing){ clearInterval(playing); playing=null; playBtn.textContent='Play'; } t=0; slider.value=0; refresh(); }

  slider.addEventListener('input', e=>{ t=parseInt(e.target.value,10)||0; refresh(); });
  stepBtn.addEventListener('click', step);
  playBtn.addEventListener('click', play);
  resetBtn.addEventListener('click', reset);
  showVals.addEventListener('change', ()=>{ topkEl.classList[showVals.checked ? 'add' : 'remove']('showvals'); });

  /* ---------- init ---------- */
  function init(){
    getX();
    forwardToHf();
    buildVocabHead();
    buildUI();
    refresh();
  }
  init();
})();
</script>
