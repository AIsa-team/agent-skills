# OpenClaw Skills Repository Restructuring Plan

## 1. Introduction

This document outlines a plan to restructure the `AIsa-team/OpenClaw-Skills` GitHub repository. The current repository contains a collection of skills for OpenClaw autonomous agents, each residing in its own top-level directory. While functional, the existing structure exhibits inconsistencies in naming conventions and some redundancy in code and documentation, which can hinder maintainability and clarity for contributors and users.

The primary goal of this restructuring is to enhance the repository's organization, standardize file naming, eliminate redundant code, and improve overall maintainability and user experience.

## 2. Current Repository Structure Analysis

The `OpenClaw-Skills` repository currently has the following top-level directories and observed patterns:

```
/home/ubuntu/OpenClaw-Skills/
├── LICENSE
├── README.md
├── market/
│   ├── README.md
│   ├── SKILL.md
│   └── scripts/
│       └── market_client.py
├── media-gen/
│   ├── README.md
│   ├── SKILL.md
│   └── scripts/
│       └── media_gen_client.py
├── perplexity-search/
│   ├── SKILL.md
│   └── scripts/
│       └── perplexity_search_client.py
├── prediction-market/
│   ├── readme.md
│   ├── scripts/
│   │   └── prediction_market_client.py
│   └── skill.md
├── prediction-market-arbitrage/
│   ├── readme.md
│   ├── script/
│   │   ├── arbitrage_finder.py
│   │   └── prediction_market_client.py
│   └── skill.md
├── search/
│   ├── README.md
│   ├── SKILL.md
│   └── scripts/
│       └── search_client.py
├── twitter/
│   ├── README.md
│   ├── SKILL.md
│   ├── references/
│   │   ├── engage_twitter.md
│   │   └── post_twitter.md
│   └── scripts/
│       ├── twitter_client.py
│       ├── twitter_engagement_client.py
│       └── twitter_oauth_client.py
└── youtube/
    ├── README.md
    ├── SKILL.md
    └── scripts/
        └── youtube_client.py
```

**Key Observations and Issues:**

*   **Inconsistent Naming:**
    *   `SKILL.md` vs. `skill.md`: Some skill directories use `SKILL.md` (e.g., `market`, `media-gen`, `perplexity-search`, `search`, `twitter`, `youtube`), while `prediction-market` and `prediction-market-arbitrage` use `skill.md`.
    *   `README.md` vs. `readme.md`: Similar inconsistency for README files.
    *   `scripts/` vs. `script/`: The `prediction-market-arbitrage` skill uses a singular `script/` directory, whereas others use the plural `scripts/`.
*   **Code Duplication:** The file `prediction-market-arbitrage/script/prediction_market_client.py` is nearly identical to `prediction-market/scripts/prediction_market_client.py`. This redundancy makes updates and bug fixes more complex.
*   **Overlapping Functionality and Documentation:**
    *   The `search` skill's `SKILL.md` and `search_client.py` include functionalities related to Perplexity Sonar endpoints, which are also the sole focus of the `perplexity-search` skill.
    *   This overlap suggests that the Perplexity Sonar functionality could be consolidated or more clearly delineated.
*   **Complex Skill Implementations:** The `twitter` skill is implemented across multiple client scripts (`twitter_client.py`, `twitter_oauth_client.py`, `twitter_engagement_client.py`), indicating a need for clearer modularization or a unified client approach if feasible.
*   **`references/` Directory:** Only the `twitter` skill has a `references/` directory, suggesting a lack of a standardized location for supplementary documentation across all skills.

## 3. Proposed New Repository Structure

To address the identified issues, the following new repository structure is proposed. The core idea is to introduce a `skills/` subdirectory to house all individual skill modules, ensuring a cleaner root directory and a more consistent organizational pattern. Redundant files will be removed, and naming conventions will be standardized.

```
/home/ubuntu/OpenClaw-Skills/
├── LICENSE
├── README.md
├── skills/
│   ├── market/
│   │   ├── SKILL.md
│   │   ├── README.md
│   │   └── scripts/
│   │       └── market_client.py
│   ├── media-gen/
│   │   ├── SKILL.md
│   │   ├── README.md
│   │   └── scripts/
│   │       └── media_gen_client.py
│   ├── prediction-market/
│   │   ├── SKILL.md
│   │   ├── README.md
│   │   └── scripts/
│   │       └── prediction_market_client.py
│   ├── prediction-market-arbitrage/
│   │   ├── SKILL.md
│   │   ├── README.md
│   │   └── scripts/
│   │       └── arbitrage_finder.py
│   ├── search/
│   │   ├── SKILL.md
│   │   ├── README.md
│   │   └── scripts/
│   │       └── search_client.py
│   ├── twitter/
│   │   ├── SKILL.md
│   │   ├── README.md
│   │   ├── scripts/
│   │   │   ├── twitter_client.py
│   │   │   ├── twitter_engagement_client.py
│   │   │   └── twitter_oauth_client.py
│   │   └── references/
│   │       ├── engage_twitter.md
│   │       └── post_twitter.md
│   └── youtube/
│       ├── SKILL.md
│       ├── README.md
│       └── scripts/
│           └── youtube_client.py
└── .gitignore
```

