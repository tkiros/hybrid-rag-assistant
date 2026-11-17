# Tuning experiments: dev split only

Generated 2026-11-17 11:57 UTC by `python -m evals.tune`. Do not edit by hand.

33 answerable dev questions. Each cell is hit@5 / MRR@10.

| Variant | exact_id (n=13) | paraphrased (n=13) | multi_chunk (n=7) | all (n=33) |
|---|---|---|---|---|
| bm25 | 1.000 / 0.923 | 0.308 / 0.195 | 1.000 / 0.929 | 0.727 / 0.637 |
| vector | 0.385 / 0.378 | 0.692 / 0.564 | 0.714 / 0.385 | 0.576 / 0.453 |
| vector + BGE prefix | 0.462 / 0.439 | 0.692 / 0.654 | 0.857 / 0.469 | 0.636 / 0.530 |
| hybrid, top 5 of each | 1.000 / 0.949 | 0.615 / 0.455 | 1.000 / 0.821 | 0.848 / 0.727 |
| hybrid, top 10 of each | 1.000 / 0.853 | 0.615 / 0.417 | 1.000 / 0.814 | 0.848 / 0.673 |
| hybrid, top 20 of each | 0.923 / 0.857 | 0.692 / 0.531 | 1.000 / 0.814 | 0.848 / 0.719 |
| hybrid, top 40 of each | 0.923 / 0.749 | 0.462 / 0.500 | 0.857 / 0.689 | 0.727 / 0.638 |
| hybrid, top 10 of each + BGE prefix | 1.000 / 0.865 | 0.692 / 0.387 | 1.000 / 0.790 | 0.879 / 0.661 |
| hybrid, top 20 of each + BGE prefix | 0.923 / 0.843 | 0.692 / 0.458 | 1.000 / 0.790 | 0.848 / 0.680 |
