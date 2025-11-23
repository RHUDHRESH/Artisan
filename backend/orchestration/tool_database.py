"""
Tool Database - Centralized registry for all agent tools
Stores tool definitions, usage metrics, and metadata
"""
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, Column, String, Integer, JSON, DateTime, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from loguru import logger
import json

Base = declarative_base()


class Tool(Base):
    """Tool definition stored in database"""
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)

    # Tool metadata
    parameters_schema = Column(JSON, nullable=False)  # JSON schema for parameters
    return_schema = Column(JSON, nullable=True)  # Expected return type
    implementation = Column(String(500), nullable=False)  # Module path to implementation

    # Usage metrics
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_execution_time = Column(Float, default=0.0)

    # Metadata
    tags = Column(JSON, default=list)  # Tags for discovery
    version = Column(String(50), default="1.0.0")
    author = Column(String(255), nullable=True)
    requires_auth = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class AgentToolUsage(Base):
    """Track which agents use which tools"""
    __tablename__ = "agent_tool_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(255), nullable=False, index=True)
    tool_id = Column(Integer, nullable=False, index=True)

    # Usage stats
    execution_count = Column(Integer, default=0)
    last_execution = Column(DateTime, nullable=True)
    success_rate = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)


class ToolExecution(Base):
    """Log of tool executions for analytics"""
    __tablename__ = "tool_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_id = Column(Integer, nullable=False, index=True)
    agent_id = Column(String(255), nullable=False, index=True)

    # Execution details
    input_params = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    execution_time = Column(Float, nullable=False)  # seconds
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)

    # Context
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)

    executed_at = Column(DateTime, default=datetime.utcnow, index=True)


class ToolDatabaseManager:
    """Manager for tool database operations"""

    def __init__(self, database_url: str = "sqlite:///./data/tools.db"):
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"✅ Tool database initialized: {database_url}")

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def register_tool(
        self,
        name: str,
        description: str,
        category: str,
        parameters_schema: Dict,
        implementation: str,
        **kwargs
    ) -> Tool:
        """Register a new tool"""
        session = self.get_session()
        try:
            # Check if tool exists
            existing_tool = session.query(Tool).filter(Tool.name == name).first()
            if existing_tool:
                logger.warning(f"Tool {name} already exists, updating...")
                existing_tool.description = description
                existing_tool.category = category
                existing_tool.parameters_schema = parameters_schema
                existing_tool.implementation = implementation
                for key, value in kwargs.items():
                    setattr(existing_tool, key, value)
                session.commit()
                return existing_tool

            tool = Tool(
                name=name,
                description=description,
                category=category,
                parameters_schema=parameters_schema,
                implementation=implementation,
                **kwargs
            )
            session.add(tool)
            session.commit()
            session.refresh(tool)
            logger.info(f"✅ Registered tool: {name}")
            return tool
        finally:
            session.close()

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        session = self.get_session()
        try:
            return session.query(Tool).filter(Tool.name == name).first()
        finally:
            session.close()

    def get_tools_by_category(self, category: str) -> List[Tool]:
        """Get all tools in a category"""
        session = self.get_session()
        try:
            return session.query(Tool).filter(Tool.category == category, Tool.is_enabled == True).all()
        finally:
            session.close()

    def search_tools(self, query: str, limit: int = 10) -> List[Tool]:
        """Search tools by name, description, or tags"""
        session = self.get_session()
        try:
            return session.query(Tool).filter(
                (Tool.name.contains(query)) |
                (Tool.description.contains(query)) |
                (Tool.tags.contains(query))
            ).filter(Tool.is_enabled == True).limit(limit).all()
        finally:
            session.close()

    def get_all_tools(self, enabled_only: bool = True) -> List[Tool]:
        """Get all tools"""
        session = self.get_session()
        try:
            query = session.query(Tool)
            if enabled_only:
                query = query.filter(Tool.is_enabled == True)
            return query.all()
        finally:
            session.close()

    def log_tool_execution(
        self,
        tool_name: str,
        agent_id: str,
        execution_time: float,
        success: bool,
        input_params: Optional[Dict] = None,
        output_data: Optional[Any] = None,
        error_message: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Log tool execution for analytics"""
        session = self.get_session()
        try:
            tool = session.query(Tool).filter(Tool.name == tool_name).first()
            if not tool:
                logger.warning(f"Tool {tool_name} not found for logging")
                return

            # Create execution log
            execution = ToolExecution(
                tool_id=tool.id,
                agent_id=agent_id,
                input_params=input_params,
                output_data=output_data if isinstance(output_data, dict) else {"result": str(output_data)},
                execution_time=execution_time,
                success=success,
                error_message=error_message,
                user_id=user_id,
                session_id=session_id
            )
            session.add(execution)

            # Update tool metrics
            tool.usage_count += 1
            if success:
                tool.success_count += 1
            else:
                tool.failure_count += 1

            # Update average execution time
            tool.avg_execution_time = (
                (tool.avg_execution_time * (tool.usage_count - 1) + execution_time) / tool.usage_count
            )
            tool.last_used_at = datetime.utcnow()

            session.commit()
        finally:
            session.close()

    def get_tool_analytics(self, tool_name: str) -> Dict:
        """Get analytics for a specific tool"""
        session = self.get_session()
        try:
            tool = session.query(Tool).filter(Tool.name == tool_name).first()
            if not tool:
                return {}

            recent_executions = session.query(ToolExecution).filter(
                ToolExecution.tool_id == tool.id
            ).order_by(ToolExecution.executed_at.desc()).limit(100).all()

            return {
                "name": tool.name,
                "category": tool.category,
                "total_usage": tool.usage_count,
                "success_count": tool.success_count,
                "failure_count": tool.failure_count,
                "success_rate": tool.success_count / max(tool.usage_count, 1),
                "avg_execution_time": tool.avg_execution_time,
                "last_used": tool.last_used_at.isoformat() if tool.last_used_at else None,
                "recent_executions": len(recent_executions),
            }
        finally:
            session.close()

    def get_most_used_tools(self, limit: int = 10) -> List[Dict]:
        """Get most frequently used tools"""
        session = self.get_session()
        try:
            tools = session.query(Tool).filter(
                Tool.is_enabled == True
            ).order_by(Tool.usage_count.desc()).limit(limit).all()

            return [{
                "name": t.name,
                "category": t.category,
                "usage_count": t.usage_count,
                "success_rate": t.success_count / max(t.usage_count, 1),
            } for t in tools]
        finally:
            session.close()


# Global tool database instance
_tool_db: Optional[ToolDatabaseManager] = None


def get_tool_database(database_url: str = "sqlite:///./data/tools.db") -> ToolDatabaseManager:
    """Get or create tool database instance"""
    global _tool_db
    if _tool_db is None:
        _tool_db = ToolDatabaseManager(database_url)
    return _tool_db
