"""
Council Blackboard State - Shared state management for council deliberations
"""
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class MoveStatus(str, Enum):
    PROPOSED = "proposed"
    REFINED = "refined"
    APPROVED = "approved"
    DISCARDED = "discarded"


class CouncilNode(BaseModel):
    """Represents a council node/agent"""
    name: str
    role: str
    expertise: List[str]
    confidence: float = 0.0
    reasoning: str = ""


class CouncilMove(BaseModel):
    """Represents a proposed move/action"""
    id: str
    name: str
    description: str
    status: MoveStatus = MoveStatus.PROPOSED
    confidence: float = 0.0
    tool_requirements: List[str] = []
    muse_prompt: Optional[str] = None
    success_prediction: float = 0.0
    risk_score: float = 0.0
    proposed_by: str
    supported_by: List[str] = []
    critiqued_by: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)


class DebateRound(BaseModel):
    """Represents a single debate round"""
    round_number: int
    topic: str
    participants: List[str]
    arguments: Dict[str, str] = {}
    consensus_score: float = 0.0
    outcome: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class CouncilMetrics(BaseModel):
    """Council consensus and performance metrics"""
    consensus_alignment: float
    debate_quality: float
    decision_confidence: float
    participation_rate: float
    expert_agreement: float


class CouncilBlackboardState(TypedDict):
    """Shared blackboard state for council deliberations"""
    # Core inputs
    workspace_id: str
    objective: str
    details: Dict[str, Any]
    target_icp: Optional[str]  # For campaign plans
    
    # Council configuration
    council_nodes: List[CouncilNode]
    current_round: int
    max_rounds: int
    
    # Deliberation state
    debate_history: List[DebateRound]
    proposed_moves: List[CouncilMove]
    refined_moves: List[CouncilMove]
    approved_moves: List[CouncilMove]
    discarded_moves: List[CouncilMove]
    
    # Consensus and metrics
    consensus_metrics: Optional[CouncilMetrics]
    decree: Optional[str]  # Final council decision
    reasoning_chain_id: Optional[str]
    
    # Campaign specific (for campaign plans)
    campaign_arc: Optional[Dict[str, Any]]
    
    # Metadata
    started_at: datetime
    completed_at: Optional[datetime]
    errors: List[str]
    kill_switch_triggered: bool


class CouncilBlackboard:
    """
    Blackboard pattern implementation for council state management
    """
    
    def __init__(self, workspace_id: str, objective: str, details: Dict[str, Any], target_icp: Optional[str] = None):
        self.state: CouncilBlackboardState = {
            "workspace_id": workspace_id,
            "objective": objective,
            "details": details,
            "target_icp": target_icp,
            
            "council_nodes": [],
            "current_round": 0,
            "max_rounds": 5,
            
            "debate_history": [],
            "proposed_moves": [],
            "refined_moves": [],
            "approved_moves": [],
            "discarded_moves": [],
            
            "consensus_metrics": None,
            "decree": None,
            "reasoning_chain_id": None,
            
            "campaign_arc": None,
            
            "started_at": datetime.now(),
            "completed_at": None,
            "errors": [],
            "kill_switch_triggered": False
        }
        
    def add_council_node(self, node: CouncilNode):
        """Add a council node"""
        self.state["council_nodes"].append(node)
        
    def add_debate_round(self, round_data: DebateRound):
        """Add a debate round to history"""
        self.state["debate_history"].append(round_data)
        self.state["current_round"] = round_data.round_number
        
    def propose_move(self, move: CouncilMove):
        """Add a proposed move"""
        self.state["proposed_moves"].append(move)
        
    def refine_move(self, move: CouncilMove):
        """Add a refined move"""
        self.state["refined_moves"].append(move)
        
    def approve_move(self, move: CouncilMove):
        """Add an approved move"""
        self.state["approved_moves"].append(move)
        
    def discard_move(self, move: CouncilMove):
        """Add a discarded move"""
        self.state["discarded_moves"].append(move)
        
    def set_consensus_metrics(self, metrics: CouncilMetrics):
        """Set consensus metrics"""
        self.state["consensus_metrics"] = metrics
        
    def set_decree(self, decree: str):
        """Set final council decree"""
        self.state["decree"] = decree
        
    def trigger_kill_switch(self, reason: str):
        """Trigger emergency stop"""
        self.state["kill_switch_triggered"] = True
        self.state["errors"].append(f"Kill switch triggered: {reason}")
        
    def add_error(self, error: str):
        """Add an error to the state"""
        self.state["errors"].append(error)
        
    def complete(self):
        """Mark the council session as complete"""
        self.state["completed_at"] = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for JSON serialization"""
        return {
            "workspace_id": self.state["workspace_id"],
            "objective": self.state["objective"],
            "details": self.state["details"],
            "target_icp": self.state["target_icp"],
            
            "council_nodes": [node.dict() for node in self.state["council_nodes"]],
            "current_round": self.state["current_round"],
            "max_rounds": self.state["max_rounds"],
            
            "debate_history": [round.dict() for round in self.state["debate_history"]],
            "proposed_moves": [move.dict() for move in self.state["proposed_moves"]],
            "refined_moves": [move.dict() for move in self.state["refined_moves"]],
            "approved_moves": [move.dict() for move in self.state["approved_moves"]],
            "discarded_moves": [move.dict() for move in self.state["discarded_moves"]],
            
            "consensus_metrics": self.state["consensus_metrics"].dict() if self.state["consensus_metrics"] else None,
            "decree": self.state["decree"],
            "reasoning_chain_id": self.state["reasoning_chain_id"],
            
            "campaign_arc": self.state["campaign_arc"],
            
            "started_at": self.state["started_at"].isoformat(),
            "completed_at": self.state["completed_at"].isoformat() if self.state["completed_at"] else None,
            "errors": self.state["errors"],
            "kill_switch_triggered": self.state["kill_switch_triggered"]
        }
