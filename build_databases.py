"""Build GO + KEGG + MSigDB gene set databases."""
import subprocess, json, time, os, re
from pathlib import Path

DB = Path('backend/gene_db')
DB.mkdir(exist_ok=True)

def curl(url, timeout=30):
    r = subprocess.run(['curl', '-sL', '--max-time', str(timeout), url],
                       capture_output=True, text=True,
                       env={**os.environ, 'no_proxy': '*', 'http_proxy': '', 'https_proxy': ''})
    if r.returncode != 0:
        raise Exception(r.stderr[:100])
    return r.stdout

# ===== 1. MSigDB Hallmark (GMT format) =====
print("[1/4] MSigDB Hallmark (GMT format)...")
gmt_url = 'https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2024.1.Hs/h.all.v2024.1.Hs.symbols.gmt'
gmt_text = curl(gmt_url)
msig = {}
for line in gmt_text.strip().split('\n'):
    parts = line.strip().split('\t')
    if len(parts) >= 3:
        name = parts[0]
        url_ref = parts[1]
        genes = [g for g in parts[2:] if g.strip()]
        if genes:
            msig[name] = genes
print(f'  MSigDB: {len(msig)} hallmark gene sets')
# Save as JSON for easy loading
json.dump(msig, open(DB / 'msigdb_hallmark.json', 'w'), ensure_ascii=False)

# ===== 2. KEGG pathways (GET endpoint) =====
print("[2/4] KEGG pathways...")
pwy_text = curl('https://rest.kegg.jp/list/pathway/hsa')
kegg = {}
pathways = []
for line in pwy_text.strip().split('\n'):
    if '\t' in line:
        pid, name = line.split('\t', 1)
        pathways.append((pid.replace('path:', ''), name))

for pid, name in pathways[:350]:
    try:
        kgml = curl(f'https://rest.kegg.jp/get/{pid}', 15)
        genes = re.findall(r'hsa:(\d+)', kgml)
        if len(genes) >= 5:
            kegg[f'{pid} {name}'] = list(set(genes))
    except Exception:
        pass
    if len(kegg) % 30 == 0 and len(kegg) > 0:
        print(f'  {len(kegg)} pathways...')
        time.sleep(0.3)
print(f'  KEGG: {len(kegg)} pathways saved')
json.dump(kegg, open(DB / 'kegg_sets.json', 'w'), ensure_ascii=False)

# ===== 3. GO from mygene (per-gene) =====
print("[3/4] GO via mygene.info...")
all_genes = set()
for gs in kegg.values():
    all_genes.update(gs)
for gs in msig.values():
    all_genes.update(gs)
print(f'  Genes to query: {len(all_genes)}')

go_sets = {'BP': {}, 'CC': {}, 'MF': {}}
queried = 0
for gene in list(all_genes)[:8000]:
    try:
        data = json.loads(curl(f'https://mygene.info/v3/gene/{gene}?fields=go,symbol&species=human', 8))
        symbol = data.get('symbol', gene).upper()
        for ont in ['BP', 'CC', 'MF']:
            for te in data.get('go', {}).get(ont, []):
                gid = te.get('id', '')
                tn = te.get('term', '')
                if gid and tn:
                    go_sets[ont].setdefault(f'GO:{gid} {tn}', set()).add(symbol)
        queried += 1
    except Exception:
        pass
    if queried % 300 == 0:
        print(f'  {queried}/{min(len(all_genes), 8000)} genes...')
    time.sleep(0.03)

for ont in go_sets:
    for key in go_sets[ont]:
        go_sets[ont][key] = sorted(go_sets[ont][key])
total = sum(len(v) for v in go_sets.values())
print(f'  Built: {total} GO terms (BP:{len(go_sets["BP"])} CC:{len(go_sets["CC"])} MF:{len(go_sets["MF"])})')
json.dump(go_sets, open(DB / 'go_sets.json', 'w'), ensure_ascii=False)

# ===== 4. Summary =====
print("\n[4/4] Database sizes:")
total_sz = 0
for f in sorted(DB.glob('*.json')):
    sz = os.path.getsize(f)
    total_sz += sz
    print(f'  {f.name}: {sz//1024}KB')
print(f'Total: {total_sz//1024}KB = {total_sz/1024/1024:.1f}MB')
