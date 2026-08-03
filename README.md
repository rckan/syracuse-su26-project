# Solar Energy Network Graph & Data Extraction Pipeline

## Overview

This project builds a knowledge graph of the solar energy ecosystem by extracting entities and relationships from Cornell Newsroom articles using an LLM-based information extraction pipeline. The resulting graph is analyzed using graph visualization and community detection techniques to identify major themes, organizations, technologies, policies, and their relationships.

---

# Pipeline

## 1. Dataset Selection

* Used the **Cornell Newsroom dataset** as the starting dataset.
* Used the article **summaries** from the Newsroom dataset to identify **solar energy-related keywords**.

---

## 2. Keyword Discovery

### Bigram and Trigram Extraction

* Performed **bigram** and **trigram** extraction on the article summaries already available in the downloadable dataset.
* Extracted **all bigrams and trigrams containing the keyword `solar`** from the summaries.
* Observed that the trigrams were not particularly insightful, so the analysis ultimately relied on **bigrams**.
* Only inspected bigrams that occurred **at least 5 times** across the summaries.
* Performed **manual inspection** of the resulting bigrams to remove unrelated phrases (e.g., **"solar flare"**).

### Additional Keyword Collection

* Also consulted existing literature to identify additional solar energy keywords that do **not** explicitly contain the word **"solar"** (e.g., **"photovoltaic cell"**).

---

## 3. Article Scraping

* Used the **Newsroom GitHub scraping scripts** to scrape **only** the articles whose summaries contained at least one identified solar energy keyword.
* This scraping process took **approximately 2–3 days** to complete.

---

## 4. Token Analysis

* Used **tiktoken** to count the number of tokens for each scraped article.

---

## 5. LLM Prompt Design

### Prompt Structure

A prompt was designed consisting of:

* **System prompt** (instructions to the LLM)
* **User prompt** (article text and metadata)
* **JSON structured output schema**

The prompt was iteratively refined to reduce token usage.

### Prompt Optimization

* Reformatted the prompt into the above structure.
* Made the prompt more concise to reduce token consumption.
* The prompt also instructed the model to determine whether an article was **actually relevant** to solar energy.

Some scraped articles only contained a brief mention of solar energy and therefore were excluded because they were not meaningfully related to the domain.

---

## 6. Relevance Filtering

* Initially tested the extraction pipeline on **30 articles** to evaluate its effectiveness.
* Determined that it would be better to exclude articles containing **fewer than two mentions** of any solar energy keyword.
* Reduced the dataset from **5,374 articles** to **1,985 articles**.
* Reduced total token usage and estimated cost from **TODO** to **TODO**.

---

## 7. Further Prompt Optimization

* Shortened the system prompt even further.
* The average **user prompt** was significantly shorter than the **system prompt**, making the system prompt the primary contributor to token usage since it is sent with every request.
* Reducing the system prompt therefore provided meaningful token savings.

---

## 8. LLM Information Extraction

* Ran the complete LLM extraction pipeline using **ChatGPT 4o**.
* Generated structured JSON outputs for every article.
* Converted the extracted JSON into:

  * **Nodes CSV**
  * **Relations CSV**

These CSV files served as the input for graph construction.

---

## 9. Graph Construction

Used the extracted data to build network graph visualizations.

### Initial Graph

The initial graph was extremely dense and contained a significant amount of noisy information.

### Graph Cleanup

* Removed nodes with **fewer than two edges**.
* Made node sizes proportional to their **edge degree**.
* Color-coded nodes according to **node type**.
* Also generated graphs containing **only a single node type** for easier analysis.

### Node Deduplication

* Similar nodes required deduplication.
* Applied **fuzzy matching**.
* Used **TODO transformer** to deduplicate semantically similar nodes.

---

## 10. Community Detection

Performed community detection on the cleaned graph to identify major clusters.

### Findings

* Communities were separated primarily by:

  * Geographic location
  * Area of focus (e.g., technology, policy, etc.)

Additionally:

* Identified which communities were most strongly connected to one another.
* Determined the dominant connection types between communities.
* Found the most common relationship types across the full community graph.

---

## 11. Community Graph

Generated a graph representing the communities themselves.

The resulting graph showed that most communities were **not directly connected** to one another. Instead, they were connected **indirectly through a small number of highly central communities**.

The major central communities were:

| Community | Description                                                                           |
| --------- | ------------------------------------------------------------------------------------- |
| **0**     | American Residential Solar Market                                                     |
| **1**     | US-China Manufacturing and Trade                                                      |
| **2**     | Predominantly US policy                                                               |
| **3**     | International technologies/projects that often span borders across multiple countries |
| **4**     | International projects and organizations focused on solar energy                      |
