"""GO and KEGG enrichment analysis using hypergeometric test."""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List


# Built-in GO gene sets (human, simplified for demo)
GO_SETS = {
    "BP": {
        "GO:0002376 immune system process": ["CD4", "CD8A", "CD8B", "IL2", "IL6", "TNF", "IFNG", "IL1B", "CXCL8", "CCL2", "TLR4", "NFKB1", "RELA", "STAT3", "JAK2"],
        "GO:0006954 inflammatory response": ["TNF", "IL1B", "IL6", "CXCL8", "CCL2", "TLR4", "NFKB1", "PTGS2", "NOS2", "IL10", "TGFB1", "HMGB1", "S100A8", "S100A9", "CRP"],
        "GO:0006979 response to oxidative stress": ["SOD1", "SOD2", "CAT", "GPX1", "GPX4", "PRDX1", "PRDX2", "TXN", "TXNRD1", "NFE2L2", "KEAP1", "HMOX1", "NQO1", "GCLM", "GCLC"],
        "GO:0006096 glycolytic process": ["HK2", "GPI", "PFKL", "ALDOA", "GAPDH", "PGK1", "PGAM1", "ENO1", "PKM", "LDHA", "SLC2A1", "HK1", "PFKP", "ALDOC", "TPI1"],
        "GO:0006119 oxidative phosphorylation": ["NDUFA1", "SDHA", "UQCRC1", "COX4I1", "ATP5A1", "NDUFS1", "SDHB", "UQCRC2", "COX5A", "ATP5B", "NDUFV1", "SDHC", "CYTB", "COX6B1", "ATP5C1"],
        "GO:0006915 apoptotic process": ["BCL2", "BAX", "CASP3", "CASP8", "CASP9", "TP53", "FAS", "BID", "CYCS", "APAF1", "BAD", "BAK1", "BIM", "PUMA", "NOXA"],
        "GO:0030335 positive regulation of cell migration": ["CCL2", "CCL5", "CXCL12", "EGF", "FGF2", "HGF", "IGF1", "PDGFB", "TGFB1", "VEGFA", "MMP2", "MMP9", "ITGB1", "ITGAV", "FN1"],
        "GO:0008283 cell proliferation": ["MYC", "CCND1", "CDK4", "EGFR", "FGF2", "PCNA", "MKI67", "E2F1", "RB1", "CDKN1A", "CDKN2A", "JUN", "FOS", "KRAS", "BRAF"],
        "GO:0045087 innate immune response": ["TLR2", "TLR3", "TLR4", "MYD88", "IRF3", "IRF7", "IFNB1", "IFNA1", "MAVS", "RIGI", "CGAS", "STING", "NLRP3", "AIM2", "IFI16"],
        "GO:0007155 cell adhesion": ["CDH1", "CDH2", "ITGB1", "ITGA5", "ICAM1", "VCAM1", "SELE", "CD44", "CTNNB1", "CLDN1", "OCLN", "TJP1", "DSC2", "DSG2", "PECAM1"],
        "GO:0006629 lipid metabolic process": ["PPARG", "SREBF1", "FASN", "ACACA", "SCD", "CD36", "LPL", "LDLR", "HMGCR", "CYP7A1", "APOE", "ABCA1", "CPT1A", "ACOX1", "FADS1"],
        "GO:0043066 negative regulation of apoptotic process": ["BCL2", "BCL2L1", "MCL1", "XIAP", "SURVIVIN", "HSPA1A", "HSPA1B", "AKT1", "PIK3CA", "NFKB1", "CREB1", "BDNF", "NGF", "GDNF", "IGF1"],
        "GO:1901700 response to oxygen-containing compound": ["HIF1A", "EPAS1", "VEGFA", "EPO", "GLUT1", "LDHA", "PDK1", "BNIP3", "CA9", "ADM", "ANGPT2", "FLT1", "KDR", "TEK", "ENG"],
        "GO:0072593 reactive oxygen species metabolic process": ["NOX1", "NOX4", "CYBB", "SOD1", "SOD2", "CAT", "GPX1", "PRDX1", "TXN", "NFE2L2", "HMOX1", "MPO", "DUOX1", "DUOX2", "XDH"],
        "GO:0060548 negative regulation of cell death": ["BCL2", "BCL2L1", "MCL1", "XIAP", "BIRC5", "HSPB1", "CRYAB", "SERPINB2", "AVEN", "BAG1", "BAG3", "HGF", "MET", "IL3", "CSF2"],
    },
    "CC": {
        "GO:0005739 mitochondrion": ["SOD2", "CYCS", "SDHA", "COX4I1", "ATP5A1", "HSPD1", "TUFM", "TFAM", "POLG", "MFN1", "MFN2", "OPA1", "DRP1", "FIS1", "PINK1"],
        "GO:0005783 endoplasmic reticulum": ["HSPA5", "CALR", "PDIA3", "ERO1A", "ATF4", "ATF6", "XBP1", "ERN1", "EIF2AK3", "SEC61A1", "CANX", "HSP90B1", "DDIT3", "GDF15", "HERPUD1"],
        "GO:0005634 nucleus": ["TP53", "MYC", "FOS", "JUN", "RELA", "NFKB1", "STAT3", "HIF1A", "NRF2", "PPARG", "ESR1", "AR", "SP1", "E2F1", "CTNNB1"],
        "GO:0005886 plasma membrane": ["EGFR", "TLR4", "CD4", "CD8A", "ITGB1", "ICAM1", "VCAM1", "FAS", "TNFRSF1A", "IL2RA", "PECAM1", "CD44", "SLC2A1", "SLC7A11", "ABCB1"],
        "GO:0005576 extracellular region": ["TNF", "IL1B", "IL6", "CXCL8", "CCL2", "IFNG", "IL10", "TGFB1", "VEGFA", "EGF", "FGF2", "HGF", "IGF1", "MMP2", "MMP9"],
    },
    "MF": {
        "GO:0005515 protein binding": ["TP53", "MYC", "HSP90AA1", "HSPA1A", "ACTB", "GAPDH", "YWHAZ", "UBC", "SUMO1", "NEDD8", "PIN1", "FKBP1A", "PPIA", "PRKACA", "CSNK2A1"],
        "GO:0000166 nucleotide binding": ["KRAS", "HRAS", "NRAS", "RAC1", "CDC42", "RHOA", "RAB5A", "RAB7A", "ARF1", "ARF6", "RAN", "RHEB", "GNAI1", "GNAQ", "GNAS"],
        "GO:0016491 oxidoreductase activity": ["SOD1", "SOD2", "CAT", "GPX1", "PRDX1", "TXN", "TXNRD1", "NQO1", "HMOX1", "CYP2E1", "CYP1A1", "CYP3A4", "MAOA", "MAOB", "IDH1"],
        "GO:0003700 DNA-binding transcription factor activity": ["TP53", "MYC", "FOS", "JUN", "RELA", "NFKB1", "STAT3", "HIF1A", "PPARG", "ESR1", "AR", "E2F1", "CREB1", "CTCF", "YY1"],
        "GO:0004871 signal transducer activity": ["EGFR", "TLR4", "IFNGR1", "IL2RA", "TNFRSF1A", "FAS", "TGFBR1", "TGFBR2", "BMPR1A", "NOTCH1", "WNT1", "FZD1", "LRP5", "LRP6", "PTCH1"],
    },
}

