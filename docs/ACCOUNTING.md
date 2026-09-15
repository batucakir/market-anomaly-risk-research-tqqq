# Accounting Conventions

Performance values are only comparable when calendar, mark price, execution price, transaction-cost treatment, and terminal liquidation or rebalance treatment match.

The official V16 comparison uses close-to-close lifecycle prices, additive transaction costs, and a terminal rebalance cost. The official corrected V8 comparator was reconstructed under the same convention. The original V8 research freeze used open-based marks and multiplicative transaction costs, so it remains a separate archived result.

The official V16 event path ends at `4.3667136990` before the terminal rebalance. Applying the final cost produces the published `4.3657796007`. Charts in this repository include that final cost so their endpoint matches the headline table.

Event-mark maximum drawdown is calculated from the event wealth series. It is not the same as maximum drawdown from a daily marked-to-market series.
