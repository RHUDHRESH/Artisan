"""
LangGraph Orchestrator - Advanced multi-agent coordination
Uses LangGraph for complex agent workflows and state management
"""
from typing import Dict, List, Optional, Any, Annotated, TypedDict, Sequence
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from loguru import logger
import operator
import json


class AgentState(TypedDict):
    """State shared across all agents in the graph"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_agent: str
    task: str
    context: Dict[str, Any]
    results: Dict[str, Any]
    errors: List[str]
    iteration: int
    max_iterations: int
    next_agent: Optional[str]
    is_complete: bool


class SupervisorDecision(BaseModel):
    """Decision made by supervisor"""
    next_agent: str = Field(description="Name of the next agent to run")
    reasoning: str = Field(description="Why this agent was chosen")
    instructions: str = Field(description="Specific instructions for the agent")
    is_complete: bool = Field(default=False, description="Whether the task is complete")


class LangGraphOrchestrator:
    """
    Advanced orchestrator using LangGraph for multi-agent coordination
    Supports complex workflows, state management, and dynamic routing
    """

    def __init__(self, llm_manager: Any):
        self.llm = llm_manager
        self.graph: Optional[StateGraph] = None
        self.agents: Dict[str, Any] = {}
        self.tools: Dict[str, Any] = {}
        logger.info("🎯 LangGraph Orchestrator initialized")

    def create_supervisor(self, name: str, agents: List[str]) -> Any:
        """Create a supervisor agent that routes to sub-agents"""

        system_prompt = f"""You are {name}, a supervisor managing these agents: {', '.join(agents)}.

Your responsibilities:
1. Understand the task and break it into subtasks
2. Assign each subtask to the most appropriate agent
3. Monitor progress and handle errors
4. Synthesize results from all agents
5. Determine when the task is complete

Available agents:
{self._format_agent_descriptions(agents)}

Guidelines:
- Choose agents based on their capabilities
- Provide clear instructions to each agent
- Track progress and dependencies
- Handle failures gracefully
- Ensure all required information is gathered

