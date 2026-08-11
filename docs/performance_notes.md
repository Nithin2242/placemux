## Performance — Before Optimization (Day 13)

Measured with filters: Passenger class [2, 3], Sex [male], Port [southampton, cherbourg] (338 of 782 passengers shown).

| Step | Time (ms) |
|---|---|
| Data load | 0.97 |
| Filtering | 4.83 |
| Chart 1 (class) | 84.34 |
| Chart 2 (sex) | 49.55 |
| Chart 3 (port) | 86.10 |
| **Total** | **~225.8** |

**Finding:** Data load and filtering are already near-instant at this data 
size. The real bottleneck (96%+ of total time) is matplotlib chart rendering, 
not data processing — meaning optimization effort should target chart 
rendering, not query/aggregation logic.