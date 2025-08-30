---
layout: page
title: Publications
---

<style>
.sticker-tag{
  display:inline-block; font-size:11px; line-height:1; font-weight:700;
  padding:3px 6px; border-radius:6px; margin-left:6px; vertical-align:middle;
}
.sticker-new{ background:#e6fffb; color:#006d75; border:1px solid #87e8de; }
.sticker-preprint{ background:#f6ffed; color:#237804; border:1px solid #b7eb8f; }
.sticker-award{ background:#fff7e6; color:#ad4e00; border:1px solid #ffd591; }
@media (prefers-color-scheme: dark){
  .sticker-new{ background:#003a3f; color:#c2fffb; border-color:#146b66; }
  .sticker-preprint{ background:#163a24; color:#bdf7a8; border-color:#2c6c45; }
  .sticker-award{ background:#3e2a00; color:#ffd8a8; border-color:#805500; }
}
</style>


## Preprint
{% bibliography --query '@preprint or note:/preprint/i or url:/arxiv\.org|ssrn\.com|biorxiv\.org|medrxiv\.org/' %}

## Journals
{% bibliography --query '@article' %}

## Book Chapters
{% bibliography --query '@incollection' %}

## Conferences
{% bibliography --query '@inproceedings' %}
