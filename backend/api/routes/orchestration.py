"""
Orchestration API - Multi-agent coordination endpoints
Manages agent creation, execution, and monitoring
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from loguru import logger

from backend.orchestration.agent_factory import (
    get_agent_factory,
    AgentSpec,
    AgentRole,
    AgentCapability,
    AgentLibrary
)
from backend.orchestration.graph_orchestrator import (
    get_graph_orchestrator,
    get_hierarchical_orchestrator
)
from backend.orchestration.tool_database import get_tool_database
from backend.orchestration.agent_memory import get_memory_manager
from backend.core.llm_provider import LLMManager, LLMProvider
from backend.config import settings

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


# Request/Response Models

class CreateAgentRequest(BaseModel):
    """Request to create a new agent"""
    name: str
    role: AgentRole
    capabilities: List[AgentCapability]
    description: str
    tools: List[str] = Field(default_factory=list)
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7


class ExecuteWorkflowRequest(BaseModel):
    """Request to execute a workflow"""
    task: str
    agents: List[str]  # List of agent names to use
    context: Dict[str, Any] = Field(default_factory=dict)
    max_iterations: int = 10
    use_supervisor: bool = True


class RegisterToolRequest(BaseModel):
    """Request to register a new tool"""
    name: str
    description: str
    category: str
    parameters_schema: Dict
    implementation: str  # Module path
    tags: List[str] = Field(default_factory=list)


# Endpoints

@router.post("/agents/create")
async def create_agent(request: CreateAgentRequest):
    """Create a new specialized agent"""
    try:
        factory = get_agent_factory()

        spec = AgentSpec(
            name=request.name,
            role=request.role,
            capabilities=request.capabilities,
            description=request.description,
            tools=request.tools,
            model=request.model,
            temperature=request.temperature
        )

        # Create LLM manager
        async with LLMManager(
            primary_provider=LLMProvider(settings.llm_provider),
            groq_api_key=settings.groq_api_key,
            openrouter_api_key=settings.openrouter_api_key,
            gemini_api_key=settings.gemini_api_key,
        ) as llm_manager:
            agent = factory.create_agent(spec, llm_manager)

        return {
            "success": True,
            "agent_name": request.name,
            "message": f"Agent {request.name} created successfully"
        }

    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/templates")
async def list_agent_templates():
    """List all available agent templates"""
    factory = get_agent_factory()
    templates = factory.list_available_templates()

    # Add all library agents
    library_agents = [
        attr for attr in dir(AgentLibrary)
        if not attr.startswith('_') and attr.isupper()
    ]

    return {
        "templates": templates,
        "library_agents": library_agents,
        "total_count": len(templates) + len(library_agents)
    }


@router.get("/agents/list")
async def list_agents():
    """List all created agents"""
    factory = get_agent_factory()
    agents = factory.get_all_agents()

    return {
        "agents": list(agents.keys()),
        "count": len(agents)
    }


@router.post("/workflow/execute")
async def execute_workflow(request: ExecuteWorkflowRequest, background_tasks: BackgroundTasks):
    """Execute a multi-agent workflow"""
    try:
        # Create LLM manager
        async with LLMManager(
            primary_provider=LLMProvider(settings.llm_provider),
            groq_api_key=settings.groq_api_key,
            openrouter_api_key=settings.openrouter_api_key,
            gemini_api_key=settings.gemini_api_key,
        ) as llm_manager:

            if request.use_supervisor:
                # Use LangGraph orchestrator with supervisor
                orchestrator = get_graph_orchestrator(llm_manager)

                # Build agent functions (simplified for demo)
                agent_funcs = {}
                for agent_name in request.agents:
                    async def agent_func(task: str, context: Dict, name=agent_name):
                        # Placeholder - would call actual agent
                        return f"{name} processed: {task}"

                    agent_funcs[agent_name] = agent_func

                # Build and execute graph
                orchestrator.build_graph("supervisor", agent_funcs)
                result = await orchestrator.execute_workflow(
                    task=request.task,
                    context=request.context,
                    max_iterations=request.max_iterations
                )

            else:
                # Sequential execution without supervisor
                results = {}
                for agent_name in request.agents:
                    # Execute each agent sequentially
                    results[agent_name] = f"Processed by {agent_name}"

                result = {
                    "success": True,
                    "results": results,
                    "errors": [],
                    "iterations": len(request.agents)
                }

        return result

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/register")
async def register_tool(request: RegisterToolRequest):
    """Register a new tool in the database"""
    try:
        tool_db = get_tool_database()

        tool = tool_db.register_tool(
            name=request.name,
            description=request.description,
            category=request.category,
            parameters_schema=request.parameters_schema,
            implementation=request.implementation,
            tags=request.tags
        )

        return {
            "success": True,
            "tool_id": tool.id,
            "tool_name": tool.name,
            "message": f"Tool {request.name} registered successfully"
        }

    except Exception as e:
        logger.error(f"Failed to register tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/list")
async def list_tools(category: Optional[str] = None):
    """List all available tools"""
    try:
        tool_db = get_tool_database()

        if category:
            tools = tool_db.get_tools_by_category(category)
        else:
            tools = tool_db.get_all_tools()

        return {
            "tools": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "usage_count": t.usage_count,
                    "success_rate": t.success_count / max(t.usage_count, 1)
                }
                for t in tools
            ],
            "count": len(tools)
        }

    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/{tool_name}/analytics")
async def get_tool_analytics(tool_name: str):
    """Get analytics for a specific tool"""
    try:
        tool_db = get_tool_database()
        analytics = tool_db.get_tool_analytics(tool_name)

        if not analytics:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/top")
async def get_top_tools(limit: int = 10):
    """Get most used tools"""
    try:
        tool_db = get_tool_database()
        top_tools = tool_db.get_most_used_tools(limit)

        return {
            "top_tools": top_tools,
            "count": len(top_tools)
        }

    except Exception as e:
        logger.error(f"Failed to get top tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{agent_id}/stats")
async def get_memory_stats(agent_id: str):
    """Get memory statistics for an agent"""
    try:
        memory_manager = await get_memory_manager()
        stats = await memory_manager.get_memory_stats(agent_id)

        return stats

    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{agent_id}/clear")
async def clear_agent_memory(
    agent_id: str,
    memory_type: Optional[str] = None
):
    """Clear memory for an agent"""
    try:
        memory_manager = await get_memory_manager()
        await memory_manager.clear_agent_memory(agent_id, memory_type)

        return {
            "success": True,
            "message": f"Memory cleared for agent {agent_id}"
        }

    except Exception as e:
        logger.error(f"Failed to clear memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hierarchy/create")
async def create_hierarchy(
    departments: Dict[str, List[str]],  # dept_name -> list of worker agent names
):
    """Create hierarchical organization"""
    try:
        async with LLMManager(
            primary_provider=LLMProvider(settings.llm_provider),
            groq_api_key=settings.groq_api_key,
            openrouter_api_key=settings.openrouter_api_key,
            gemini_api_key=settings.gemini_api_key,
        ) as llm_manager:

            hierarchy = get_hierarchical_orchestrator(llm_manager)

            for dept_name, worker_names in departments.items():
                # Create placeholder worker functions
                workers = {}
                for worker_name in worker_names:
                    async def worker_func(task: str, context: Dict, name=worker_name):
                        return f"{name} completed: {task}"
                    workers[worker_name] = worker_func

                hierarchy.create_department(dept_name, workers)

            hierarchy.create_master_supervisor()

            org_chart = hierarchy.get_organization_chart()

            return {
                "success": True,
                "organization": org_chart,
                "message": "Hierarchical organization created"
            }

    except Exception as e:
        logger.error(f"Failed to create hierarchy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def list_capabilities():
    """List all available agent capabilities"""
    return {
        "capabilities": [c.value for c in AgentCapability],
        "roles": [r.value for r in AgentRole],
        "count": {
            "capabilities": len(AgentCapability),
            "roles": len(AgentRole)
        }
    }


@router.get("/health")
async def orchestration_health():
    """Health check for orchestration system"""
    try:
        tool_db = get_tool_database()
        memory_manager = await get_memory_manager()

        # Check Redis
        try:
            redis_healthy = memory_manager.redis_client is not None
            if redis_healthy:
                await memory_manager.redis_client.ping()
        except:
            redis_healthy = False

        return {
            "status": "healthy",
            "components": {
                "tool_database": "healthy",
                "agent_factory": "healthy",
                "memory_manager": "healthy" if redis_healthy else "degraded",
                "redis": "connected" if redis_healthy else "disconnected"
            },
            "statistics": {
                "total_tools": len(tool_db.get_all_tools()),
                "agent_templates": len(get_agent_factory().list_available_templates())
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
