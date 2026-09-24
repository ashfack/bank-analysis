import pytest
import pandas as pd
import math
from model.models import Transaction, BudgetDomain, StrategyConfig
from orchestrator import Orchestrator
from config.config import BudgetStrategy, ANCHOR_CATEGORY

class TestOrchestratorCoverage:

    @pytest.fixture
    def multi_cycle_domain(self):
        """
        Creates logically consistent data:
        - 'Food' is isolated in its own cluster and overridden (Level 1).
        - 'Restaurant' & 'Bar' share a cluster and a total cap (Level 2).
        """
        transactions = [
            # Cycle 1: January
            Transaction(pd.Timestamp('2026-01-01'), "SALAIRE", 3000.0, ANCHOR_CATEGORY),
            Transaction(pd.Timestamp('2026-01-05'), "AUCHAN", -100.0, "Food"),
            Transaction(pd.Timestamp('2026-01-10'), "MCDO", -50.0, "Restaurant"),
            Transaction(pd.Timestamp('2026-01-15'), "PUB", -20.0, "Bar"),
            
            # Cycle 2: February
            Transaction(pd.Timestamp('2026-02-01'), "SALAIRE", 3000.0, ANCHOR_CATEGORY),
            Transaction(pd.Timestamp('2026-02-05'), "AUCHAN", -200.0, "Food"),
            Transaction(pd.Timestamp('2026-02-10'), "KFC", -30.0, "Restaurant"),
            Transaction(pd.Timestamp('2026-02-15'), "BAR", -40.0, "Bar")
        ]
        
        mapping = {
            ANCHOR_CATEGORY: "0. Incoming",
            "Food": "1. Groceries",      # Isolated Cluster
            "Restaurant": "2. Leisure",   # Shared Cluster
            "Bar": "2. Leisure"           # Shared Cluster
        }
        
        # Overrides:
        # 1. Hard-limit Food to 150 (Level 1)
        # 2. Cap the entire '2. Leisure' cluster (McDo + Bars) at 200 (Level 2)
        overrides = {
            "Food": "150", 
            "2. Leisure": "200"
        }
        
        return BudgetDomain(transactions, mapping, overrides)

    def test_level_1_category_override(self, multi_cycle_domain):
        """Tests that a specific category override is respected when isolated."""
        orch = Orchestrator(multi_cycle_domain)
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        
        food = next(r for r in results if r.category == "Food")
        # Even if median is 150, we verify the logic actually applied the string '150'
        assert food.theoretical_budget == 150.0

    def test_level_2_cluster_cap_distribution(self, multi_cycle_domain):
        """Tests that a Cluster Cap is distributed proportionally among its members."""
        orch = Orchestrator(multi_cycle_domain)
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        
        leisure_items = [r for r in results if r.master_cluster == "2. Leisure"]
        total_budget = sum(r.theoretical_budget for r in leisure_items)
        
        # The sum of budgets for Restaurant and Bar should equal the cluster cap of 200
        assert pytest.approx(total_budget) == 200.0

    def test_symbolic_cluster_override(self):
        """Tests applying a symbolic rule (e.g., +10%) to an entire cluster."""
        t_salary = Transaction(pd.Timestamp('2026-01-01'), "SALAIRE", 3000.0, ANCHOR_CATEGORY)
        t_rent = Transaction(pd.Timestamp('2026-01-05'), "RENT", -1000.0, "Home")
        
        domain = BudgetDomain(
            [t_salary, t_rent], 
            {"Home": "1. Fixed", ANCHOR_CATEGORY: "0. Incoming"}, 
            {"1. Fixed": "+10%"}
        )
        
        orch = Orchestrator(domain)
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        
        home = next(r for r in results if r.category == "Home")
        # Base limit 1000 + 10% = 1100
        assert home.theoretical_budget == 1100.0

    def test_initial_cycle_assignment(self):
        """Tests transactions occurring before any anchor date (Salary)."""
        transactions = [
            Transaction(pd.Timestamp('2025-12-28'), "EARLY_BUY", -50.0, "Misc"),
            Transaction(pd.Timestamp('2026-01-01'), "SALAIRE", 3000.0, ANCHOR_CATEGORY)
        ]
        domain = BudgetDomain(transactions, {"Misc": "Other", ANCHOR_CATEGORY: "In"}, {})
        orch = Orchestrator(domain)
        
        early_buy = next(item for item in orch.reporting_data if item['label'] == "EARLY_BUY")
        assert early_buy['cycle'] == "Initial"

    def test_zero_median_cluster_distribution(self):
        """Tests fallback distribution when cluster members have 0 historical spending."""
        transactions = [
            Transaction(pd.Timestamp('2026-01-01'), "SALAIRE", 3000.0, ANCHOR_CATEGORY),
            Transaction(pd.Timestamp('2026-01-05'), "GIFT", 0.0, "Gifts")
        ]
        domain = BudgetDomain(
            transactions, 
            {"Gifts": "Presents", ANCHOR_CATEGORY: "In"}, 
            {"Presents": "100"}
        )
        orch = Orchestrator(domain)
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        
        gift = next(r for r in results if r.category == "Gifts")
        # Total cap 100 / 1 member = 100
        assert gift.theoretical_budget == 100.0

    def test_orchestrator_infers_unmapped_categories(self):
        """Ensures unknown categories are classified correctly using signed amounts."""
        t = Transaction(
            dateOperation=pd.Timestamp('2026-01-01'),
            label="NEW_STARTUP_SUBSCRIPTION",
            amount=-15.0,
            category="Software_Unknown"
        )
        
        domain = BudgetDomain([t], {ANCHOR_CATEGORY: "0. Incoming"}, {})
        orch = Orchestrator(domain)
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        
        res = next(r for r in results if r.category == "Software_Unknown")
        # Should NOT be Incoming because amount is -15.0
        assert res.master_cluster != "0. Incoming"

    def test_frequency_with_initial_cycle(self):
        """Acknowledges that 'Initial' is a valid cycle count."""
        t = Transaction(pd.Timestamp('2026-01-01'), "CASH", -10.0, "Misc")
        domain = BudgetDomain([t], {"Misc": "Other"}, {})
        orch = Orchestrator(domain)
        
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        # It's 1.0 because 'Initial' exists as a cycle
        assert results[0].frequency == 1.0

    def test_cluster_numeric_cap_branch(self):
        """Hits: _update_cluster AND the numeric branch of _calculate_distribution."""
        t1 = Transaction(pd.Timestamp('2026-01-01'), "A", -50.0, "Cat1")
        # Overriding a cluster 'Clus' with a number '100'
        domain = BudgetDomain([t1], {"Cat1": "Clus"}, {"Clus": "100"})
        orch = Orchestrator(domain)
        
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        assert results[0].theoretical_budget == 100.0

    def test_cluster_symbolic_rule_branch(self):
        """Hits: the 'else' (symbolic) branch of _calculate_distribution."""
        t1 = Transaction(pd.Timestamp('2026-01-01'), "A", -100.0, "Cat1")
        # Overriding a cluster 'Clus' with a string '+10%'
        domain = BudgetDomain([t1], {"Cat1": "Clus"}, {"Clus": "+10%"})
        orch = Orchestrator(domain)
        
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        assert results[0].theoretical_budget == 110.0

    def test_non_existent_cluster_override_guard(self):
        """Hits: the 'if not members: return results' guard in _update_cluster."""
        t1 = Transaction(pd.Timestamp('2026-01-01'), "A", -100.0, "Cat1")
        # Override for 'Ghost' which exists in overrides but NO category belongs to it
        domain = BudgetDomain([t1], {"Cat1": "Real"}, {"Ghost": "500"})
        orch = Orchestrator(domain)
        
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        # Should finish without error and ignore 'Ghost'
        assert len(results) == 1

    def test_empty_cycles_frequency_fallback(self):
        """Hits: the 'else 0.0' fallback in _calculate_stats."""
        # This requires total_cycles to be 0
        # We can simulate this by having an empty transaction list if Orchestrator allows
        domain = BudgetDomain([], {}, {})
        orch = Orchestrator(domain)
        # We call the private math method directly to force the 0.0 branch
        freq = orch._calculate_stats([10.0, 20.0], total_cycles=0).frequency
        assert freq == 0.0

    def test_coverage_shadows(self, multi_cycle_domain):
        """Forces the Orchestrator into defensive fallback paths."""
        orch = Orchestrator(multi_cycle_domain)

        # 1. Force the 'else 0.0' frequency fallback in _calculate_stats
        # We call the private method directly to hit the division-by-zero guard
        stats = orch._calculate_stats([100.0, 200.0], total_cycles=0)
        assert stats.frequency == 0.0

        # 2. Force the 'if not members' guard in _update_cluster
        # We try to update a cluster that exists in overrides but has NO categories
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        updated = orch._update_cluster(results, "NonExistentCluster", "500")
        assert updated == results  # Should return immediately without changing anything

        # 3. Force the 'm_sum > 0' else branch in _calculate_distribution
        # This happens when a cluster cap is set but all items in it have 0.0 median
        from model.models import ProcessedCategory
        zero_item = ProcessedCategory(
            "ZeroCat", "ZeroClus", 0.0, 0.0, 1, 1.0, 0.0, 0.0, 0.0
        )
        dist = orch._calculate_distribution([zero_item], "100")
        # Should distribute the 100 equally because m_sum is 0
        assert dist == [100.0]

    def test_symbolic_cluster_distribution_path(self):
        """Hits the 'else' branch of _calculate_distribution (Symbolic rules)."""
        t = Transaction(pd.Timestamp('2026-01-01'), "RENT", -1000.0, "Home")
        domain = BudgetDomain([t], {"Home": "Fixed"}, {"Fixed": "+10%"})
        orch = Orchestrator(domain)
        
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        # This ensures the 'else' branch for SymbolicOverride.apply is hit at cluster level
        assert results[0].theoretical_budget == 1100.0
    def test_coverage_final_push(self):
        """Kills the last 9% of missing lines in Orchestrator."""
        t1 = Transaction(pd.Timestamp('2026-01-01'), "A", -10.0, "Cat1")
        domain = BudgetDomain([t1], {"Cat1": "Real"}, {"Ghost": "500"})
        orch = Orchestrator(domain)
        
        # 1. Hit the 'if not members' guard in _update_cluster
        # We call it with 'Ghost', which is in overrides but has no members
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        assert len(results) == 1

        # 2. Hit the 'm_sum > 0' else branch in _calculate_distribution
        # Create a mock cluster where all medians are 0.0
        from model.models import ProcessedCategory
        zero_member = ProcessedCategory(
            "Zero", "Ghost", 0.0, 0.0, 1, 1.0, 0.0, 0.0, 0.0
        )
        # This forces the (float(rule) / len(members)) path
        dist = orch._calculate_distribution([zero_member], "100")
        assert dist == [100.0]

        # 3. Hit the 'total_cycles else 0.0' fallback in _calculate_stats
        stats = orch._calculate_stats([10.0], total_cycles=0)
        assert stats.frequency == 0.0

    def test_kill_final_seven_lines(self):
        """Surgical strike to reach 100% coverage."""
        # Setup: One category with 0 spending
        t_zero = Transaction(pd.Timestamp('2026-01-01'), "ZERO", 0.0, "ZeroCat")
        # Override for a Ghost cluster (hits 'if not members')
        # Override for a real cluster with a number (hits 'm_sum > 0' else)
        # Override for a real cluster with symbolic (hits 'else' symbolic branch)
        domain = BudgetDomain(
            [t_zero], 
            {"ZeroCat": "RealCluster"}, 
            {"Ghost": "500", "RealCluster": "100", "OtherClus": "+10%"}
        )
        orch = Orchestrator(domain)

        # 1. Trigger: total_cycles = 0 fallback
        # We call the internal method directly because run_pipeline always has >= 1 cycle
        stats = orch._calculate_stats([10.0], total_cycles=0)
        assert stats.frequency == 0.0

        # 2. Trigger: The cluster overrides logic
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        
        # Verify the zero-sum distribution (hits the numeric 'else' branch)
        zero_cat = next(r for r in results if r.category == "ZeroCat")
        assert zero_cat.theoretical_budget == 100.0

    def test_symbolic_cluster_path(self):
        """Explicitly hit the symbolic branch in distribution."""
        t1 = Transaction(pd.Timestamp('2026-01-01'), "A", -100.0, "Cat1")
        domain = BudgetDomain([t1], {"Cat1": "Clus"}, {"Clus": "+10%"})
        orch = Orchestrator(domain)
        
        results = orch.run_pipeline(BudgetStrategy.HYBRID_VOLATILITY, StrategyConfig())
        assert results[0].theoretical_budget == 110.0