# Built-in KEGG pathways (human, simplified)
KEGG_PATHWAYS = {
    "hsa04060 Cytokine-cytokine receptor interaction": ["TNF", "IL1B", "IL6", "CXCL8", "CCL2", "IL10", "IFNG", "TGFB1", "IL2", "IL4", "CCL5", "CXCL10", "CCR5", "CXCR4", "TNFRSF1A"],
    "hsa04064 NF-kappa B signaling pathway": ["RELA", "NFKB1", "IKBKB", "IKBKG", "TNF", "IL1B", "TLR4", "MYD88", "TRAF6", "RIPK1", "BCL2", "XIAP", "PTGS2", "VCAM1", "ICAM1"],
    "hsa04657 IL-17 signaling pathway": ["IL17A", "IL17RA", "TRAF6", "NFKB1", "RELA", "FOS", "JUN", "CXCL8", "CCL2", "MMP9", "PTGS2", "CSF2", "CSF3", "S100A8", "S100A9"],
    "hsa04668 TNF signaling pathway": ["TNF", "TNFRSF1A", "TRADD", "TRAF2", "RIPK1", "NFKB1", "RELA", "FOS", "JUN", "CASP3", "CASP8", "MAP3K7", "TAB1", "TAB2", "TAB3"],
    "hsa04210 Apoptosis": ["BCL2", "BAX", "CASP3", "CASP8", "CASP9", "TP53", "CYCS", "APAF1", "BID", "FAS", "TNFRSF1A", "AKT1", "PIK3CA", "BAD", "ENDOG"],
    "hsa04151 PI3K-Akt signaling pathway": ["PIK3CA", "AKT1", "MTOR", "PTEN", "EGFR", "IGF1R", "ERBB2", "CCND1", "MYC", "BCL2", "BCL2L1", "CREB1", "GSK3B", "FOXO3", "TSC1"],
    "hsa04010 MAPK signaling pathway": ["KRAS", "BRAF", "MAP2K1", "MAPK1", "MAPK3", "JUN", "FOS", "TP53", "EGFR", "FGFR1", "PDGFRA", "TGFBR1", "TGFBR2", "RAC1", "CDC42"],
    "hsa04216 Ferroptosis": ["GPX4", "SLC7A11", "ACSL4", "LPCAT3", "TFRC", "FTH1", "FTL", "NFE2L2", "HMOX1", "SAT1", "ALOX5", "ALOX12", "ALOX15", "VDAC2", "VDAC3"],
    "hsa04932 Non-alcoholic fatty liver disease": ["TNF", "IL6", "RELA", "NFKB1", "INSR", "IRS1", "SREBF1", "PPARA", "PPARG", "CPT1A", "FASN", "ACACA", "LEP", "ADIPOQ", "CXCL8"],
    "hsa05200 Pathways in cancer": ["TP53", "MYC", "KRAS", "EGFR", "PIK3CA", "AKT1", "MTOR", "CCND1", "CDKN2A", "RB1", "HIF1A", "VEGFA", "MMP9", "PTEN", "BCL2"],
    "hsa00190 Oxidative phosphorylation": ["NDUFA1", "SDHA", "UQCRC1", "COX4I1", "ATP5A1", "NDUFS1", "SDHB", "UQCRC2", "COX5A", "ATP5B", "NDUFV1", "SDHC", "CYTB", "COX6B1", "ATP5C1"],
    "hsa00010 Glycolysis / Gluconeogenesis": ["HK2", "GPI", "PFKL", "ALDOA", "GAPDH", "PGK1", "PGAM1", "ENO1", "PKM", "LDHA", "PCK1", "FBP1", "G6PC", "PDHA1", "PDK1"],
    "hsa04974 Protein digestion and absorption": ["COL1A1", "COL1A2", "COL3A1", "COL4A1", "COL5A1", "ELN", "DPP4", "ACE2", "SLC1A1", "SLC7A9", "SLC3A2", "SLC7A7", "SLC36A1", "SLC15A1", "ANPEP"],
    "hsa04621 NOD-like receptor signaling": ["NLRP3", "NOD1", "NOD2", "RIPK2", "NFKB1", "RELA", "IL1B", "IL18", "CASP1", "TXNIP", "NEK7", "PYCARD", "CARD8", "TAB1", "TAB2"],
    "hsa04380 Osteoclast differentiation": ["TNFRSF11A", "TNFSF11", "TNF", "IL1B", "FOS", "JUN", "NFKB1", "RELA", "NFATC1", "MITF", "CSF1", "CSF1R", "ACPS", "CTSK", "MMP9"],
    "hsa04612 Antigen processing and presentation": ["HLA-A", "HLA-B", "HLA-C", "B2M", "TAP1", "TAP2", "TAPBP", "CALR", "CANX", "PDIA3", "HSPA5", "HSP90AA1", "CD74", "CTSS", "CTSL"],
    "hsa04066 HIF-1 signaling pathway": ["HIF1A", "EPAS1", "VEGFA", "EPO", "SLC2A1", "LDHA", "PDK1", "BNIP3", "HMOX1", "TFRC", "SERPINE1", "EDN1", "IGF1", "EGF", "ANGPT2"],
    "hsa04310 Wnt signaling pathway": ["CTNNB1", "WNT1", "FZD1", "LRP5", "LRP6", "DVL1", "GSK3B", "AXIN1", "APC", "TCF7L2", "LEF1", "MYC", "CCND1", "JUN", "MMP7"],
}