**Key Changes and Rationale:**

1.  **`skills/` Directory:** All individual skill directories will be moved into a new `skills/` subdirectory. This centralizes all skills, making the repository's purpose immediately clear and separating skill modules from root-level repository files (like `LICENSE` and `README.md`).
2.  **Standardized Naming:**
    *   All `skill.md` files will be renamed to `SKILL.md`.
    *   All `readme.md` files will be renamed to `README.md`.
    *   All `script/` directories will be renamed to `scripts/`.
    This ensures consistency across all skill modules, simplifying navigation and adherence to project standards.
3.  **Consolidation of Perplexity Search:**
    *   The `perplexity-search` skill will be removed.
    *   Its unique functionalities (Perplexity Sonar endpoints) are already present in `search/SKILL.md` and `search/scripts/search_client.py`. Consolidating these into the `search` skill reduces redundancy and simplifies the overall search-related offerings.
4.  **Prediction Market Client Duplication Resolution:**
    *   The duplicate `prediction_market_client.py` in `prediction-market-arbitrage/scripts/` will be removed.
    *   The `arbitrage_finder.py` script in `prediction-market-arbitrage/scripts/` will be updated to import and utilize the `prediction_market_client.py` from the `prediction-market/scripts/` directory. This promotes code reuse and eliminates redundancy.
5.  **Twitter Skill Structure:** The `twitter` skill's internal structure with multiple client scripts and a `references/` directory will be maintained due to its inherent complexity and distinct operational modes (read, write, engagement). This decision prioritizes functional separation within a complex skill over forced simplification that might compromise clarity or functionality.

## 4. Implementation Steps

1.  **Create `skills/` directory:** `mkdir /home/ubuntu/OpenClaw-Skills/skills`
2.  **Move existing skill directories:** `mv /home/ubuntu/OpenClaw-Skills/{market,media-gen,prediction-market,prediction-market-arbitrage,search,twitter,youtube} /home/ubuntu/OpenClaw-Skills/skills/`
3.  **Standardize `SKILL.md` naming:**
    *   `mv /home/ubuntu/OpenClaw-Skills/skills/prediction-market/skill.md /home/ubuntu/OpenClaw-Skills/skills/prediction-market/SKILL.md`
    *   `mv /home/ubuntu/OpenClaw-Skills/skills/prediction-market-arbitrage/skill.md /home/ubuntu/OpenClaw-Skills/skills/prediction-market-arbitrage/SKILL.md`
4.  **Standardize `README.md` naming:**
    *   `mv /home/ubuntu/OpenClaw-Skills/skills/prediction-market/readme.md /home/ubuntu/OpenClaw-Skills/skills/prediction-market/README.md`
    *   `mv /home/ubuntu/OpenClaw-Skills/skills/prediction-market-arbitrage/readme.md /home/ubuntu/OpenClaw-Skills/skills/prediction-market-arbitrage/README.md`
5.  **Standardize `scripts/` directory naming:**
    *   `mv /home/ubuntu/OpenClaw-Skills/skills/prediction-market-arbitrage/script /home/ubuntu/OpenClaw-Skills/skills/prediction-market-arbitrage/scripts`
6.  **Remove `perplexity-search` skill:** `rm -rf /home/ubuntu/OpenClaw-Skills/perplexity-search`
7.  **Remove duplicate `prediction_market_client.py`:** `rm /home/ubuntu/OpenClaw-Skills/skills/prediction-market-arbitrage/scripts/prediction_market_client.py`
8.  **Update `arbitrage_finder.py`:** Modify `arbitrage_finder.py` to import `prediction_market_client.py` from the `prediction-market` skill's `scripts` directory. This will involve changing the import statement and potentially the instantiation of the client.
9.  **Update `search/SKILL.md` and `search/README.md`:** Ensure these documents fully cover the Perplexity Sonar functionalities now that `perplexity-search` is removed.
10. **Update `README.md` (root):** Reflect the new `skills/` directory structure and any other relevant changes.

## 5. Conclusion

This restructuring plan aims to create a more organized, consistent, and maintainable `OpenClaw-Skills` repository. By standardizing naming conventions, consolidating overlapping functionalities, and eliminating redundant code, the repository will be easier to navigate, understand, and contribute to, ultimately benefiting both developers and users of OpenClaw agents.
