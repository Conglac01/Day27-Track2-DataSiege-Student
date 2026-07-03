# Reflection

## Hardest Faults
The hardest faults to detect were the **subtle-tier faults** in the `ai_infra` (feature drift, embedding staleness) and `checks` (distribution shifts) pillars. Their magnitudes were deliberately set close to normal statistical variance, meaning any simple static threshold tight enough to catch them would trigger a deluge of false positives on clean data. 

To overcome this without sacrificing our FPR, we implemented a combined sum-of-squares anomaly score (a simplified Mahalanobis distance). By squaring and summing the Z-scores across all relevant metrics for an event (e.g., `row_count`, `null_rate`, `mean_amount`, and `staleness_min` for `data_batch`), we were able to flag events that exhibited moderate, concurrent deviations across multiple signals, even if no single metric crossed the explicit 3σ threshold.

## Cost/Coverage Tradeoff
Our strategy favored **complete single-pass coverage**. By routing each event strictly to its corresponding, specific metered tool (and maintaining state locally via `ctx.state` to avoid redundant external checks like tracking missing lineage upstreams), our total cost profile was highly deterministic. 

For the private phase, our cost ledger came out to exactly 300 credits against a budget of 320, yielding an overage penalty of 0.0. Because the scoring formula heavily penalizes TPR drops (a 1-fault miss typically costs more points than the penalty incurred by exceeding the budget by a single metered call), skipping checks was mathematically suboptimal. If the budget had been drastically tighter, we would have adjusted our coverage by completely ignoring `feature_drift` on highly stable event sources, but under the current cost structure, full coverage yielded the maximal score.
