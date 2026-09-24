from typing import Dict, List, Protocol, Sequence

from auto_tuner.strategy_auto_tuner import TuningResult
from model.models import BudgetView, EnrichedTransaction, Transaction
from orchestrator import Orchestrator


class TransactionReader(Protocol):
    def read(self, source: bytes) -> List[Transaction]: ...

    def count_duplicates(self, source: bytes) -> int: ...


class MappingReader(Protocol):
    def read(self, source: bytes) -> Dict[str, str]: ...


class BudgetReader(Protocol):
    def read(self, source: bytes) -> Dict[str, str]: ...


class ReportWriter(Protocol):
    def write(
        self,
        view: BudgetView,
        transactions: Sequence[EnrichedTransaction],
    ) -> bytes: ...


class StrategyTuner(Protocol):
    def discover(self, orchestrator: Orchestrator) -> TuningResult: ...
