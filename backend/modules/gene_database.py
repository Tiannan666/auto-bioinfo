
"""Real gene set databases: downloads GO, KEGG, MSigDB from public sources."""

import os, gzip, json, time, urllib.request
from pathlib import Path
from typing import Dict, List, Set

DB_DIR = Path(__file__).parent.parent / "gene_db"
DB_DIR.mkdir(parents=True, exist_ok=True)

_go_sets = {}       # GO_ID -> {term, category, genes}
_kegg_sets = {}     # pathway_name -> [genes]
_msigdb_sets = {}   # gene_set_name -> [genes]
_symbol_entrez = {} # symbol -> entrez
_loaded = False


def load_all(force_refresh: bool = False):
    global _loaded
    if _loaded and not force_refresh:
        return
    _load_go(force_refresh)
    _load_msigdb()
    _load_kegg(force_refresh)
    _loaded = True


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': 'BEingBio/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def _download_gz(url: str) -> str:
    data = _download(url)
    return gzip.decompress(data).decode('utf-8', errors='replace')


def _parse_go_obo(text: str) -> Dict[str, Dict]:
    """Parse GO .obo file -> {GO_ID: {name, namespace, is_obsolete}}"""
    terms = {}
    current = None
    for line in text.split('\n'):
        line = line.strip()
        if line == '[Term]':
            current = {}
        elif line == '[Typedef]':
            current = None
        elif current is not None and ': ' in line:
            k, v = line.split(': ', 1)
            if k == 'id':
                current['id'] = v
            elif k == 'name':
                current['name'] = v
            elif k == 'namespace':
                current['namespace'] = v
            elif k == 'is_obsolete' and v == 'true':
                current['obsolete'] = True
            if 'id' in current and 'name' in current and 'namespace' in current:
                terms[current['id']] = current
                current = None
    return terms


def _parse_goa_gaf(text: str) -> Dict[str, Set[str]]:
    """Parse GOA human GAF -> {GO_ID: {gene_symbols}}"""
    go_genes = {}
    for line in text.split('\n'):
        if line.startswith('!'):
            continue
        cols = line.split('\t')
        if len(cols) < 5:
            continue
        # GAF 2.0: DB, DB_Object_ID, DB_Object_Symbol, Qualifier, GO_ID, ...
        if len(cols) >= 5:
            go_id = cols[4]
            gene_symbol = cols[2] if len(cols) > 2 else ''
            qualifier = cols[3] if len(cols) > 3 else ''
            if not go_id.startswith('GO:') or not gene_symbol:
                continue
            if 'NOT' in qualifier:
                continue
            if go_id not in go_genes:
                go_genes[go_id] = set()
            go_genes[go_id].add(gene_symbol.upper())
    return go_genes


def _load_go(force_refresh: bool):
    global _go_sets, _symbol_entrez

    # Try cached first
    cache = DB_DIR / "go_sets.json"
    if cache.exists() and not force_refresh:
        try:
            import json as j
            _go_sets = j.loads(cache.read_text())
            return
        except: pass

    cat_map = {
        'biological_process': 'BP',
        'cellular_component': 'CC',
        'molecular_function': 'MF',
    }

    try:
        print("[GeneDB] Downloading GO ontology...")
        obo_text = _download('http://purl.obolibrary.org/obo/go/go-basic.obo').decode('utf-8', errors='replace')
        terms = _parse_go_obo(obo_text)
        print(f"[GeneDB] GO terms: {len(terms)}")

        print("[GeneDB] Downloading GOA human annotations...")
        gaf_text = _download_gz('ftp://ftp.ebi.ac.uk/pub/databases/GO/goa/HUMAN/goa_human.gaf.gz')
        go_genes = _parse_goa_gaf(gaf_text)
        print(f"[GeneDB] GO annotations: {len(go_genes)} terms with genes")

        # Build category-specific gene sets
        _go_sets = {'BP': {}, 'CC': {}, 'MF': {}}
        for go_id, genes in go_genes.items():
            if go_id not in terms or terms[go_id].get('obsolete'):
                continue
            cat = cat_map.get(terms[go_id].get('namespace', ''), 'BP')
            name = terms[go_id]['name']
            key = f"{go_id} {name}"
            _go_sets[cat][key] = sorted(genes)

        total = sum(len(v) for v in _go_sets.values())
        print(f"[GeneDB] Built GO: {total} terms (BP:{len(_go_sets['BP'])} CC:{len(_go_sets['CC'])} MF:{len(_go_sets['MF'])})")
        import json as j
        cache.write_text(j.dumps(_go_sets))

    except Exception as e:
        print(f"[GeneDB] GO download failed: {e}")
        _build_fallback_go()


