// i18n — Internationalization for BioInfo Platform
// Chinese mode keeps all technical terms (RNA, DNA, PCR, GO, KEGG, etc.) in English.

const I18N = {
  _lang: localStorage.getItem('bioinfo_lang') || 'en',

  get lang() { return this._lang; },

  setLang(lang) {
    this._lang = lang;
    localStorage.setItem('bioinfo_lang', lang);
    applyI18nAll();
    // Force re-render even if same page
    App.currentPage = null;
    const hash = window.location.hash || '#dashboard';
    App.navigate(hash.replace('#', ''));
  },

  // Scan all [data-i18n] elements and update text
  applyAll() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      const val = I18N.t(key);
      if (val && val !== key) {
        // For <select> options, update textContent only
        if (el.tagName === 'OPTION') {
          el.textContent = val;
        } else if (el.children.length === 0) {
          // Leaf element: just text
          el.textContent = val;
        } else {
          // Element with children: update only the first text node
          for (let node of el.childNodes) {
            if (node.nodeType === 3 && node.textContent.trim()) {
              node.textContent = ' ' + val + ' ';
              break;
            }
          }
        }
      }
    });
    // Update page title
    document.getElementById('pageTitle').textContent = I18N.t('nav.' + App.currentPage) || 'Dashboard';
  }
};

  t(key) {
    const val = DICT[key];
    if (!val) return key;
    return val[this._lang] || val['en'] || key;
  }
};

