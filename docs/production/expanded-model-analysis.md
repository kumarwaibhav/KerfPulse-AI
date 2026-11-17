# Expanded grouped model comparison

All held-out identities, source targets and linked-workpiece splits were validated before analysis.
Cohort: 952 eligible cuts, 60 positives, 8 connected-workpiece clusters. Seeds: [17, 29, 43].

| Method | Mean AP | AP seed range | Mean Brier | Paired AP delta vs logistic, bootstrap 95% |
|---|---:|---|---:|---|
| age_only | 0.2266 | 0.2266–0.2266 | 0.0613 | [-0.388672648242279, 0.15512468833403467] |
| context | 0.1741 | 0.1741–0.1741 | 0.0594 | [-0.3901970457326392, 0.06196505087114452] |
| logistic | 0.3252 | 0.3252–0.3252 | 0.0510 | [0.0, 0.0] |
| current_no_age | 0.3381 | 0.3381–0.3381 | 0.0497 | [-0.010236776320810362, 0.06501837504600352] |
| fused | 0.3531 | 0.3531–0.3531 | 0.0487 | [-0.1641868650520747, 0.11400914751927416] |
| mlp | 0.3218 | 0.2861–0.3898 | 0.0625 | [-0.23904457220113615, 0.12209399937032624] |

Intervals are paired connected-workpiece bootstrap approximations on few clusters, conditional on fitted models. They are not independent-machine confirmation or a guarantee under domain shift. Seeds are repeated optimization runs on the same data, not independent samples. Inspection utility must be assessed separately.
