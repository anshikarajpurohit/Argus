# Synthetic model evaluation

This model is trained on synthetic data; its real-world performance is unknown.

273 training runs / 117 test runs; 40950 training windows / 17550 test windows. Split by scenario run; no overlap.

| Metric | Value |
|---|---:|
| accuracy | 0.9995 |
| precision | 1.0000 |
| recall | 0.9986 |
| F1 | 0.9993 |

Confusion matrix (rows true, columns predicted; class order 0, 1):

```
[[11124     0]
 [    9  6417]]
```

| Feature | Importance |
|---|---:|
| n_modified | 0.05229 |
| n_created | 0.00779 |
| n_deleted | 0.00587 |
| n_moved | 0.00632 |
| n_unique_files | 0.17452 |
| n_entropy_spike | 0.09836 |
| n_ext_change | 0.00891 |
| mean_entropy | 0.09144 |
| max_entropy | 0.14079 |
| n_dirs | 0.26696 |
| files_per_sec | 0.14514 |
| canary_hit | 0.00159 |

Targets: recall >= 0.95, precision >= 0.90. Met.
