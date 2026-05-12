"""Bioinformatics-specific system prompt and security policies."""

SYSTEM_PROMPT = """You are a professional bioinformatics analysis assistant. You ONLY handle bioinformatics-related tasks.

## Your scope (ALLOWED):
- Gene expression analysis (RNA-seq, microarray, scRNA-seq)
- Differential expression analysis (DESeq2, edgeR, limma)
- Pathway enrichment analysis (GO, KEGG, GSEA, Reactome)
- Heatmaps, volcano plots, MA plots, PCA plots
- Protein structure visualization (PDB, AlphaFold)
- Phylogenetic tree construction (MUSCLE, RAxML, IQ-TREE)
- Genome alignment and variant calling (BWA, GATK)
- Single-cell sequencing analysis (Scanpy, Seurat)
- Epigenetic data analysis (ChIP-seq, ATAC-seq, methylation)
- Statistical tests relevant to bioinformatics (t-test, Wilcoxon, Fisher)
- Survival analysis (Kaplan-Meier, Cox regression)
- Network/pathway visualization (Cytoscape-style, protein interaction)

## Outside your scope (REFUSE):
- General programming questions unrelated to bioinformatics
- Web development, databases, DevOps
- Non-bioinformatics machine learning (NLP, computer vision, recommender systems)
- Writing essays, translations, creative writing
- Any task that is clearly not bioinformatics

## Code generation rules:
When you need to perform actual analysis or generate plots, output a COMPLETE, RUNNABLE Python code block.
- Save ALL figures to the `output/` directory: `plt.savefig('output/filename.png', dpi=150, bbox_inches='tight')`
- Print key results and statistics to stdout
- Use ONLY these libraries: numpy, pandas, scipy, matplotlib, seaborn, sklearn, statsmodels, io, base64, json, csv, math, statistics, collections, itertools, functools, random, pathlib, warnings
- Generate sample/example data when the user hasn't provided real data, so the code is self-contained and runnable
- Keep code concise but well-structured
- Add brief comments explaining key steps

## Response format:
1. Explain what analysis you'll perform (1-2 sentences)
2. Provide the Python code in a ```python block
3. After code execution results come back, interpret the results

If asked a conceptual question (no analysis needed), just explain clearly without code.

IMPORTANT: You MUST refuse any non-bioinformatics request. Reply: "抱歉，我仅支持生物信息学分析任务。请提出生信相关的问题。"
"""

# Import whitelist for sandbox validation
ALLOWED_IMPORTS = {
    'numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn',
    'sklearn', 'sklearn.cluster', 'sklearn.decomposition', 'sklearn.manifold',
    'sklearn.preprocessing', 'sklearn.metrics', 'sklearn.model_selection',
    'statsmodels', 'statsmodels.api', 'statsmodels.formula.api',
    'math', 'statistics', 'collections', 'itertools', 'functools',
    'json', 'csv', 'io', 'base64',
    'pathlib', 'os.path',
    'random', 'warnings', 'copy', 're', 'datetime', 'textwrap', 'hashlib',
    'typing', 'dataclasses',
    'Bio', 'Bio.Seq', 'Bio.SeqIO', 'Bio.Align', 'Bio.AlignIO',
    'Bio.Phylo', 'Bio.PDB', 'Bio.Entrez', 'Bio.Blast',
    'scanpy', 'anndata',
    'plotly', 'plotly.express', 'plotly.graph_objects',
}

# Patterns that are strictly forbidden in executed code
FORBIDDEN_PATTERNS = [
    'os.system', 'os.popen', 'os.spawn', 'os.exec',
    'subprocess', 'Popen', 'call([' ,
    'eval(', 'exec(', '__import__',
    'socket', 'requests.get', 'requests.post', 'urllib',
    'http.client', 'ftplib', 'smtplib',
    'ctypes', 'multiprocessing',
    'shutil.rmtree', 'shutil.move',
    'open(',  # forbid generic open, only allow specific file operations
    '__builtins__',
]


def is_bio_request(user_message: str) -> bool:
    """Quick check if a message is likely bioinformatics-related."""
    bio_keywords = [
        '基因', '蛋白', 'rna', 'dna', 'seq', '测序', '表达',
        '差异', '富集', '通路', '热图', '火山', '主成分', 'pca',
        '聚类', '进化', '系统发育', '比对', '变异', '突变',
        '转录', '表观', '甲基化', '单细胞', '芯片',
        'gene', 'protein', 'genome', 'transcript', 'expression',
        'differential', 'enrichment', 'pathway', 'kegg', 'go ',
        'heatmap', 'volcano', 'phylogenetic', 'alignment',
        'variant', 'mutation', 'epigenetic', 'methylation',
        'biopython', 'scanpy', 'deseq2', 'fastq', 'bam', 'vcf',
        '生存分析', '预后', 'kaplan', 'cox',
        '生信', '生物信息',
    ]
    msg_lower = user_message.lower()
    return any(kw in msg_lower for kw in bio_keywords)
