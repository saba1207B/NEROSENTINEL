from threading import RLock
from uuid import UUID

from aquasentinel.schemas import ScenarioCreate, ScenarioRecord, ScenarioResult


class DemoStore:
    """Thread-safe demo repository. Production deployments use SQL repositories."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.scenarios: dict[UUID, ScenarioRecord] = {}
        self.results: dict[UUID, ScenarioResult] = {}
        self.alerts: dict[str, dict] = {}
        self.audit_events: list[dict] = []
        self.idempotency: dict[tuple[str, str], tuple[UUID, dict]] = {}
        self.ingestions: dict[str, dict] = {}
        self.optimizations: dict[UUID, dict] = {}
        self.reports: dict[UUID, dict] = {}
        self.proposals: dict[UUID, dict] = {}

    def add_scenario(self, record: ScenarioRecord) -> ScenarioRecord:
        with self._lock:
            self.scenarios[record.id] = record
        return record

    def create_scenario(self, payload: ScenarioCreate, actor: str, key: str | None) -> tuple[ScenarioRecord, bool]:
        with self._lock:
            if key:
                existing = self.idempotency.get((actor, key))
                if existing:
                    scenario_id, original = existing
                    if original != payload.model_dump(mode="json"):
                        raise ValueError("idempotency key reused with different scenario parameters")
                    return self.scenarios[scenario_id], False
            record = ScenarioRecord(**payload.model_dump())
            self.scenarios[record.id] = record
            if key:
                self.idempotency[(actor, key)] = (record.id, payload.model_dump(mode="json"))
            return record, True

    def save_result(self, scenario_id: UUID, result: ScenarioResult) -> ScenarioResult:
        with self._lock:
            result.scenario_id = scenario_id
            self.results[scenario_id] = result
            self.scenarios[scenario_id].status = "completed"
        return result

    def audit(self, actor: str, action: str, target: str) -> None:
        with self._lock:
            self.audit_events.append({"actor": actor, "action": action, "target": target})


store = DemoStore()
