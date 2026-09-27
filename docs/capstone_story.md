# Day 20 — Titanic Survival Capstone Story

## Headline

### Survival outcomes were highly uneven across passenger segments.

The Phase-1 cleaned Titanic dataset contains 782 passenger records.
The executive dashboard uses interactive filters to show how observed
survival changes by passenger class, sex and port of embarkation.

## Story 1 — Start with the overall outcome

The dashboard begins with the filtered survival rate and number of
passengers represented by the current selection.

This establishes the baseline before moving into subgroup comparisons.

## Story 2 — Passenger class matters

Survival rates differ materially across passenger classes.

Class-level comparison is therefore an important first drill-down when
trying to identify where the weakest outcomes occurred.

## Story 3 — Sex reveals a much larger separation

Female and male passengers show a large difference in observed survival
rates.

This is one of the strongest patterns identified during Phase 1 and was
also formally tested in Day 16.

## Story 4 — The strongest view is class × sex

Looking at class and sex together identifies specific passenger segments
rather than treating all members of a class or sex group as identical.

The dashboard dynamically highlights the weakest observed class × sex
segment under the current filter combination.

## Story 5 — Use the filters to challenge the story

The dashboard allows users to filter by:

- Passenger class
- Sex
- Port of embarkation

The purpose of the filters is not interactivity for its own sake. They
allow the user to test whether the headline pattern changes for a more
specific passenger population.

## Decision Focus

The dashboard should be used to identify the segments with the weakest
observed outcomes and quantify the gap versus stronger segments.

The evidence is descriptive and observational. It should therefore be
used for analytical understanding rather than interpreted as proof that
sex, class or embarkation caused the observed survival differences.

## Source

`data/titanic_cleaned.csv`

## Metric Definition

Survival Rate = mean of the binary `survived` field.

## Freshness

The dashboard reports the source file's last modification timestamp
directly from the local dataset.