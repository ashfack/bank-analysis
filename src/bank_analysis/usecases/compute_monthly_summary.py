from typing import Sequence
from ..domain.reporting import summary
from ..domain.value_objects import MonthlySummary
from ..domain.entities import Transaction
from ..ports.cycle_grouper import CycleGrouper


class ComputeMonthlySummaryUseCase:
    def __init__(self,
                 cycle_grouper: CycleGrouper
    ):
        self.cycle_grouper = cycle_grouper

    def execute(self,
        txns: Sequence[Transaction]
    ) -> list[MonthlySummary]:
      return summary.compute_monthly_summary_core(txns,
                                                  cycle_grouper=self.cycle_grouper)

