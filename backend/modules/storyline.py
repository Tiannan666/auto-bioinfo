"""Storyline recommendation using DeepSeek LLM."""

from typing import Dict, List

from ..deepseek_client import chat as llm_chat


def generate_storylines(diff_result: Dict = None, enrich_result: Dict = None,
                        gsea_result: Dict = None, count: int = 5,
                        language: str = 'both') -> Dict:
    """Generate research direction storylines based on analysis results."""

    context = _build_story_context(diff_result, enrich_result, gsea_result)
    lang = 'Chinese' if language == 'zh' else ('English' if language == 'en' else 'bilingual Chinese/English')

    prompt = f"""You are a senior bioinformatics principal investigator helping a researcher interpret their RNA-seq results.

Analysis results:
{context}

Based on these REAL results, propose {count} distinct mechanistic hypotheses/research directions. Each direction MUST be grounded in the actual data (specific genes and pathways that appeared in the results).

For each direction, provide (in {lang}):

1. **Hypothesis**: Core mechanistic hypothesis (1-2 sentences)
2. **Key Genes**: 3-5 genes from the actual results supporting this direction
3. **Key Pathways**: 2-3 pathways from the actual enrichment/GSEA results
4. **Direction**: Up/down regulation trends
5. **Validation**: 2-3 specific experiments to test this hypothesis
6. **Suggested Figures**: Recommended figure layout for a paper
7. **Paper Title**: A potential paper title for this direction
8. **Mechanism Description**: A paragraph (4-6 sentences) describing the proposed mechanism, similar to:

"Treatment group showed upregulation of glutathione metabolism and oxidative stress response genes (including SLC7A11 and GPX4), suggesting redox metabolic reprogramming. Combined with the enrichment of ferroptosis pathway, these results support further investigation of the SLC7A11/GSH axis in ROS scavenging and cellular antioxidant homeostasis."

IMPORTANT:
- Every gene and pathway mentioned MUST be from the actual results provided above. Do NOT fabricate genes.
- Each direction should explore a DIFFERENT mechanistic angle.
- Write naturally as if for a grant proposal or paper discussion.
- Return results as a structured list with clear section headers.
- Show the confidence level as High/Medium/Low based on how well-supported the hypothesis is by the data."""

    try:
        resp = llm_chat([{"role": "user", "content": prompt}])
        content = resp.get('content', 'Storyline generation requires API key.')
        storylines = _parse_storylines(content, count)
        return {"storylines": storylines, "raw": content}
    except Exception as e:
        return {"storylines": [_empty_storyline(i) for i in range(min(count, 3))], "error": str(e)}


def _build_story_context(diff, enrich, gsea) -> str:
    parts = []
    if diff:
        parts.append(f"DEGs: {diff.get('n_up', 0)} up, {diff.get('n_down', 0)} down (|log2FC|>{diff.get('logfc_threshold', 1.0)}, FDR<{diff.get('fdr_threshold', 0.05)})")
        up_genes = [g['gene'] for g in diff.get('top_genes', []) if g.get('direction') == 'up'][:15]
        down_genes = [g['gene'] for g in diff.get('top_genes', []) if g.get('direction') == 'down'][:15]
        if up_genes:
            parts.append(f"Top up-regulated: {', '.join(up_genes)}")
        if down_genes:
            parts.append(f"Top down-regulated: {', '.join(down_genes)}")
    if enrich:
        terms = enrich.get('terms', [])[:10]
        term_strs = ['{} (FDR={:.1e})'.format(t["term"], t["fdr"]) for t in terms]
        parts.append("Enriched terms: " + "; ".join(term_strs))
    if gsea:
        gsea_terms = gsea.get('terms', [])[:8]
        gsea_strs = ['{} (NES={:.2f}, FDR={:.1e})'.format(t["term"], t["nes"], t["fdr"]) for t in gsea_terms]
        parts.append("GSEA: " + "; ".join(gsea_strs))
    return '\n'.join(parts) if parts else "No analysis results available."


def _parse_storylines(text: str, count: int) -> List[Dict]:
    """Parse LLM output into structured storylines."""
    # Simple parsing: split by numbered sections
    import re
    storylines = []
    # Try to find direction markers
    parts = re.split(r'(?:###?\s*)?(?:Direction|Hypothesis|Mechanism)\s*\d+[:\)]', text, flags=re.IGNORECASE)
    if len(parts) <= 1:
        # Alternative parsing
        parts = re.split(r'\n(?=#{1,3}\s)', text)

    if len(parts) <= 1:
        # Fallback: treat each paragraph as a direction
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
        for i, p in enumerate(paragraphs[:count]):
            storylines.append({
                "title": f"Direction {i+1}",
                "hypothesis": p[:300],
                "key_genes": [],
                "key_pathways": [],
                "validation": "Recommended: qPCR validation, Western blot, functional assays",
                "suggested_figures": f"Figure {i+1}: Mechanism overview",
                "paper_title": f"Research Direction {i+1}",
                "mechanism": p,
                "confidence": "Medium",
            })
    else:
        for i, part in enumerate(parts[1:count+1]):
            storylines.append({
                "title": f"Direction {i+1}",
                "hypothesis": part[:300].strip(),
                "key_genes": _extract_genes(part),
                "key_pathways": [],
                "validation": "See mechanism description for recommended validation.",
                "suggested_figures": f"Figure {i+1}",
                "paper_title": "",
                "mechanism": part.strip(),
                "confidence": "Medium",
            })

    return storylines if storylines else [_empty_storyline(i) for i in range(min(count, 3))]


def _extract_genes(text: str) -> List[str]:
    """Extract gene symbols from text (simple pattern matching)."""
    import re
    # Match uppercase gene symbols (2-8 chars, mostly uppercase with optional numbers)
    genes = re.findall(r'\b([A-Z][A-Z0-9]{1,7})\b', text)
    # Filter out common non-gene words
    stop = {'THE', 'AND', 'FOR', 'ARE', 'NOT', 'BUT', 'HAS', 'HAD', 'WAS', 'ALL', 'CAN', 'MAY', 'VIA', 'PER', 'VIA', 'WITH', 'FROM', 'THIS', 'THAT', 'THESE', 'THOSE', 'EACH', 'WHICH', 'BOTH', 'MORE', 'LESS', 'ALSO', 'VERY', 'JUST', 'LIKE', 'SUCH', 'INTO', 'OVER', 'THAN', 'THEN', 'WHEN', 'WERE', 'WILL', 'WOULD', 'COULD', 'SHOULD', 'ABOUT', 'AFTER', 'BEFORE', 'DURING', 'UNDER', 'ABOVE', 'BELOW', 'BETWEEN', 'THROUGH', 'WHERE', 'WHILE', 'SINCE'}
    return [g for g in genes if g not in stop][:10]


def _empty_storyline(i: int) -> Dict:
    return {
        "title": f"Direction {i+1}",
        "hypothesis": "Run differential analysis and enrichment first to generate storylines.",
        "key_genes": [],
        "key_pathways": [],
        "validation": "Complete analysis pipeline first.",
        "suggested_figures": "",
        "paper_title": "",
        "mechanism": "",
        "confidence": "Low",
    }