Respond with a JSON object:
{{
    "next_agent": "agent_name",
    "reasoning": "why this agent is appropriate",
    "instructions": "specific task for the agent",
    "is_complete": false
}}
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "Task: {task}\n\nContext: {context}\n\nWhat should we do next?")
        ])

        supervisor_chain = prompt | self.llm

        async def supervisor_node(state: AgentState) -> AgentState:
            """Supervisor node function"""
            try:
                response = await supervisor_chain.ainvoke({
                    "messages": state["messages"],
                    "task": state["task"],
                    "context": json.dumps(state["context"], indent=2)
                })

                # Parse supervisor decision
                decision_text = response.content if hasattr(response, 'content') else str(response)

                # Try to extract JSON from response
                if "```json" in decision_text:
                    decision_text = decision_text.split("```json")[1].split("```")[0]

                decision = json.loads(decision_text)

                # Update state
                state["next_agent"] = decision.get("next_agent")
                state["is_complete"] = decision.get("is_complete", False)
                state["messages"].append(AIMessage(
                    content=f"Supervisor: {decision.get('reasoning', 'Routing to next agent')}"
                ))

                logger.info(f"📍 Supervisor routing to: {decision.get('next_agent')}")

                return state

            except Exception as e:
                logger.error(f"Supervisor error: {e}")
                state["errors"].append(str(e))
                state["is_complete"] = True
                return state

        return supervisor_node

    def create_worker_node(self, agent_name: str, agent_func: Any) -> Any:
        """Create a worker node for an agent"""

        async def worker_node(state: AgentState) -> AgentState:
            """Worker node function"""
            try:
                logger.info(f"🔧 {agent_name} starting work...")

                # Get the latest message/task
                last_message = state["messages"][-1] if state["messages"] else None
                task_description = last_message.content if last_message else state["task"]

                # Execute agent
                result = await agent_func(task_description, state["context"])

                # Store result
                state["results"][agent_name] = result
                state["current_agent"] = agent_name
                state["iteration"] += 1

                # Add result to messages
                state["messages"].append(AIMessage(
                    content=f"{agent_name}: {result}"
                ))

                logger.info(f"✅ {agent_name} completed")

                return state

            except Exception as e:
                logger.error(f"{agent_name} error: {e}")
                state["errors"].append(f"{agent_name}: {str(e)}")
                return state

        return worker_node

    def build_graph(
        self,
        supervisor_name: str,
        agents: Dict[str, Any],
        entry_point: str = "supervisor"
    ) -> StateGraph:
        """Build LangGraph workflow"""

        # Create graph
        workflow = StateGraph(AgentState)

        # Add supervisor node
        supervisor_node = self.create_supervisor(supervisor_name, list(agents.keys()))
        workflow.add_node("supervisor", supervisor_node)

        # Add worker nodes
        for agent_name, agent_func in agents.items():
            worker_node = self.create_worker_node(agent_name, agent_func)
            workflow.add_node(agent_name, worker_node)

            # Add edge from worker back to supervisor
            workflow.add_edge(agent_name, "supervisor")

        # Add conditional edges from supervisor
        def router(state: AgentState) -> str:
            """Route based on supervisor decision"""
            if state["is_complete"] or state["iteration"] >= state["max_iterations"]:
                return END

            next_agent = state.get("next_agent")
            if next_agent and next_agent in agents:
                return next_agent

            return END

        workflow.add_conditional_edges(
            "supervisor",
            router,
            {agent_name: agent_name for agent_name in agents.keys()} | {END: END}
        )

        # Set entry point
        workflow.set_entry_point(entry_point)

        self.graph = workflow.compile()
        logger.info(f"✅ Graph built with {len(agents)} agents")

        return self.graph

    async def execute_workflow(
        self,
        task: str,
        context: Optional[Dict] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """Execute the workflow"""

        if not self.graph:
            raise ValueError("Graph not built. Call build_graph() first")

        initial_state: AgentState = {
            "messages": [HumanMessage(content=task)],
            "current_agent": "supervisor",
            "task": task,
            "context": context or {},
            "results": {},
            "errors": [],
            "iteration": 0,
            "max_iterations": max_iterations,
            "next_agent": None,
            "is_complete": False
        }

        logger.info(f"🚀 Starting workflow: {task}")

        try:
            final_state = await self.graph.ainvoke(initial_state)

            return {
                "success": len(final_state["errors"]) == 0,
                "results": final_state["results"],
                "errors": final_state["errors"],
                "iterations": final_state["iteration"],
                "messages": [
                    {"role": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content}
                    for m in final_state["messages"]
                ]
            }

        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {
                "success": False,
                "results": {},
                "errors": [str(e)],
                "iterations": 0,
                "messages": []
            }

    def _format_agent_descriptions(self, agent_names: List[str]) -> str:
        """Format agent descriptions for supervisor"""
        descriptions = []
        for name in agent_names:
            # This would pull from agent registry
            descriptions.append(f"- {name}: Specialized agent for {name.replace('_', ' ')}")
        return "\n".join(descriptions)

    def visualize_graph(self, output_path: str = "workflow_graph.png"):
        """Visualize the workflow graph"""
        if not self.graph:
            logger.warning("No graph to visualize")
            return

        try:
            # This requires graphviz
            from IPython.display import Image, display
            display(Image(self.graph.get_graph().draw_mermaid_png()))
            logger.info(f"Graph visualization saved to {output_path}")
        except Exception as e:
            logger.warning(f"Could not visualize graph: {e}")


class HierarchicalOrchestrator:
    """
    Multi-level hierarchical orchestration
    Master Supervisor -> Department Supervisors -> Worker Agents
    """

    def __init__(self, llm_manager: Any):
        self.llm = llm_manager
        self.master_supervisor: Optional[Any] = None
        self.department_supervisors: Dict[str, Any] = {}
        self.worker_agents: Dict[str, Dict[str, Any]] = {}
        logger.info("🏢 Hierarchical Orchestrator initialized")

    def create_department(
        self,
        department_name: str,
        workers: Dict[str, Any]
    ):
        """Create a department with supervisor and workers"""

        orchestrator = LangGraphOrchestrator(self.llm)
        graph = orchestrator.build_graph(
            supervisor_name=f"{department_name}_supervisor",
            agents=workers
        )

        self.department_supervisors[department_name] = orchestrator
        self.worker_agents[department_name] = workers

        logger.info(f"✅ Created department: {department_name} with {len(workers)} workers")

    def create_master_supervisor(self):
        """Create master supervisor that routes to departments"""

        # Create master orchestrator that routes to department supervisors
        async def department_executor(dept_name: str, task: str, context: Dict) -> Any:
            """Execute task in a specific department"""
            if dept_name in self.department_supervisors:
                supervisor = self.department_supervisors[dept_name]
                result = await supervisor.execute_workflow(task, context)
                return result
            return {"error": f"Department {dept_name} not found"}

        # Build master graph
        department_funcs = {
            dept_name: lambda t, c, d=dept_name: department_executor(d, t, c)
            for dept_name in self.department_supervisors.keys()
        }

        master_orch = LangGraphOrchestrator(self.llm)
        master_orch.build_graph(
            supervisor_name="master_supervisor",
            agents=department_funcs
        )

        self.master_supervisor = master_orch
        logger.info("✅ Master supervisor created")

    async def execute_hierarchical_task(
        self,
        task: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute task through hierarchical structure"""

        if not self.master_supervisor:
            raise ValueError("Master supervisor not created")

        return await self.master_supervisor.execute_workflow(task, context)

    def get_organization_chart(self) -> Dict[str, Any]:
        """Get the organizational structure"""
        return {
            "master_supervisor": {
                "departments": {
                    dept_name: list(workers.keys())
                    for dept_name, workers in self.worker_agents.items()
                }
            }
        }


# Global orchestrator instances
_graph_orchestrator: Optional[LangGraphOrchestrator] = None
_hierarchical_orchestrator: Optional[HierarchicalOrchestrator] = None


def get_graph_orchestrator(llm_manager: Any) -> LangGraphOrchestrator:
    """Get or create graph orchestrator"""
    global _graph_orchestrator
    if _graph_orchestrator is None:
        _graph_orchestrator = LangGraphOrchestrator(llm_manager)
    return _graph_orchestrator


def get_hierarchical_orchestrator(llm_manager: Any) -> HierarchicalOrchestrator:
    """Get or create hierarchical orchestrator"""
    global _hierarchical_orchestrator
    if _hierarchical_orchestrator is None:
        _hierarchical_orchestrator = HierarchicalOrchestrator(llm_manager)
    return _hierarchical_orchestrator