def run_enrichment(gene_list: List[str], background_size: int = 20000,
                   pval_cutoff: float = 0.05, go_bp: bool = True,
                   go_cc: bool = True, go_mf: bool = True,
                   kegg: bool = True) -> Dict:
    """Run hypergeometric enrichment test for GO and KEGG."""

    gene_set = set(g.upper() for g in gene_list)
    n_query = len(gene_set)
    results = []
    total_bg = background_size

    # GO enrichment
    if go_bp or go_cc or go_mf:
        ontologies = []
        if go_bp: ontologies.append(("BP", GO_SETS.get("BP", {})))
        if go_cc: ontologies.append(("CC", GO_SETS.get("CC", {})))
        if go_mf: ontologies.append(("MF", GO_SETS.get("MF", {})))

        for ont_name, terms in ontologies:
            for term_id, term_genes in terms.items():
                term_set = set(g.upper() for g in term_genes)
                overlap = gene_set & term_set
                if len(overlap) < 2:
                    continue
                k = len(overlap)
                m = len(term_set)
                pval = stats.hypergeom.sf(k - 1, total_bg, m, n_query)
                results.append({
                    "term": term_id.split(" ", 1)[1] if " " in term_id else term_id,
                    "id": term_id.split(" ", 1)[0] if " " in term_id else term_id,
                    "category": f"GO_{ont_name}",
                    "gene_count": k,
                    "pvalue": pval,
                    "fdr": 1.0,
                    "genes": sorted(overlap)[:10],
                    "total_genes": m,
                })

    # KEGG enrichment
    if kegg:
        for pathway_id, pathway_genes in KEGG_PATHWAYS.items():
            term_set = set(g.upper() for g in pathway_genes)
            overlap = gene_set & term_set
            if len(overlap) < 2:
                continue
            k = len(overlap)
            m = len(term_set)
            pval = stats.hypergeom.sf(k - 1, total_bg, m, n_query)
            results.append({
                "term": pathway_id.split(" ", 1)[1] if " " in pathway_id else pathway_id,
                "id": pathway_id.split(" ", 1)[0] if " " in pathway_id else pathway_id,
                "category": "KEGG",
                "gene_count": k,
                "pvalue": pval,
                "fdr": 1.0,
                "genes": sorted(overlap)[:10],
                "total_genes": m,
            })

    if not results:
        return {"type": "go_kegg", "terms": [], "n_terms": 0, "gene_count": n_query}

    # Multiple testing correction
    results.sort(key=lambda x: x["pvalue"])
    n = len(results)
    for i, r in enumerate(results):
        r["fdr"] = min(r["pvalue"] * n / (i + 1), 1.0)
    for i in range(n - 2, -1, -1):
        results[i]["fdr"] = min(results[i]["fdr"], results[i + 1]["fdr"])

    # Filter by p-value
    significant = [r for r in results if r["fdr"] < pval_cutoff]

    return {
        "type": "go_kegg",
        "terms": significant[:50],
        "n_terms": len(significant),
        "gene_count": n_query,
    }
