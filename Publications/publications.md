---
layout: page
title: Publications
---

## Preprint
{% bibliography --query '@preprint or note:/preprint/i or url:/arxiv\.org|ssrn\.com|biorxiv\.org|medrxiv\.org/' %}

## Journals
{% bibliography --query '@article' %}

## Book Chapters
{% bibliography --query '@incollection' %}

## Conferences
{% bibliography --query '@inproceedings' %}
