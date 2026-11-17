# ML system (Stage 3, milestone: trained 22 Jan)

Undecided. Before writing code, pin down in `docs/decisions/`:

- **Role**: what the ML does that the physics baseline can't (e.g. residual correction on top of the
  baseline, a fast surrogate for scenario/Monte Carlo runs, or demand forecasting for control).
  "ML for its own sake" will be hard to defend under the PR methodology criterion.
- **Data budget**: one year of hourly data is about 8.7k points with strong seasonality, so keep
  models small and validate on a held-out time block.
- **Benchmark**: it must beat the physics baseline on the same test split to earn its place.
