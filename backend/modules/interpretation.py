"""AI-powered result interpretation using DeepSeek LLM."""

from typing import Dict, List

from ..deepseek_client import chat as llm_chat


RESEARCH_FOCI = {
    'inflammation': 'Inflammation / 炎症',
    'oxidative_stress': 'Oxidative Stress / 氧化应激',
    'metabolic_reprogramming': 'Metabolic Reprogramming / 代谢重编程',
    'macrophage_polarization': 'Macrophage Polarization / 巨噬细胞极化',
    'bone_remodeling': 'Bone Remodeling / 骨改建',
    'tumor_immunity': 'Tumor Immunity / 肿瘤免疫',
    'mitochondrial': 'Mitochondrial Function / 线粒体功能',
    'cell_death': 'Cell Death / 细胞死亡',
    'immune_regulation': 'Immune Regulation / 免疫调控',
    'cell_proliferation': 'Cell Proliferation / 细胞增殖',
    'cell_migration': 'Cell Migration / 细胞迁移',
    'lipid_metabolism': 'Lipid Metabolism / 脂质代谢',
    'glycolysis': 'Glycolysis / 糖酵解',
    'oxphos': 'Oxidative Phosphorylation / 氧化磷酸化',
}


def generate_interpretation(diff_result: Dict = None, enrich_result: Dict = None,
                            gsea_result: Dict = None, focus: str = '',
                            language: str = 'zh') -> Dict:
    """Generate AI interpretation of analysis results."""

    context = _build_context(diff_result, enrich_result, gsea_result, focus)
    lang_instr = _get_language_instruction(language)

    sections = ['summary', 'results', 'figure_legend', 'discussion', 'verification']
    output = {}

    for section in sections:
        prompt = _build_section_prompt(section, context, lang_instr)
        try:
            resp = llm_chat([{"role": "user", "content": prompt}])
            output[section] = resp.get('content', f'Failed to generate {section}.')
        except Exception:
            output[section] = f'({section} generation requires API key)'

    # Key findings: top DEGs + top pathways
    key_genes = []
    if diff_result:
        key_genes = [g['gene'] for g in diff_result.get('top_genes', [])[:10]]
    key_terms = []
    if enrich_result:
        key_terms = [t['term'] for t in enrich_result.get('terms', [])[:5]]

    output['key_findings'] = f"Key genes: {', '.join(key_genes) if key_genes else 'N/A'}. Key pathways: {', '.join(key_terms) if key_terms else 'N/A'}."

    return output


def _build_context(diff, enrich, gsea, focus) -> str:
    parts = []
    if focus and focus in RESEARCH_FOCI:
        parts.append(f"Research focus: {RESEARCH_FOCI[focus]}")
    if diff:
        parts.append(f"Differential analysis: {diff.get('n_up', 0)} up-regulated, {diff.get('n_down', 0)} down-regulated genes (FDR<{diff.get('fdr_threshold', 0.05)}, |log2FC|>{diff.get('logfc_threshold', 1.0)}).")
        top = diff.get('top_genes', [])[:10]
        gene_strs = []
        for g in top:
            gene_strs.append('{}({}, logFC={:.2f})'.format(g["gene"], g["direction"], g["logfc"]))
        parts.append("Top DEGs: " + ", ".join(gene_strs))
    if enrich:
        top_terms = enrich.get('terms', [])[:5]
        term_strs = ['{} (FDR={:.1e})'.format(t["term"], t["fdr"]) for t in top_terms]
        parts.append("Top enriched terms: " + ", ".join(term_strs))
    if gsea:
        top_gsea = gsea.get('terms', [])[:5]
        gsea_strs = ['{} (NES={:.2f}, FDR={:.1e})'.format(t["term"], t["nes"], t["fdr"]) for t in top_gsea]
        parts.append("Top GSEA terms: " + ", ".join(gsea_strs))
    return '\n'.join(parts)


def _get_language_instruction(lang: str) -> str:
    if lang == 'zh':
        return 'Please respond in Chinese. Write professionally as for a scientific paper.'
    elif lang == 'en':
        return 'Please respond in English. Write professionally as for a scientific paper.'
    else:
        return 'Please provide bilingual output (Chinese + English). Write professionally as for a scientific paper.'


def _build_section_prompt(section: str, context: str, lang_instr: str) -> str:
    prompts = {
        'summary': f"""Based on the following bioinformatics analysis results, write a concise summary (2-3 sentences) of key findings. Focus on the most significant genes and pathways. {lang_instr}

Analysis context:
{context}

Summary:""",

        'results': f"""Based on the following bioinformatics analysis results, write a detailed "Results" section suitable for a scientific paper. Describe the differential expression patterns, enriched pathways, and their biological relevance. Include specific gene names and statistics where available. Use formal scientific language. {lang_instr}

Analysis context:
{context}

Results:""",

        'figure_legend': f"""Based on the following bioinformatics results, write figure legends for the key figures (volcano plot, heatmap, enrichment plots). Each legend should be 2-4 sentences. {lang_instr}

Analysis context:
{context}

Figure Legends:""",

        'discussion': f"""Based on the following bioinformatics results, write a short Discussion paragraph (4-6 sentences) interpreting the biological significance of the findings, relating them to potential mechanisms, and suggesting future directions. Connect the dots between differentially expressed genes and enriched pathways. {lang_instr}

Analysis context:
{context}

Discussion:""",

        'verification': f"""Based on the following bioinformatics results, recommend 3-4 experimental validation approaches that would strengthen the findings. Include specific techniques (e.g., qPCR, Western blot, ELISA, IHC, knockdown/overexpression) and which genes/pathways to validate. {lang_instr}

Analysis context:
{context}

Recommended Validation:""",
    }
    return prompts.get(section, f"Analyze: {context}")
