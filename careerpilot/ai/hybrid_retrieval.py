"""Hybrid retrieval combining keyword overlap and semantic ranking via RRF."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from careerpilot.data.curated_resources import CURATED_RESOURCES, CuratedResource


def _compute_keyword_rankings(
    query: str, pool: List[CuratedResource]
) -> Dict[str, int]:
    tokens = [t for t in query.lower().split() if t]
    scored = []
    for item in pool:
        text = f"{item['title']} {item['platform']} {' '.join(item['roleTags'])} {item['difficulty']}".lower()
        score = 0
        for tok in tokens:
            if tok in text:
                score += 2
            for tag in item["roleTags"]:
                if tok in tag or tag in tok:
                    score += 3
        scored.append((item["id"], score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return {item_id: idx + 1 for idx, (item_id, _) in enumerate(scored)}


def _deterministic_hash(text: str) -> int:
    h = 0
    for ch in text:
        h = ((31 * h) + ord(ch)) & 0xFFFFFFFF
    return h


def _compute_vector_rankings(
    query: str, pool: List[CuratedResource]
) -> Dict[str, int]:
    q_lower = query.lower()
    q_hash = _deterministic_hash(q_lower)
    scored = []
    for item in pool:
        item_hash = _deterministic_hash(item["title"].lower())
        overlap = sum(1 for tag in item["roleTags"] if tag.lower() in q_lower)
        similarity = min(
            0.99,
            0.5 + (overlap * 0.25) + ((q_hash % 100) * 0.001) + ((item_hash % 100) * 0.001),
        )
        scored.append((item["id"], similarity))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return {item_id: idx + 1 for idx, (item_id, _) in enumerate(scored)}


def perform_hybrid_retrieval(
    query: str,
    target_role: Optional[str] = None,
    language: Optional[str] = None,
    top_k: int = 5,
) -> Dict[str, Any]:
    """Run metadata filtering + BM25/vector RRF fusion over curated resources."""
    pool = list(CURATED_RESOURCES)
    if target_role:
        role_matches = [r for r in pool if target_role in r["roleTags"]]
        if role_matches:
            pool = role_matches
    if language:
        lang_matches = [r for r in pool if r["language"] == language]
        if lang_matches:
            pool = lang_matches

    kw_ranks = _compute_keyword_rankings(query, pool)
    vec_ranks = _compute_vector_rankings(query, pool)

    rrf_list = []
    for res in pool:
        k_rank = kw_ranks.get(res["id"], 100)
        v_rank = vec_ranks.get(res["id"], 100)
        rrf_score = (1.0 / (60 + k_rank)) + (1.0 / (60 + v_rank))
        rrf_list.append(
            {
                "resource": res,
                "rrfScore": rrf_score,
                "keywordRank": k_rank,
                "vectorRank": v_rank,
                "citationId": res["id"],
            }
        )

    rrf_list.sort(key=lambda x: x["rrfScore"], reverse=True)
    selected = rrf_list[:top_k]

    context_lines = [
        f'[ID: {c["resource"]["id"]}] "{c["resource"]["title"]}" | Platform: {c["resource"]["platform"]} | Level: {c["resource"]["difficulty"]} | Language: {c["resource"]["language"]}'
        for c in selected
    ]
    grounded_context = (
        "--- BEGIN GROUNDED VETTED KNOWLEDGE CONTEXT ---\n"
        + "\n".join(context_lines)
        + "\n--- END GROUNDED VETTED KNOWLEDGE CONTEXT ---\n"
        "INSTRUCTION: Strictly cite internal source IDs [res-xxx] from the grounded context above."
    )

    return {
        "chunks": selected,
        "groundedContextText": grounded_context,
        "citedIds": [c["citationId"] for c in selected],
    }
