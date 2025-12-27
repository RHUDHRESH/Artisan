"""
Database Models for Campaigns and Moves
"""
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List, Dict, Any

Base = declarative_base()


class CampaignStatus(PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MoveStatus(PyEnum):
    PROPOSED = "proposed"
    REFINED = "refined"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISCARDED = "discarded"
    FAILED = "failed"


class TaskStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Campaign(Base):
    """
    Campaign model - first-class entity for organizing moves
    """
    __tablename__ = "campaigns"
    
    id = Column(String, primary_key=True)
    workspace_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    objective = Column(Text, nullable=False)
    arc_data = Column(JSON)  # 90-day campaign arc data
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)
    target_icp = Column(Text)  # Target Ideal Customer Profile
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String)  # User who created the campaign
    completed_at = Column(DateTime(timezone=True))
    
    # Campaign metrics
    total_moves = Column(Integer, default=0)
    completed_moves = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Relationships
    moves = relationship("Move", back_populates="campaign", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Campaign(id={self.id}, title={self.title}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "title": self.title,
            "objective": self.objective,
            "arc_data": self.arc_data,
            "status": self.status.value,
            "target_icp": self.target_icp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_moves": self.total_moves,
            "completed_moves": self.completed_moves,
            "success_rate": self.success_rate
        }


class Move(Base):
    """
    Move model - actionable items within campaigns
    """
    __tablename__ = "moves"
    
    id = Column(String, primary_key=True)
    workspace_id = Column(String, nullable=False, index=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True, index=True)  # Nullable for standalone moves
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(MoveStatus), default=MoveStatus.PROPOSED, nullable=False)
    
    # Council-generated data
    confidence = Column(Float, default=0.0)
    tool_requirements = Column(JSON, default=list)
    muse_prompt = Column(Text)  # Generated prompt for execution
    success_prediction = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    reasoning_chain_id = Column(String)  # Link to reasoning chains table
    
    # Refinement data
    refinement_data = Column(JSON)  # Additional refinement information
    assets = Column(JSON, default=list)  # Associated assets
    
    # RAG status
    rag = Column(JSON)  # RAG analysis results
    
    # Dates
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String)
    proposed_by = Column(String)  # Council node that proposed this move
    
    # Ordering
    order_index = Column(Integer, default=0)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="moves")
    tasks = relationship("Task", back_populates="move", cascade="all, delete-orphan")
    daily_metrics = relationship("DailyMetrics", back_populates="move", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Move(id={self.id}, name={self.name}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "campaign_id": self.campaign_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "confidence": self.confidence,
            "tool_requirements": self.tool_requirements,
            "muse_prompt": self.muse_prompt,
            "success_prediction": self.success_prediction,
            "risk_score": self.risk_score,
            "reasoning_chain_id": self.reasoning_chain_id,
            "refinement_data": self.refinement_data,
            "assets": self.assets,
            "rag": self.rag,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "proposed_by": self.proposed_by,
            "order_index": self.order_index,
            "tasks": [task.to_dict() for task in self.tasks] if self.tasks else [],
            "daily_metrics": [metric.to_dict() for metric in self.daily_metrics] if self.daily_metrics else []
        }


class Task(Base):
    """
    Task model - individual tasks within moves
    """
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)
    move_id = Column(String, ForeignKey("moves.id"), nullable=False, index=True)
    label = Column(String, nullable=False)
    instructions = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    
    # Task details
    due_date = Column(DateTime(timezone=True))
    estimated_minutes = Column(Integer)
    proposed_by = Column(String)
    assigned_to = Column(String)
    
    # Completion data
    completed_at = Column(DateTime(timezone=True))
    completion_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Ordering
    order_index = Column(Integer, default=0)
    
    # Relationships
    move = relationship("Move", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(id={self.id}, label={self.label}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "move_id": self.move_id,
            "label": self.label,
            "instructions": self.instructions,
            "status": self.status.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "estimated_minutes": self.estimated_minutes,
            "proposed_by": self.proposed_by,
            "assigned_to": self.assigned_to,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "completion_notes": self.completion_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "order_index": self.order_index
        }


class DailyMetrics(Base):
    """
    Daily metrics for moves
    """
    __tablename__ = "daily_metrics"
    
    id = Column(String, primary_key=True)
    move_id = Column(String, ForeignKey("moves.id"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Metrics
    leads = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    calls = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    
    # Additional metrics
    conversion_rate = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    move = relationship("Move", back_populates="daily_metrics")
    
    def __repr__(self):
        return f"<DailyMetrics(id={self.id}, move_id={self.move_id}, date={self.date})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "move_id": self.move_id,
            "date": self.date.isoformat() if self.date else None,
            "leads": self.leads,
            "replies": self.replies,
            "calls": self.calls,
            "confidence": self.confidence,
            "conversion_rate": self.conversion_rate,
            "engagement_score": self.engagement_score,
            "revenue": self.revenue,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ReasoningChain(Base):
    """
    Reasoning chains for council deliberations
    """
    __tablename__ = "reasoning_chains"
    
    id = Column(String, primary_key=True)
    workspace_id = Column(String, nullable=False, index=True)
    move_id = Column(String, ForeignKey("moves.id"), nullable=True, index=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True, index=True)
    
    # Reasoning data
    debate_history = Column(JSON, nullable=False)
    consensus_metrics = Column(JSON)
    synthesis = Column(Text)
    decree = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ReasoningChain(id={self.id}, workspace_id={self.workspace_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "move_id": self.move_id,
            "campaign_id": self.campaign_id,
            "debate_history": self.debate_history,
            "consensus_metrics": self.consensus_metrics,
            "synthesis": self.synthesis,
            "decree": self.decree,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Notification(Base):
    """
    Notification model for user notifications
    """
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True)
    workspace_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    
    # Notification content
    type = Column(String, nullable=False)  # info, success, warning, error
    channel = Column(String, nullable=False)  # in_app, email, push, sms
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Status
    read = Column(Boolean, default=False, nullable=False)
    sent = Column(Boolean, default=False, nullable=False)
    
    # Data
    data = Column(JSON)  # Additional notification data
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    read_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, title={self.title})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "type": self.type,
            "channel": self.channel,
            "title": self.title,
            "message": self.message,
            "read": self.read,
            "sent": self.sent,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None
        }


# Radar-related models
class Signal(Base):
    """
    Radar signal model for market intelligence
    """
    __tablename__ = "signals"
    
    id = Column(String, primary_key=True)
    workspace_id = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    
    # Signal data
    type = Column(String, nullable=False)  # competitor, market, trend, opportunity
    source = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    strength = Column(String, nullable=False)  # high, medium, low
    freshness = Column(String, nullable=False)  # fresh, recent, stale
    
    # Analysis
    action_suggestion = Column(Text)
    evidence_count = Column(Integer, default=0)
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Signal(id={self.id}, type={self.type}, strength={self.strength})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "tenant_id": self.tenant_id,
            "type": self.type,
            "source": self.source,
            "content": self.content,
            "confidence": self.confidence,
            "strength": self.strength,
            "freshness": self.freshness,
            "action_suggestion": self.action_suggestion,
            "evidence_count": self.evidence_count,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Dossier(Base):
    """
    Dossier model for signal analysis summaries
    """
    __tablename__ = "dossiers"
    
    id = Column(String, primary_key=True)
    workspace_id = Column(String, nullable=False, index=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True, index=True)
    
    # Dossier content
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    hypotheses = Column(JSON, default=list)
    experiments = Column(JSON, default=list)
    copy_snippets = Column(JSON, default=list)
    market_narrative = Column(Text)
    
    # Associated signals
    signal_ids = Column(JSON, default=list)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Dossier(id={self.id}, title={self.title})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "campaign_id": self.campaign_id,
            "title": self.title,
            "summary": self.summary,
            "hypotheses": self.hypotheses,
            "experiments": self.experiments,
            "copy_snippets": self.copy_snippets,
            "market_narrative": self.market_narrative,
            "signal_ids": self.signal_ids,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
