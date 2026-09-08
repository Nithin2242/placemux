import logging

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules


def mine_frequent_itemsets(
    basket_matrix: pd.DataFrame,
    min_support: float,
    max_itemset_length: int,
    logger: logging.Logger,
) -> pd.DataFrame:
    logger.info(
        "Mining frequent itemsets: support >= %.4f, max length = %d.",
        min_support,
        max_itemset_length,
    )

    frequent_itemsets = apriori(
        basket_matrix,
        min_support=min_support,
        use_colnames=True,
        max_len=max_itemset_length,
    )

    if frequent_itemsets.empty:
        raise ValueError(
            "No frequent itemsets found. Lower min_support or inspect data."
        )

    frequent_itemsets["itemset_size"] = (
        frequent_itemsets["itemsets"].apply(len)
    )

    frequent_itemsets = frequent_itemsets.sort_values(
        ["itemset_size", "support"],
        ascending=[True, False],
    ).reset_index(drop=True)

    logger.info(
        "Frequent-itemset mining complete: %d itemsets.",
        len(frequent_itemsets),
    )

    return frequent_itemsets


def generate_rules(
    frequent_itemsets: pd.DataFrame,
    min_confidence: float,
    min_lift: float,
    logger: logging.Logger,
) -> pd.DataFrame:
    logger.info(
        "Generating association rules: confidence >= %.2f, lift >= %.2f.",
        min_confidence,
        min_lift,
    )

    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=min_confidence,
    )

    if rules.empty:
        raise ValueError(
            "No association rules were generated."
        )

    rules = rules[
        rules["lift"] >= min_lift
    ].copy()

    if rules.empty:
        raise ValueError(
            "No rules passed the configured lift threshold."
        )

    rules["antecedent"] = rules["antecedents"].apply(
        lambda items: ", ".join(sorted(items))
    )

    rules["consequent"] = rules["consequents"].apply(
        lambda items: ", ".join(sorted(items))
    )

    rules["support_pct"] = rules["support"] * 100
    rules["confidence_pct"] = rules["confidence"] * 100

    rules["priority_score"] = (
        rules["support"] * rules["lift"]
    )

    rules = rules.sort_values(
        ["priority_score", "lift", "support"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    logger.info(
        "Rule generation complete: %d rules passed the thresholds.",
        len(rules),
    )

    return rules


def make_business_rules(
    rules: pd.DataFrame,
    logger: logging.Logger,
    top_n: int = 10,
) -> pd.DataFrame:
    logger.info("Creating business-focused one-to-one rules.")

    business_rules = rules[
        (rules["antecedents"].apply(len) == 1)
        & (rules["consequents"].apply(len) == 1)
    ].copy()

    if business_rules.empty:
        raise ValueError(
            "No one-to-one business rules remain after filtering."
        )

    business_rules["Item_A"] = business_rules["antecedents"].apply(
        lambda items: next(iter(items))
    )

    business_rules["Item_B"] = business_rules["consequents"].apply(
        lambda items: next(iter(items))
    )

    # Treat A -> B and B -> A as the same underlying product pair.
    business_rules["pair_key"] = business_rules.apply(
        lambda row: tuple(
            sorted([row["Item_A"], row["Item_B"]])
        ),
        axis=1,
    )

    business_rules = (
        business_rules
        .sort_values(
            ["lift", "support", "confidence"],
            ascending=[False, False, False],
        )
        .drop_duplicates("pair_key")
        .copy()
    )

    business_rules["priority_score"] = (
        business_rules["support"]
        * business_rules["lift"]
    )

    business_rules = (
        business_rules
        .sort_values(
            ["priority_score", "lift", "support"],
            ascending=[False, False, False],
        )
        .reset_index(drop=True)
    )

    final_rules = business_rules.head(top_n).copy()

    final_rules["Recommendation"] = final_rules.apply(
        lambda row:
        f"Test {row['Item_B']} as a cross-sell recommendation "
        f"when a customer buys {row['Item_A']}. Consider a bundle "
        f"or paired placement if the association remains consistent.",
        axis=1,
    )

    logger.info(
        "Business-rule selection complete: %d unique one-to-one rules; "
        "reporting top %d.",
        len(business_rules),
        len(final_rules),
    )

    return final_rules