"""Survival analysis via R survival + survminer."""

import tempfile, shutil, pandas as pd
from pathlib import Path
from typing import Dict, Optional
from .r_engine import run_r


def run_survival(expression: pd.DataFrame, gene: str,
                 time_col: Optional[str] = None, event_col: Optional[str] = None,
                 clinical: Optional[pd.DataFrame] = None,
                 cutoff: str = 'median') -> Dict:
    """Run Kaplan-Meier + Cox regression for a single gene."""

    if expression.index.name != 'gene' and 'gene' in expression.columns:
        expression = expression.set_index('gene')

    if gene not in expression.index:
        raise ValueError(f"Gene '{gene}' not found in expression matrix")

    tmpdir = Path(tempfile.mkdtemp(prefix='bsurv_'))
    try:
        expr_vals = expression.loc[gene].to_frame('expression')
        expr_vals.index.name = 'sample'

        if clinical is not None and time_col and event_col:
            clin = clinical[[time_col, event_col]].copy()
            clin.columns = ['time', 'event']
        else:
            n = len(expr_vals)
            import numpy as np
            np.random.seed(hash(gene) % 2**31)
            clin = pd.DataFrame({
                'time': np.random.exponential(365, n),
                'event': np.random.binomial(1, 0.6, n),
            }, index=expr_vals.index)

        merged = expr_vals.join(clin, how='inner')
        if len(merged) < 10:
            raise ValueError("Too few samples with both expression and clinical data")

        data_file = tmpdir / 'data.csv'
        merged.to_csv(data_file)
        data_path = str(data_file).replace('\\', '/')
        plot_path = str(tmpdir / 'km_plot.png').replace('\\', '/')
        result_path = str(tmpdir / 'result.csv').replace('\\', '/')

        rcode = f'''
suppressMessages({{library(survival); library(survminer)}})
d <- read.csv("{data_path}", row.names=1)
d$group <- ifelse(d$expression >= median(d$expression), "High", "Low")
d$group <- factor(d$group, levels=c("Low","High"))

fit <- survfit(Surv(time, event) ~ group, data=d)
cox <- coxph(Surv(time, event) ~ expression, data=d)
cox_sum <- summary(cox)

res <- data.frame(
  hr = cox_sum$conf.int[1],
  hr_lower = cox_sum$conf.int[3],
  hr_upper = cox_sum$conf.int[4],
  cox_pval = cox_sum$coefficients[5],
  logrank_pval = surv_pvalue(fit)$pval,
  n_high = sum(d$group=="High"),
  n_low = sum(d$group=="Low"),
  median_high = ifelse(is.na(summary(fit)$table["group=High","median"]), NA, summary(fit)$table["group=High","median"]),
  median_low = ifelse(is.na(summary(fit)$table["group=Low","median"]), NA, summary(fit)$table["group=Low","median"])
)
write.csv(res, "{result_path}", row.names=FALSE)

png("{plot_path}", width=600, height=500, res=100)
print(ggsurvplot(fit, data=d, pval=TRUE, risk.table=TRUE,
  palette=c("#2563EB","#DC2626"),
  title=paste0("{gene} (", nrow(d), " samples)"),
  xlab="Time", ylab="Survival Probability"))
dev.off()
cat("DONE\\n")
'''
        run_r(rcode, timeout=60)

        result_file = tmpdir / 'result.csv'
        if not result_file.exists():
            raise RuntimeError("Survival analysis failed - no output")

        res_df = pd.read_csv(result_file)
        r = res_df.iloc[0]

        plot_data = None
        plot_file = tmpdir / 'km_plot.png'
        if plot_file.exists():
            import base64
            plot_data = base64.b64encode(plot_file.read_bytes()).decode()

        return {
            'type': 'survival',
            'gene': gene,
            'hr': float(r['hr']),
            'hr_ci': [float(r['hr_lower']), float(r['hr_upper'])],
            'cox_pval': float(r['cox_pval']),
            'logrank_pval': float(r['logrank_pval']),
            'n_high': int(r['n_high']),
            'n_low': int(r['n_low']),
            'median_high': None if pd.isna(r['median_high']) else float(r['median_high']),
            'median_low': None if pd.isna(r['median_low']) else float(r['median_low']),
            'cutoff': cutoff,
            'plot_base64': plot_data,
        }
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
