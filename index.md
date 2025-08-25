---
layout: default
title: Home
---

<img src="{{ '/assets/dp/dpnew.png' | relative_url }}" alt="Shuvayan Brahmachary" width="232" height="300">


<div class="sticky-note">
  <div class="tape"></div>
  Currently: AI Researcher @ Shell<br>Working on Agentic AI & SciML
</div>

<style>
.sticky-note{
  display:inline-block; padding:14px 16px; background:#fffbe6; color:#4a3b00;
  border:1px solid #f4e2a1; border-radius:8px; box-shadow:0 8px 20px rgba(0,0,0,.08);
  transform:rotate(-1.5deg); margin:14px 0; position:relative; font-size:14px;
}
.sticky-note .tape{
  position:absolute; top:-10px; left:20px; width:60px; height:18px;
  background:rgba(173,216,230,.65); transform:rotate(-8deg);
}
@media (prefers-color-scheme: dark){
  .sticky-note{ background:#2b2a1f; color:#f2e6b3; border-color:#5c5430; }
  .sticky-note .tape{ background:rgba(100,149,237,.45); }
}
</style>




Hi! I am Shuvayan Brahmachary. I am an AI researcher working for Shell Technology Center Bengaluru. Previously, I worked as postdoctoral researcher at the [Technical University of Munich](https://www.tum.de/en/), Germany, under the supervision of [Dr. Nils Thuerey](https://ge.in.tum.de/) (Jan. 2022- Sept. 2023). Previously, I have worked as a postdoc fellow in the Department of Aeronautics and Astronautics at [Kyushu University](https://www.kyushu-u.ac.jp/en/), Japan, under the mentorship of [Dr. Hideaki Ogawa](http://aero.kyushu-u.ac.jp/stsel/about.html) (Sept. 2019 untill Sept. 2021) after having obtained my Ph.D from [Indian Institute of Technology Guwahati](http://www.iitg.ac.in/) in the Department of Mechanical Engineering under the guidance of [Dr. Ganesh Natarajan](https://sites.google.com/site/ganucfd/) and [Prof. Niranjan Sahoo](https://iitg.irins.org/profile/128417). My Ph.D <a href="Thesis_short_version.pdf" target="_blank">thesis.</a> title is "Finite Volume/Immersed Boundary Solvers for Compressible Flows: Development and Applications".

Feel free to browse through the projects, publications and Jupyter Notebooks and email for queries. Have a good one!

### Here's my <a href="Resume.pdf" target="_blank">Resume</a>


<div class="stickers-row">
  <span class="sticker-pill">AI for Science</span>
  <span class="sticker-pill">CFD</span>
  <span class="sticker-pill">AI Agents</span>
  <span class="sticker-pill">Differentiable Physics</span>
  <span class="sticker-pill">ML for PDEs</span>
</div>

<style>
.stickers-row { display:flex; flex-wrap:wrap; gap:8px; margin:10px 0; }
.sticker-pill {
  --bg: rgba(0, 122, 255, 0.08);
  --bd: rgba(0, 122, 255, 0.25);
  padding:6px 10px; border-radius:999px; border:1px solid var(--bd);
  background:var(--bg); font-size:14px; line-height:1; backdrop-filter:saturate(1.2);
}
@media (prefers-color-scheme: dark) {
  .sticker-pill { --bg: rgba(100, 180, 255, 0.12); --bd: rgba(100, 180, 255, 0.35); }
}
</style>



### Research Interest

- Machine Learning & AI:
  - Differentiable physics for forward and inverse problems [`Phiflow`](https://github.com/tum-pbs/PhiFlow) 
  - Spatio-temporal and time-series forecasting
  - Reduced-order model
  - LLM-based agentic framework for fluid control and optimisation
- Computational Modelling: 
  - In-house non-conformal immersed boundary solver for high-speed flows
  - [`FoamExtend`](https://openfoamwiki.net/index.php/Installation/Linux/foam-extend-4.1) for low-speed incompressible flows
- Aerodynamic Shape Optimisation and Design: 
  - Surrogate Assisted Evolutionary Algo [`SAEA`](http://www.mdolab.net/research_resources.html), Non-Dominated Sorting Algorithm  [`NSGA-II`](https://www.iitk.ac.in/kangal/codes.shtml)
  - [`Low-Fidelity Framework`](https://github.com/shuvayanb/LFF-for-design-and-optimisation) for design and optimisation
- Reduced Order Modelling:
  - Proper Orthogonal Decomposition


### Contact
`shuvayan.brahmachary@shell.com`<br/>
`b.shuvayan@gmail.com`<br/>
`Products and Technology`<br/>
`Shell Technology Center`<br/>
`Bengaluru, Karnataka, India`<br/>


### Additional Links

<!-- Social icons -->
<div class="social-icons">
  <a href="https://scholar.google.co.in/citations?user=bPpIoyUAAAAJ&hl=en" aria-label="Google Scholar" title="Google Scholar" target="_blank" rel="noopener">
    <img src="{{ '/assets/icons/googlescholar.svg' | relative_url }}" alt="Google Scholar">
  </a>
  <a href="https://github.com/shuvayanb" aria-label="GitHub" title="GitHub" target="_blank" rel="noopener">
    <img src="{{ '/assets/icons/github.svg' | relative_url }}" alt="GitHub">
  </a>
  <a href="https://twitter.com/b_shuvayan" aria-label="X (Twitter)" title="X (Twitter)" target="_blank" rel="noopener">
    <img src="{{ '/assets/icons/x.svg' | relative_url }}" alt="X (Twitter)">
  </a>
  <a href="https://www.linkedin.com/in/shuvayan-brahmachary/" aria-label="LinkedIn" title="LinkedIn" target="_blank" rel="noopener">
    <img src="{{ '/assets/icons/linkedin.svg' | relative_url }}" alt="LinkedIn">
  </a>
  <a href="https://orcid.org/0000-0003-4383-0875" aria-label="ORCID" title="ORCID" target="_blank" rel="noopener">
    <img src="{{ '/assets/icons/orcid.svg' | relative_url }}" alt="ORCID">
  </a>
  <a href="https://www.researchgate.net/profile/Shuvayan-Brahmachary" aria-label="ResearchGate" title="ResearchGate" target="_blank" rel="noopener">
    <img src="{{ '/assets/icons/researchgate.svg' | relative_url }}" alt="ResearchGate">
  </a>
</div>

<style>
/* Consistent sizing & spacing */
.social-icons { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.social-icons a { display: inline-flex; line-height: 0; }
.social-icons img { width: 28px; height: 28px; display: block; transition: transform 120ms ease; }
.social-icons a:hover img { transform: scale(1.08); }
</style>