const DICT = {
  // App
  'app.title': { zh: 'BEing Bio', en: 'BEing Bio' },
  'app.settings': { zh: '设置', en: 'Settings' },
  'app.api_ready': { zh: 'API 已配置', en: 'API Ready' },
  'app.no_api_key': { zh: '未配置 API Key', en: 'No API Key' },
  'app.save': { zh: '保存', en: 'Save' },
  'app.cancel': { zh: '取消', en: 'Cancel' },
  'app.language': { zh: '界面语言', en: 'Language' },

  // Sidebar
  'nav.analysis_workflow': { zh: '分析流程', en: 'Analysis Workflow' },
  'nav.dashboard': { zh: 'Dashboard', en: 'Dashboard' },
  'nav.data_import': { zh: '数据导入', en: 'Data Import' },
  'nav.quality_control': { zh: '质量检查', en: 'Quality Control' },
  'nav.differential': { zh: '差异分析', en: 'Differential Analysis' },
  'nav.enrichment': { zh: '富集分析', en: 'Enrichment Analysis' },
  'nav.visualization': { zh: '可视化', en: 'Visualization' },
  'nav.intelligence': { zh: '智能分析', en: 'Intelligence' },
  'nav.interpretation': { zh: '结果解读', en: 'Interpretation' },
  'nav.storyline': { zh: '故事线推荐', en: 'Storyline' },
  'nav.output': { zh: '结果输出', en: 'Output' },
  'nav.report_export': { zh: '报告导出', en: 'Report Export' },
  'nav.scrna': { zh: 'scRNA-seq', en: 'scRNA-seq' },
  'nav.coming_soon': { zh: '即将推出', en: 'Soon' },

  // Dashboard
  'dashboard.welcome': { zh: '欢迎使用 BioInfo Platform。按照以下流程从原始数据到可用于发表的结果。', en: 'Welcome to BioInfo Platform. Follow the workflow below to go from raw data to publication-ready results.' },
  'dashboard.workflow': { zh: '分析流程', en: 'Analysis Workflow' },
  'dashboard.recent_projects': { zh: '最近项目', en: 'Recent Projects' },
  'dashboard.data_status': { zh: '数据状态', en: 'Data Status' },
  'dashboard.analysis_progress': { zh: '分析进度', en: 'Analysis Progress' },
  'dashboard.exported_reports': { zh: '已导出报告', en: 'Exported Reports' },
  'dashboard.quick_start': { zh: '快速开始', en: 'Quick Start' },
  'dashboard.quick_start_desc': { zh: '导入表达数据和分组信息，开始分析。', en: 'Import your expression data and metadata to begin analysis.' },
  'dashboard.start_analysis': { zh: '开始新分析', en: 'Start New Analysis' },
  'dashboard.supported_types': { zh: '支持的数据类型', en: 'Supported Data Types' },
  'dashboard.type_bulk': { zh: 'Bulk RNA-seq 表达矩阵 (counts/TPM/FPKM)', en: 'Bulk RNA-seq Expression Matrix (counts/TPM/FPKM)' },
  'dashboard.type_meta': { zh: 'Metadata / 分组信息', en: 'Metadata / Group Information' },
  'dashboard.type_diff': { zh: '差异基因结果表', en: 'Differential Gene Result Tables' },
  'dashboard.type_go': { zh: 'GO / KEGG / GSEA 富集结果', en: 'GO / KEGG / GSEA Enrichment Results' },
  'dashboard.type_geo': { zh: 'GEO Series (GSE accession)', en: 'GEO Series (GSE accession)' },
  'dashboard.type_scrna': { zh: 'scRNA-seq (即将推出)', en: 'scRNA-seq (coming soon)' },

  // Data Import
  'data.desc': { zh: '输入文件路径、文件夹路径或 GEO accession 编号。系统将自动检测数据类型和结构。', en: 'Enter a file path, folder path, or GEO accession number. The system will automatically detect the data type and structure.' },
  'data.source': { zh: '数据来源', en: 'Data Source' },
  'data.path_label': { zh: '文件路径 / 文件夹路径 / GEO ID', en: 'File Path / Folder Path / GEO ID' },
  'data.path_placeholder': { zh: '例如: C:/data/expr_matrix.csv  或  GSE123456', en: 'e.g. C:/data/expr_matrix.csv  or  GSE123456' },
  'data.detect_btn': { zh: '自动检测', en: 'Auto-Detect' },
  'data.hint': { zh: '支持: CSV, TSV, TXT, Excel (.xlsx), 或 GEO accession (GSE...)', en: 'Supports: CSV, TSV, TXT, Excel (.xlsx), or GEO accession (GSE...)' },
  'data.detecting': { zh: '正在检测数据类型...', en: 'Detecting data type...' },
  'data.detection_failed': { zh: '检测失败', en: 'Detection failed' },
  'data.detection_result': { zh: '检测结果', en: 'Detection Results' },
  'data.samples': { zh: '样本数', en: 'Samples' },
  'data.genes': { zh: '基因/特征数', en: 'Genes/Features' },
  'data.groups': { zh: '分组数', en: 'Groups' },
  'data.file_type': { zh: '文件类型', en: 'File Type' },
  'data.no_issues': { zh: '未检测到问题', en: 'No issues detected' },
  'data.next_steps': { zh: '下一步', en: 'Next Steps' },
  'data.load_continue': { zh: '加载数据并进入 QC', en: 'Load Data & Continue to QC' },
  'data.skip_qc': { zh: '跳过质量检查', en: 'Skip to Quality Control' },
  'data.reset': { zh: '重置', en: 'Reset' },

  // QC
  'qc.desc': { zh: '对已加载的数据进行质量检查。在分析前检查样本匹配、缺失值、异常值和数据分布。', en: 'Run quality checks on your loaded data. Review sample matching, missing values, outliers, and distribution before proceeding to analysis.' },
  'qc.title': { zh: '质量检查', en: 'Quality Control' },
  'qc.desc2': { zh: '检查项目: 样本名称匹配、缺失值、重复基因、非数值数据、异常值、log2 转换需求、分组平衡。', en: 'Checks: sample name matching, missing values, duplicate genes, non-numeric data, outliers, log2 transformation need, group balance.' },
  'qc.run_btn': { zh: '运行质量检查', en: 'Run Quality Check' },
  'qc.back': { zh: '返回数据导入', en: 'Back to Data Import' },
  'qc.running': { zh: '正在运行...', en: 'Running...' },
  'qc.proceed_diff': { zh: '进入差异分析', en: 'Proceed to Differential Analysis' },
  'qc.reimport': { zh: '重新导入数据', en: 'Re-import Data' },
  'qc.checking': { zh: '正在检查', en: 'Checking' },
  'qc.results': { zh: 'QC 结果', en: 'QC Results' },
  'qc.passed': { zh: '项通过', en: 'Passed' },
  'qc.all_passed': { zh: '所有 QC 检查通过，可以进行分析。', en: 'All QC checks passed. Ready for analysis.' },
  'qc.check_names': { zh: '样本名称匹配', en: 'Sample Name Matching' },
  'qc.check_missing': { zh: '缺失值', en: 'Missing Values' },
  'qc.check_dupes': { zh: '重复基因名', en: 'Duplicate Gene Names' },
  'qc.check_numeric': { zh: '非数值数据', en: 'Non-Numeric Values' },
  'qc.check_outliers': { zh: '异常值检测', en: 'Outlier Detection' },
  'qc.check_log2': { zh: 'log2 转换需求', en: 'Log2 Transform Need' },
  'qc.check_group': { zh: '分组平衡', en: 'Group Balance' },

  // Differential
  'diff.desc': { zh: '运行差异表达分析。设置比较组、阈值和筛选参数。', en: 'Run differential expression analysis. Set comparison groups, thresholds, and filtering parameters.' },
  'diff.params': { zh: '分析参数', en: 'Analysis Parameters' },
  'diff.group1': { zh: '比较组 1 (Treatment)', en: 'Comparison Group 1 (Treatment)' },
  'diff.group2': { zh: '比较组 2 (Control)', en: 'Comparison Group 2 (Control)' },
  'diff.logfc': { zh: '|log2FC| 阈值', en: '|log2FC| Threshold' },
  'diff.pval': { zh: 'P-value 阈值', en: 'P-value Threshold' },
  'diff.fdr': { zh: 'FDR / Adjusted P-value 阈值', en: 'FDR / Adjusted P-value Threshold' },
  'diff.advanced': { zh: '高级设置', en: 'Advanced Settings' },
  'diff.log2': { zh: '进行 log2 转换', en: 'Perform log2 transformation' },
  'diff.filter_low': { zh: '过滤低表达基因', en: 'Filter low-expression genes' },
  'diff.method': { zh: '检验方法', en: 'Test Method' },
  'diff.run': { zh: '运行分析', en: 'Run Analysis' },
  'diff.placeholder': { zh: '设置参数后点击"运行分析"开始差异分析。', en: 'Set parameters and click "Run Analysis" to start differential analysis.' },
  'diff.result_title': { zh: '差异分析结果', en: 'Differential Analysis Results' },
  'diff.total_genes': { zh: '检测基因总数', en: 'Total Genes Tested' },
  'diff.up': { zh: '上调', en: 'Up-regulated' },
  'diff.down': { zh: '下调', en: 'Down-regulated' },
  'diff.sig': { zh: '显著差异 (FDR<', en: 'Total Significant (FDR<' },
  'diff.top_genes': { zh: 'Top 差异表达基因', en: 'Top Differentially Expressed Genes' },
  'diff.gene': { zh: '基因', en: 'Gene' },
  'diff.direction': { zh: '方向', en: 'Direction' },
  'diff.proceed_enrich': { zh: '进入富集分析', en: 'Proceed to Enrichment' },
  'diff.generate_fig': { zh: '生成图表', en: 'Generate Figures' },
  'diff.export_csv': { zh: '导出 CSV', en: 'Export CSV' },

  // Enrichment
  'enrich.desc': { zh: '对差异基因列表进行 GO、KEGG 和 GSEA 富集分析。', en: 'Run GO, KEGG, and GSEA enrichment analysis on your differential gene lists.' },
  'enrich.params': { zh: '参数', en: 'Parameters' },
  'enrich.source': { zh: '基因列表来源', en: 'Gene List Source' },
  'enrich.source_diff': { zh: '所有差异基因', en: 'From Differential Analysis' },
  'enrich.source_up': { zh: '仅上调基因', en: 'Up-regulated Only' },
  'enrich.source_down': { zh: '仅下调基因', en: 'Down-regulated Only' },
  'enrich.source_all': { zh: '全部检测基因 (GSEA)', en: 'All Tested Genes (GSEA)' },
  'enrich.pval': { zh: 'P-value 阈值', en: 'P-value Cutoff' },
  'enrich.go_cat': { zh: 'GO 分类', en: 'GO Categories' },
  'enrich.gsea_geneset': { zh: 'GSEA 基因集', en: 'Gene Sets for GSEA' },
  'enrich.run': { zh: '运行富集分析', en: 'Run Enrichment' },
  'enrich.placeholder': { zh: '选择参数后点击"运行富集分析"开始。', en: 'Select parameters and click "Run Enrichment" to start.' },
  'enrich.result_title': { zh: '富集分析结果', en: 'Enrichment Results' },
  'enrich.terms': { zh: '个条目', en: 'terms' },

  // Visualization
  'viz.desc': { zh: '生成论文级图表。选择图表类型，调整参数，支持多种格式导出。', en: 'Generate publication-quality figures. Select a plot type, adjust parameters, and export in multiple formats.' },
  'viz.plot_type': { zh: '图表类型', en: 'Plot Type' },
  'viz.volcano': { zh: '火山图', en: 'Volcano Plot' },
  'viz.heatmap': { zh: '热图', en: 'Heatmap' },
  'viz.pca': { zh: 'PCA 图', en: 'PCA Plot' },
  'viz.correlation': { zh: '相关性热图', en: 'Correlation Heatmap' },
  'viz.go_bubble': { zh: 'GO 气泡图', en: 'GO Bubble Chart' },
  'viz.go_bar': { zh: 'GO 柱状图', en: 'GO Bar Chart' },
  'viz.kegg_bubble': { zh: 'KEGG 气泡图', en: 'KEGG Bubble Chart' },
  'viz.kegg_bar': { zh: 'KEGG 柱状图', en: 'KEGG Bar Chart' },
  'viz.gsea_curve': { zh: 'GSEA 曲线', en: 'GSEA Curve' },
  'viz.top_genes': { zh: 'Top DEG 柱状图', en: 'Top DEG Barplot' },
  'viz.boxplot': { zh: '关键基因箱线图', en: 'Key Gene Boxplot' },
  'viz.violin': { zh: '关键基因小提琴图', en: 'Key Gene Violin' },
  'viz.deg_stats': { zh: 'DEG 统计图', en: 'DEG Statistics' },
  'viz.title': { zh: '标题', en: 'Title' },
  'viz.xlabel': { zh: 'X 轴标签', en: 'X-axis Label' },
  'viz.ylabel': { zh: 'Y 轴标签', en: 'Y-axis Label' },
  'viz.font_size': { zh: '字体大小', en: 'Font Size' },
  'viz.width': { zh: '宽度 (inch)', en: 'Width (in)' },
  'viz.height': { zh: '高度 (inch)', en: 'Height (in)' },
  'viz.up_color': { zh: '上调颜色', en: 'Up Color' },
  'viz.down_color': { zh: '下调颜色', en: 'Down Color' },
  'viz.more_options': { zh: '更多选项', en: 'More Options' },
  'viz.show_labels': { zh: '显示基因标签', en: 'Show Gene Labels' },
  'viz.show_legend': { zh: '显示图例', en: 'Show Legend' },
  'viz.show_logfc': { zh: '显示 |log2FC| 阈值线', en: 'Show |log2FC| Threshold Line' },
  'viz.top_n': { zh: '显示 Top N 基因', en: 'Show Top N Genes' },
  'viz.generate': { zh: '生成图表', en: 'Generate Plot' },
  'viz.generating': { zh: '正在生成图表...', en: 'Generating plot...' },
  'viz.placeholder': { zh: '选择参数后点击"生成图表"。', en: 'Select parameters and click "Generate Plot".' },

  // Interpretation
  'interp.desc': { zh: '基于差异分析和富集分析结果，使用 AI 生成结果解读。选择研究方向获取上下文解释。', en: 'Generate AI-powered result interpretation based on your differential and enrichment analysis results. Select a research focus area for contextual explanation.' },
  'interp.focus': { zh: '研究方向', en: 'Research Focus' },
  'interp.auto': { zh: '自动检测', en: 'Auto-detect' },
  'interp.lang': { zh: '输出语言', en: 'Output Language' },
  'interp.generate': { zh: '生成解读', en: 'Generate Interpretation' },
  'interp.placeholder': { zh: '选择研究方向后点击"生成解读"获取 AI 结果解释。', en: 'Select a research focus and click "Generate Interpretation" to get AI-powered result explanation.' },
  'interp.generating': { zh: '正在使用 DeepSeek AI 分析结果...', en: 'Analyzing results with DeepSeek AI...' },
  'interp.summary': { zh: '摘要', en: 'Summary' },
  'interp.results': { zh: '结果描述', en: 'Results' },
  'interp.figure_legend': { zh: '图注', en: 'Figure Legends' },
  'interp.discussion': { zh: '讨论', en: 'Discussion' },
  'interp.verification': { zh: '推荐验证', en: 'Recommended Validation' },
  'interp.key_findings': { zh: '关键发现', en: 'Key Findings' },

  // Storyline
  'storyline.desc': { zh: 'AI 驱动机制假说生成。基于差异基因和富集通路，系统推荐 3-5 个潜在研究方向及实验验证建议。', en: 'AI-powered mechanism hypothesis generation. Based on your differential genes and enriched pathways, the system recommends 3-5 potential research directions with experimental validation suggestions.' },
  'storyline.title': { zh: '故事线生成', en: 'Storyline Generation' },
  'storyline.desc2': { zh: '系统分析您的 DEGs 和通路，提出含支持证据、推荐 Figure 和验证实验的机制假说。', en: 'The system analyzes your DEGs and pathways to propose mechanistic hypotheses with supporting evidence, recommended figures, and validation experiments.' },
  'storyline.count': { zh: '故事线数量', en: 'Number of Storylines' },
  'storyline.generate': { zh: '生成故事线', en: 'Generate Storylines' },
  'storyline.direction': { zh: '方向', en: 'Direction' },
  'storyline.score': { zh: '评分', en: 'Score' },
  'storyline.hypothesis': { zh: '核心假说', en: 'Core Hypothesis' },
  'storyline.key_genes': { zh: '关键基因', en: 'Key Genes' },
  'storyline.key_pathways': { zh: '关键通路', en: 'Key Pathways' },
  'storyline.validation': { zh: '推荐验证', en: 'Recommended Validation' },
  'storyline.figures': { zh: '推荐 Figure', en: 'Suggested Figures' },
  'storyline.title_field': { zh: '可能标题', en: 'Possible Title' },

  // Report Export
  'report.desc': { zh: '导出完整分析包，包括 Excel 表格、论文级图表、Word 报告和 PPT 演示文稿。', en: 'Export a complete analysis package including Excel tables, publication-quality figures, Word report, and PPT presentation.' },
  'report.word': { zh: 'Word 报告', en: 'Word Report' },
  'report.word_desc': { zh: '包含数据概览、QC、差异分析、富集分析、图表、结果解读和方法学的完整报告。', en: 'Comprehensive analysis report with data summary, QC, differential results, enrichment, figures, interpretation, and methods.' },
  'report.excel': { zh: 'Excel 结果', en: 'Excel Results' },
  'report.excel_desc': { zh: '多 sheet Excel 工作簿，包含所有分析结果表。', en: 'All analysis result tables in a multi-sheet Excel workbook.' },
  'report.ppt': { zh: 'PPT 演示', en: 'PPT Presentation' },
  'report.ppt_desc': { zh: '6-10 页幻灯片，适用于组会、基金申请或会议汇报。', en: '6-10 slide presentation for lab meeting, grant application, or conference.' },
  'report.all': { zh: '完整包', en: 'Full Package' },
  'report.all_desc': { zh: '导出全部：Excel 表格、所有图片、Word 报告、PPT、参数记录和分析日志。', en: 'Export everything: Excel tables, all figures, Word report, PPT, parameters, and analysis log.' },
  'report.export_btn': { zh: '导出', en: 'Export' },
  'report.complete': { zh: '导出完成', en: 'Export Complete' },

  // scRNA
  'scrna.title': { zh: 'scRNA-seq 分析 — 即将推出', en: 'scRNA-seq Analysis — Coming Soon' },
  'scrna.desc': { zh: '单细胞 RNA 测序分析模块正在开发中。计划功能包括:', en: 'Single-cell RNA sequencing analysis module is under development. Planned features include:' },

  // Research foci
  'focus.inflammation': { zh: 'Inflammation / 炎症', en: 'Inflammation' },
  'focus.oxidative_stress': { zh: 'Oxidative Stress / 氧化应激', en: 'Oxidative Stress' },
  'focus.metabolic_reprogramming': { zh: 'Metabolic Reprogramming / 代谢重编程', en: 'Metabolic Reprogramming' },
  'focus.macrophage_polarization': { zh: 'Macrophage Polarization / 巨噬细胞极化', en: 'Macrophage Polarization' },
  'focus.bone_remodeling': { zh: 'Bone Remodeling / 骨改建', en: 'Bone Remodeling' },
  'focus.tumor_immunity': { zh: 'Tumor Immunity / 肿瘤免疫', en: 'Tumor Immunity' },
  'focus.mitochondrial': { zh: 'Mitochondrial Function / 线粒体功能', en: 'Mitochondrial Function' },
  'focus.cell_death': { zh: 'Cell Death / 细胞死亡', en: 'Cell Death' },
  'focus.immune_regulation': { zh: 'Immune Regulation / 免疫调控', en: 'Immune Regulation' },
  'focus.cell_proliferation': { zh: 'Cell Proliferation / 细胞增殖', en: 'Cell Proliferation' },
  'focus.cell_migration': { zh: 'Cell Migration / 细胞迁移', en: 'Cell Migration' },
  'focus.lipid_metabolism': { zh: 'Lipid Metabolism / 脂质代谢', en: 'Lipid Metabolism' },
  'focus.glycolysis': { zh: 'Glycolysis / 糖酵解', en: 'Glycolysis' },
  'focus.oxphos': { zh: 'Oxidative Phosphorylation / 氧化磷酸化', en: 'Oxidative Phosphorylation' },

  // Language options
  'lang.zh': { zh: '中文', en: 'Chinese' },
  'lang.en': { zh: 'English', en: 'English' },

  // Steps
  'step.data_import': { zh: '数据导入', en: 'Data Import' },
  'step.qc': { zh: '质量检查', en: 'Quality Control' },
  'step.differential': { zh: '差异分析', en: 'Differential' },
  'step.enrichment': { zh: '富集分析', en: 'Enrichment' },
  'step.visualization': { zh: '可视化', en: 'Visualization' },
  'step.interpretation': { zh: '结果解读', en: 'Interpretation' },
  'step.storyline': { zh: '故事线', en: 'Storyline' },
  'step.report': { zh: '报告导出', en: 'Report Export' },
};
