from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from hashlib import sha256
import json, math
from typing import Iterable

PROTOCOL = "TRISTAN-ANTI-EGO-COURT-R1"

def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False, default=str).encode("utf-8")
def digest(value: object) -> str:
    return sha256(_canonical(value)).hexdigest()
def _finite(value: float, name: str) -> float:
    value=float(value)
    if not math.isfinite(value): raise ValueError(f"{name} must be finite")
    return value

@dataclass(frozen=True)
class Submission:
    candidate_id:str
    origin:str
    family:str
    value:float=0.0
    evidence:float=0.0
    uncertainty_reduction:float=0.0
    future_work_destroyed:float=0.0
    proof_reuse:float=0.0
    complexity:float=0.0
    latency:float=0.0
    monetary_cost:float=0.0
    maintenance_cost:float=0.0
    irreversibility:float=0.0
    blast_radius:float=0.0
    authority_risk:float=0.0
    reversible:bool=True
    blocked:bool=False
    tags:tuple[str,...]=()
    def __post_init__(self):
        if not self.candidate_id.strip(): raise ValueError("candidate_id required")
        if not self.origin.strip(): raise ValueError("origin required")
        for n in ("value","evidence","uncertainty_reduction","future_work_destroyed","proof_reuse","complexity","latency","monetary_cost","maintenance_cost","irreversibility","blast_radius","authority_risk"): _finite(getattr(self,n),n)
    @property
    def blind_token(self)->str:
        return digest({
            "family":self.family,"value":self.value,"evidence":self.evidence,
            "uncertainty_reduction":self.uncertainty_reduction,
            "future_work_destroyed":self.future_work_destroyed,
            "proof_reuse":self.proof_reuse,"complexity":self.complexity,
            "latency":self.latency,"monetary_cost":self.monetary_cost,
            "maintenance_cost":self.maintenance_cost,
            "irreversibility":self.irreversibility,"blast_radius":self.blast_radius,
            "authority_risk":self.authority_risk,"reversible":self.reversible,
            "blocked":self.blocked,"tags":self.tags
        })[:24]

@dataclass(frozen=True)
class CourtPolicy:
    value_weight:float=1.0
    evidence_weight:float=.9
    uncertainty_weight:float=.8
    future_work_weight:float=1.2
    proof_reuse_weight:float=.8
    complexity_weight:float=.9
    latency_weight:float=.2
    monetary_weight:float=1.0
    maintenance_weight:float=.8
    irreversibility_weight:float=1.4
    blast_radius_weight:float=.6
    authority_risk_weight:float=2.0
    evidence_floor:float=0.0
    max_authority_risk:float=0.0

@dataclass(frozen=True)
class BlindEvaluation:
    blind_token:str
    eligible:bool
    score:float
    reasons:tuple[str,...]

@dataclass(frozen=True)
class BlindDecision:
    protocol:str
    selected_blind_token:str
    evaluations:tuple[BlindEvaluation,...]
    status:str
    receipt_digest:str=""
    def with_digest(self):
        return replace(self,receipt_digest=digest(asdict(replace(self,receipt_digest=""))))

@dataclass(frozen=True)
class RevealedDecision:
    protocol:str
    candidate_id:str
    origin:str
    family:str
    blind_token:str
    status:str
    blind_receipt_digest:str

def score(sub:Submission,policy:CourtPolicy=CourtPolicy())->float:
    benefit=(policy.value_weight*sub.value+policy.evidence_weight*sub.evidence+
             policy.uncertainty_weight*sub.uncertainty_reduction+
             policy.future_work_weight*sub.future_work_destroyed+
             policy.proof_reuse_weight*sub.proof_reuse)
    burden=(policy.complexity_weight*sub.complexity+policy.latency_weight*sub.latency+
            policy.monetary_weight*sub.monetary_cost+policy.maintenance_weight*sub.maintenance_cost+
            policy.irreversibility_weight*sub.irreversibility+policy.blast_radius_weight*sub.blast_radius+
            policy.authority_risk_weight*sub.authority_risk)
    return benefit-burden

def evaluate(sub:Submission,policy:CourtPolicy=CourtPolicy())->BlindEvaluation:
    reasons=[]
    if sub.blocked: reasons.append("BLOCKED")
    if sub.evidence<policy.evidence_floor: reasons.append("EVIDENCE_FLOOR")
    if sub.authority_risk>policy.max_authority_risk: reasons.append("AUTHORITY_RISK")
    eligible=not reasons
    return BlindEvaluation(sub.blind_token,eligible,score(sub,policy) if eligible else float("-inf"),tuple(reasons))

def no_action()->Submission:
    return Submission("NO_ACTION","BASELINE","NO_ACTION",evidence=1.0,reversible=True)

def blind_court(submissions:Iterable[Submission],policy:CourtPolicy=CourtPolicy())->BlindDecision:
    pool=list(submissions)
    if not any(s.family=="NO_ACTION" or s.candidate_id=="NO_ACTION" for s in pool): pool.append(no_action())
    evaluations=tuple(evaluate(s,policy) for s in pool)
    eligible=[e for e in evaluations if e.eligible]
    if not eligible:
        selected=evaluate(no_action(),policy); status="NO_ELIGIBLE_ACTION"
    else:
        selected=max(eligible,key=lambda e:(e.score,e.blind_token))
        status="NO_ACTION_WINS" if selected.blind_token==no_action().blind_token else "CANDIDATE_WINS"
    return BlindDecision(PROTOCOL,selected.blind_token,evaluations,status).with_digest()

def reveal(decision:BlindDecision,submissions:Iterable[Submission])->RevealedDecision:
    pool=list(submissions)+[no_action()]
    matches=[s for s in pool if s.blind_token==decision.selected_blind_token]
    if len(matches)!=1: raise ValueError("blind token must reveal to exactly one candidate")
    s=matches[0]
    return RevealedDecision(PROTOCOL,s.candidate_id,s.origin,s.family,s.blind_token,decision.status,decision.receipt_digest)

@dataclass(frozen=True)
class VitalityHistory:
    candidate_id:str
    uses:int
    wins:int
    verified_wins:int
    unique_regimes_won:int
    dominated_runs:int
    unique_value:float
    maintenance_cost:float
    regenerable:bool

def right_to_die(history:VitalityHistory,dominated_threshold:int=3)->str:
    if history.regenerable and history.uses==0 and history.unique_value<=0: return "HIBERNATE_OR_DELETE"
    if history.dominated_runs>=dominated_threshold and history.unique_value<=0 and history.maintenance_cost>0: return "RIGHT_TO_DIE"
    if history.verified_wins==0 and history.uses>0 and history.maintenance_cost>history.unique_value: return "RIGHT_TO_DIE"
    return "RETAIN"

def ablation_value(full_score:float,ablated_score:float,removal_savings:float=0.0)->float:
    return _finite(ablated_score,"ablated_score")-_finite(full_score,"full_score")+_finite(removal_savings,"removal_savings")
