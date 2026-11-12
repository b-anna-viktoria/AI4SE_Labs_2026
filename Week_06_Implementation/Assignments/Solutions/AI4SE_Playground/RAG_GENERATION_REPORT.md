# RAG code generation report

## Run summary

- **Model:** `gpt-6-luna`
- **Tasks loaded:** 10 from `missing_code.json`
- **Retrieval:** Top 5 chunks per task using the repository's sparse TF-IDF embeddings and cosine similarity.
- **Methods inserted:** 5 of 10
- **Tests:** 447 passed; 26 failed; 8 errored (481 total)

## Code generation results

| Target method | Result |
|---|---|
| `OrderStatus.is_terminal` | Inserted |
| `InventoryLedger.__contains__` | Not inserted; generated implementation did not pass Python syntax validation |
| `Warehouse.stock_report` | Inserted |
| `OrderStateMachine.transition` | Not inserted; generated implementation did not pass Python syntax validation |
| `OrderLog.by_status` | Not inserted; generated implementation did not pass Python syntax validation |
| `Customer.can_afford` | Not inserted; generated implementation did not pass indentation validation |
| `Order.__len__` | Inserted |
| `BulkDiscountPricing.price` | Not inserted; generated implementation did not pass Python syntax validation |
| `EventBus.__contains__` | Inserted |
| `Money.__bool__` | Inserted |

Rejected implementations were not written to their target files.

## Unit test results

The suite was rerun after code generation. These tests passed:

| Test module | Passed |
|---|---:|
| `test_base` | 23 |
| `test_decorators` | 18 |
| `test_enums` | 15 |
| `test_events` | 24 |
| `test_exceptions` | 15 |
| `test_inventory` | 68 |
| `test_models` | 98 |
| `test_orders` | 51 |
| `test_package` | 6 |
| `test_pricing` | 26 |
| `test_repository` | 24 |
| `test_simulation` | 37 |
| `test_util` | 42 |
| **Total passed** | **447** |

The following tests did not pass. Names are listed without error messages or
tracebacks:

### Failed assertions (26)

- `test_inventory.InventoryLedgerContainsLenIterTests.test_contains_normalized_present`
- `test_inventory.InventoryLedgerContainsLenIterTests.test_contains_present_even_if_zero_on_hand_after_commit`
- `test_models.CustomerTests.test_can_afford_non_money_rejected`
- `test_models.CustomerTests.test_can_afford_true_within_limit`
- `test_orders.OrderAddItemTests.test_add_after_advance_rejected`
- `test_orders.OrderAdvanceTests.test_advance_from_terminal_raises`
- `test_orders.OrderAdvanceTests.test_advance_to_same_status_raises`
- `test_orders.OrderAdvanceTests.test_cancel_from_new`
- `test_orders.OrderAdvanceTests.test_cancel_from_reserved`
- `test_orders.OrderAdvanceTests.test_happy_path_to_shipped`
- `test_orders.OrderAdvanceTests.test_illegal_advance_raises_and_keeps_status`
- `test_orders.OrderStateMachineTests.test_call_is_alias_for_transition`
- `test_orders.OrderStateMachineTests.test_transition_illegal_raises`
- `test_orders.OrderStateMachineTests.test_transition_returns_target_when_legal`
- `test_orders.OrderTotalTests.test_total_reflects_merged_quantities_for_bulk_discount`
- `test_pricing.BulkDiscountPriceTests.test_at_threshold_applies_discount`
- `test_pricing.BulkDiscountPriceTests.test_below_threshold_returns_base_total`
- `test_pricing.BulkDiscountPriceTests.test_discount_uses_floor_division`
- `test_pricing.BulkDiscountPriceTests.test_empty_items_below_threshold`
- `test_pricing.BulkDiscountPriceTests.test_full_discount_yields_zero`
- `test_pricing.BulkDiscountPriceTests.test_quantity_summed_across_lines`
- `test_pricing.BulkDiscountPriceTests.test_wraps_base_with_tax`
- `test_pricing.BulkDiscountPriceTests.test_zero_percent_returns_base_even_above_threshold`
- `test_simulation.SimulationStepTests.test_cancel_path_releases_reservation`
- `test_simulation.SimulationStepTests.test_shipped_path_publishes_and_adds_revenue`
- `test_simulation.SimulationStepTests.test_step_returns_order_and_accounts_for_it`

### Tests that errored (8)

- `test_models.CustomerTests.test_can_afford_accounts_for_existing_balance`
- `test_models.CustomerTests.test_charge_exactly_to_limit_allowed`
- `test_models.CustomerTests.test_charge_increases_balance`
- `test_models.CustomerTests.test_charge_non_money_propagates_type_error`
- `test_orders.OrderEqualityTests.test_repr_includes_status`
- `test_orders.OrderLogTests.test_by_status_filters`
- `test_orders.OrderLogTests.test_by_status_is_lazy_generator`
- `test_simulation.SimulationStepTests.test_same_seed_is_reproducible`

