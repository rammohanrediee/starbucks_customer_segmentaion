# Dataset record

## Source

The order-level CSV was downloaded from the following Kaggle dataset:

- Dataset: [Starbucks Customer Ordering Patterns](https://www.kaggle.com/datasets/likithagedipudi/starbucks-customer-ordering-patterns)
- Creator: Likitha Gedipudi (`likithagedipudi`)
- Kaggle reference: `likithagedipudi/starbucks-customer-ordering-patterns`
- Version: 1, initial release
- License: [CC0 1.0 Public Domain](https://creativecommons.org/publicdomain/zero/1.0/)
- Kaggle description: simulated customer ordering patterns across 100,000
  transactions covering 2024–2025
- Retrieved by the project author from Kaggle

Kaggle reports version 1 as 13,492,973 bytes, which matches the raw CSV in this
repository exactly. The SHA-256 below provides a stronger integrity check for
the local copy.

This is simulated data published by an independent Kaggle contributor. It is
not official Starbucks customer data, and this project is not affiliated with
or endorsed by Starbucks.

## Files and integrity

| File | Purpose | Rows | SHA-256 |
| --- | --- | ---: | --- |
| `starbucks_customer_ordering_patterns.csv` | Order-level input | 100,000 | `a63088f7e1663927fdd52df7a70ef9e2093bda7e06de17f0dd33f95ef4ef0247` |
| `customer_segments_output.csv` | Derived customer features and segment labels | 14,988 | `adf2be03e8c45335fd760188e50e0b9bca48cec9746ee8dca3a65ad06e978013` |

Run `python -m scripts.validate_dataset` to verify the raw file's schema,
identifier uniqueness, date parsing, and numeric ranges.

## Limitations

- The dataset is explicitly described by its creator as a simulation and covers
  a fixed 2024–2025 period. Findings describe this sample, not real Starbucks
  customers or Starbucks business performance.
- Segment labels are analytical interpretations, not observed customer types.
- The customer output is derived from the raw orders and should be regenerated
  whenever the feature pipeline changes.