def _load_kegg(force_refresh: bool):
    global _kegg_sets
    cache = DB_DIR / "kegg_sets.json"
    if cache.exists() and not force_refresh:
        try:
            _kegg_sets = json.loads(cache.read_text())
            return
        except: pass

    try:
        print("[GeneDB] Fetching KEGG pathways...")
        pathways_text = _download('https://rest.kegg.jp/list/pathway/hsa').decode('utf-8')
        pathways = {}
        for line in pathways_text.strip().split('\n'):
            if '\t' not in line: continue
            pid, name = line.split('\t', 1)
            pid = pid.replace('path:', '')
            pathways[pid] = f"{pid} {name}"

        for pid, name in list(pathways.items())[:350]:
            try:
                genes_text = _download(f'https://rest.kegg.jp/link/genes/{pid}').decode('utf-8')
                genes = []
                for gline in genes_text.strip().split('\n'):
                    if '\t' in gline:
                        gid = gline.split('\t')[1].replace('hsa:', '')
                        # Convert Entrez to symbol if we have it
                        genes.append(_entrez_to_symbol.get(gid, gid))
                if genes:
                    _kegg_sets[name] = genes
            except:
                continue
            if len(_kegg_sets) % 30 == 0:
                time.sleep(0.3)  # Rate limit

        print(f"[GeneDB] KEGG: {len(_kegg_sets)} pathways")
        cache.write_text(json.dumps(_kegg_sets))
    except Exception as e:
        print(f"[GeneDB] KEGG failed: {e}")


def _load_msigdb():
    global _msigdb_sets
    p = DB_DIR / "msigdb_hallmark.json"
    if p.exists():
        try:
            data = json.loads(p.read_text())
            for entry in data:
                name = entry.get('name', '')
                gs = entry.get('geneSymbols', [])
                if name and gs:
                    _msigdb_sets[name] = gs
            return
        except: pass

    # Download from Broad
    try:
        print("[GeneDB] Downloading MSigDB Hallmark...")
        url = "https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2024.1.Hs/h.all.v2024.1.Hs.json"
        data = _download(url).decode('utf-8')
        p.write_text(data)
        data = json.loads(data)
        for entry in data:
            name = entry.get('name', '')
            gs = entry.get('geneSymbols', [])
            if name and gs:
                _msigdb_sets[name] = gs
        print(f"[GeneDB] MSigDB Hallmark: {len(_msigdb_sets)} sets")
    except Exception as e:
        print(f"[GeneDB] MSigDB failed: {e}")


def _build_fallback_go():
    global _go_sets
    _go_sets = {
        'BP': {
            'GO:0002376 immune system process': ['CD4','CD8A','IL2','IL6','TNF','IFNG','IL1B','TLR4','NFKB1','STAT3'],
            'GO:0006954 inflammatory response': ['TNF','IL1B','IL6','CXCL8','CCL2','TLR4','NFKB1','PTGS2','NOS2','IL10'],
        },
        'CC': {
            'GO:0005739 mitochondrion': ['SOD2','CYCS','SDHA','COX4I1','ATP5A1','MFN1','MFN2','OPA1','PINK1'],
        },
        'MF': {
            'GO:0005515 protein binding': ['TP53','MYC','HSP90AA1','ACTB','GAPDH','YWHAZ','PIN1'],
        },
    }


# Store gene symbol→entrez mappings from GO annotations
_entrez_to_symbol = {}
_symbol_to_entrez = {}


def get_go_sets(categories=None):
    load_all()
    cats = categories or ['BP','CC','MF']
    r = {}
    for c in cats:
        if c in _go_sets:
            r.update(_go_sets[c])
    return r


def get_kegg_sets():
    load_all()
    return dict(_kegg_sets)


def get_msigdb_sets():
    load_all()
    return dict(_msigdb_sets)


def get_all_gene_sets():
    r = {}
    r.update(get_go_sets())
    r.update(get_kegg_sets())
    r.update(get_msigdb_sets())
    return r


def get_background_size():
    return 20000
