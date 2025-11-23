"""
Agent Factory - Dynamic agent creation and management
Creates specialized agents on-the-fly based on requirements
"""
from typing import Dict, List, Optional, Any, Type, Callable
from enum import Enum
from pydantic import BaseModel, Field
from loguru import logger
import importlib
import inspect


class AgentCapability(str, Enum):
    """Agent capabilities/skills"""
    # Core capabilities
    REASONING = "reasoning"
    ANALYSIS = "analysis"
    SEARCH = "search"
    SCRAPING = "scraping"
    DATA_EXTRACTION = "data_extraction"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"

    # Domain-specific
    FINANCIAL_ANALYSIS = "financial_analysis"
    MARKET_RESEARCH = "market_research"
    LEGAL_ANALYSIS = "legal_analysis"
    TECHNICAL_WRITING = "technical_writing"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"

    # Specialized
    IMAGE_ANALYSIS = "image_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TREND_PREDICTION = "trend_prediction"
    RECOMMENDATION = "recommendation"
    PLANNING = "planning"
    COORDINATION = "coordination"
    VERIFICATION = "verification"
    QUALITY_ASSURANCE = "quality_assurance"


class AgentRole(str, Enum):
    """Agent roles in the system"""
    WORKER = "worker"  # Task execution
    ANALYST = "analyst"  # Data analysis
    RESEARCHER = "researcher"  # Information gathering
    SUPERVISOR = "supervisor"  # Coordinates other agents
    SPECIALIST = "specialist"  # Domain expert
    VALIDATOR = "validator"  # Quality check
    ORCHESTRATOR = "orchestrator"  # High-level coordination


class AgentSpec(BaseModel):
    """Specification for creating an agent"""
    name: str
    role: AgentRole
    capabilities: List[AgentCapability]
    description: str
    tools: List[str] = Field(default_factory=list)
    model: str = "llama-3.3-70b-versatile"  # Default GROQ model
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentTemplate:
    """Templates for common agent types"""

    @staticmethod
    def web_researcher() -> AgentSpec:
        return AgentSpec(
            name="Web Researcher",
            role=AgentRole.RESEARCHER,
            capabilities=[AgentCapability.SEARCH, AgentCapability.SCRAPING, AgentCapability.DATA_EXTRACTION],
            description="Searches the web and extracts relevant information",
            tools=["web_search", "web_scrape", "extract_data"],
            temperature=0.5
        )

    @staticmethod
    def data_analyst() -> AgentSpec:
        return AgentSpec(
            name="Data Analyst",
            role=AgentRole.ANALYST,
            capabilities=[AgentCapability.ANALYSIS, AgentCapability.REASONING, AgentCapability.SUMMARIZATION],
            description="Analyzes data and provides insights",
            tools=["analyze_data", "generate_statistics", "create_visualization"],
            temperature=0.3
        )

    @staticmethod
    def content_summarizer() -> AgentSpec:
        return AgentSpec(
            name="Content Summarizer",
            role=AgentRole.WORKER,
            capabilities=[AgentCapability.SUMMARIZATION, AgentCapability.ANALYSIS],
            description="Summarizes long-form content into key points",
            tools=["summarize_text", "extract_key_points"],
            temperature=0.4
        )

    @staticmethod
    def sentiment_analyzer() -> AgentSpec:
        return AgentSpec(
            name="Sentiment Analyzer",
            role=AgentRole.ANALYST,
            capabilities=[AgentCapability.SENTIMENT_ANALYSIS, AgentCapability.CLASSIFICATION],
            description="Analyzes sentiment in text data",
            tools=["analyze_sentiment", "classify_emotion"],
            temperature=0.2
        )

    @staticmethod
    def market_researcher() -> AgentSpec:
        return AgentSpec(
            name="Market Researcher",
            role=AgentRole.RESEARCHER,
            capabilities=[AgentCapability.MARKET_RESEARCH, AgentCapability.TREND_PREDICTION, AgentCapability.ANALYSIS],
            description="Researches market trends and opportunities",
            tools=["search_market_data", "analyze_trends", "predict_demand"],
            temperature=0.6
        )

    @staticmethod
    def code_reviewer() -> AgentSpec:
        return AgentSpec(
            name="Code Reviewer",
            role=AgentRole.SPECIALIST,
            capabilities=[AgentCapability.CODE_REVIEW, AgentCapability.QUALITY_ASSURANCE],
            description="Reviews code for quality, security, and best practices",
            tools=["analyze_code", "check_security", "suggest_improvements"],
            temperature=0.3
        )

    @staticmethod
    def planner() -> AgentSpec:
        return AgentSpec(
            name="Strategic Planner",
            role=AgentRole.ORCHESTRATOR,
            capabilities=[AgentCapability.PLANNING, AgentCapability.REASONING, AgentCapability.COORDINATION],
            description="Creates strategic plans and coordinates execution",
            tools=["create_plan", "allocate_resources", "track_progress"],
            temperature=0.7
        )

    @staticmethod
    def quality_checker() -> AgentSpec:
        return AgentSpec(
            name="Quality Checker",
            role=AgentRole.VALIDATOR,
            capabilities=[AgentCapability.QUALITY_ASSURANCE, AgentCapability.VERIFICATION],
            description="Validates output quality and accuracy",
            tools=["validate_output", "check_accuracy", "verify_completeness"],
            temperature=0.2
        )


class AgentFactory:
    """Factory for creating and managing agents"""

    def __init__(self):
        self._agent_registry: Dict[str, AgentSpec] = {}
        self._agent_instances: Dict[str, Any] = {}
        self._templates = AgentTemplate()
        logger.info("🏭 Agent Factory initialized")

    def register_agent_spec(self, spec: AgentSpec):
        """Register an agent specification"""
        self._agent_registry[spec.name] = spec
        logger.info(f"✅ Registered agent spec: {spec.name}")

    def create_agent(self, spec: AgentSpec, llm_manager: Any) -> Any:
        """Create an agent instance from specification"""
        try:
            # Import required modules dynamically
            from langchain.agents import AgentExecutor, create_react_agent
            from langchain.prompts import PromptTemplate
            from langchain_core.tools import Tool

            # Build system prompt
            system_prompt = spec.system_prompt or self._build_system_prompt(spec)

            # Create prompt template
            prompt = PromptTemplate.from_template(
                f"""You are {spec.name}.

{spec.description}

Your role: {spec.role.value}
Your capabilities: {', '.join([c.value for c in spec.capabilities])}

{system_prompt}

Question: {{input}}

Thought: {{agent_scratchpad}}
"""
            )

            # Get tools for this agent
            tools = self._get_tools_for_agent(spec)

            # Create agent
            agent = create_react_agent(
                llm=llm_manager,
                tools=tools,
                prompt=prompt
            )

            # Create executor
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                max_iterations=10,
                handle_parsing_errors=True
            )

            self._agent_instances[spec.name] = agent_executor
            logger.info(f"✅ Created agent: {spec.name}")

            return agent_executor

        except Exception as e:
            logger.error(f"Failed to create agent {spec.name}: {e}")
            raise

    def _build_system_prompt(self, spec: AgentSpec) -> str:
        """Build system prompt based on agent spec"""
        prompt_parts = []

        if AgentCapability.REASONING in spec.capabilities:
            prompt_parts.append("You excel at logical reasoning and problem-solving.")

        if AgentCapability.ANALYSIS in spec.capabilities:
            prompt_parts.append("You analyze data thoroughly and provide actionable insights.")

        if AgentCapability.SEARCH in spec.capabilities:
            prompt_parts.append("You are skilled at finding relevant information from various sources.")

        if spec.role == AgentRole.SUPERVISOR:
            prompt_parts.append("You coordinate and delegate tasks to other agents effectively.")

        if spec.role == AgentRole.SPECIALIST:
            prompt_parts.append("You are a domain expert with deep specialized knowledge.")

        return "\n".join(prompt_parts)

    def _get_tools_for_agent(self, spec: AgentSpec) -> List[Any]:
        """Get tools for an agent based on its specification"""
        from langchain_core.tools import Tool

        # This would integrate with the tool database
        # For now, return placeholder tools
        tools = []

        for tool_name in spec.tools:
            tool = Tool(
                name=tool_name,
                description=f"Tool for {tool_name.replace('_', ' ')}",
                func=lambda x: f"Executed {tool_name}"
            )
            tools.append(tool)

        return tools

    def create_from_template(self, template_name: str, llm_manager: Any) -> Any:
        """Create agent from a template"""
        template_method = getattr(self._templates, template_name, None)
        if not template_method:
            raise ValueError(f"Template {template_name} not found")

        spec = template_method()
        return self.create_agent(spec, llm_manager)

    def create_specialized_agent(
        self,
        name: str,
        purpose: str,
        capabilities: List[AgentCapability],
        llm_manager: Any,
        **kwargs
    ) -> Any:
        """Create a specialized agent for a specific purpose"""
        spec = AgentSpec(
            name=name,
            role=AgentRole.SPECIALIST,
            capabilities=capabilities,
            description=purpose,
            **kwargs
        )
        return self.create_agent(spec, llm_manager)

    def get_agent(self, name: str) -> Optional[Any]:
        """Get an existing agent instance"""
        return self._agent_instances.get(name)

    def list_available_templates(self) -> List[str]:
        """List all available agent templates"""
        return [
            name for name, method in inspect.getmembers(self._templates)
            if callable(method) and not name.startswith('_')
        ]

    def get_all_agents(self) -> Dict[str, Any]:
        """Get all agent instances"""
        return self._agent_instances

    def remove_agent(self, name: str):
        """Remove an agent instance"""
        if name in self._agent_instances:
            del self._agent_instances[name]
            logger.info(f"Removed agent: {name}")


# Predefined agent library - 100+ agent types
class AgentLibrary:
    """Library of 100+ specialized agent templates"""

    # Research & Analysis Agents (20)
    WEB_RESEARCHER = "web_researcher"
    ACADEMIC_RESEARCHER = "academic_researcher"
    MARKET_RESEARCHER = "market_researcher"
    COMPETITIVE_ANALYST = "competitive_analyst"
    DATA_ANALYST = "data_analyst"
    FINANCIAL_ANALYST = "financial_analyst"
    SENTIMENT_ANALYST = "sentiment_analyst"
    TREND_ANALYST = "trend_analyst"
    RISK_ANALYST = "risk_analyst"
    OPPORTUNITY_ANALYST = "opportunity_analyst"
    CUSTOMER_ANALYST = "customer_analyst"
    PRODUCT_ANALYST = "product_analyst"
    SWOT_ANALYST = "swot_analyst"
    STATISTICAL_ANALYST = "statistical_analyst"
    BEHAVIORAL_ANALYST = "behavioral_analyst"
    TECHNICAL_ANALYST = "technical_analyst"
    QUALITATIVE_RESEARCHER = "qualitative_researcher"
    QUANTITATIVE_RESEARCHER = "quantitative_researcher"
    USER_RESEARCHER = "user_researcher"
    ETHNOGRAPHIC_RESEARCHER = "ethnographic_researcher"

    # Content & Communication Agents (20)
    CONTENT_WRITER = "content_writer"
    TECHNICAL_WRITER = "technical_writer"
    COPYWRITER = "copywriter"
    CONTENT_SUMMARIZER = "content_summarizer"
    TRANSLATOR = "translator"
    EDITOR = "editor"
    PROOFREADER = "proofreader"
    SEO_SPECIALIST = "seo_specialist"
    SOCIAL_MEDIA_MANAGER = "social_media_manager"
    EMAIL_COMPOSER = "email_composer"
    BLOG_WRITER = "blog_writer"
    SCRIPT_WRITER = "script_writer"
    SPEECH_WRITER = "speech_writer"
    STORYTELLER = "storyteller"
    JOURNALIST = "journalist"
    DOCUMENTATION_SPECIALIST = "documentation_specialist"
    CONTENT_STRATEGIST = "content_strategist"
    BRAND_VOICE_SPECIALIST = "brand_voice_specialist"
    HEADLINE_GENERATOR = "headline_generator"
    TAG_GENERATOR = "tag_generator"

    # Development & Technical Agents (20)
    CODE_GENERATOR = "code_generator"
    CODE_REVIEWER = "code_reviewer"
    DEBUG_ASSISTANT = "debug_assistant"
    ARCHITECTURE_DESIGNER = "architecture_designer"
    DATABASE_DESIGNER = "database_designer"
    API_DESIGNER = "api_designer"
    TEST_GENERATOR = "test_generator"
    SECURITY_AUDITOR = "security_auditor"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"
    DEVOPS_SPECIALIST = "devops_specialist"
    CLOUD_ARCHITECT = "cloud_architect"
    INFRASTRUCTURE_ENGINEER = "infrastructure_engineer"
    FRONTEND_SPECIALIST = "frontend_specialist"
    BACKEND_SPECIALIST = "backend_specialist"
    FULLSTACK_DEVELOPER = "fullstack_developer"
    MOBILE_DEVELOPER = "mobile_developer"
    DATA_ENGINEER = "data_engineer"
    ML_ENGINEER = "ml_engineer"
    QA_ENGINEER = "qa_engineer"
    ACCESSIBILITY_SPECIALIST = "accessibility_specialist"

    # Business & Strategy Agents (20)
    BUSINESS_STRATEGIST = "business_strategist"
    STRATEGIC_PLANNER = "strategic_planner"
    BUSINESS_ANALYST = "business_analyst"
    OPERATIONS_MANAGER = "operations_manager"
    PROJECT_MANAGER = "project_manager"
    PRODUCT_MANAGER = "product_manager"
    CHANGE_MANAGER = "change_manager"
    RISK_MANAGER = "risk_manager"
    COMPLIANCE_OFFICER = "compliance_officer"
    QUALITY_MANAGER = "quality_manager"
    HR_SPECIALIST = "hr_specialist"
    RECRUITMENT_SPECIALIST = "recruitment_specialist"
    TRAINING_SPECIALIST = "training_specialist"
    SALES_STRATEGIST = "sales_strategist"
    MARKETING_STRATEGIST = "marketing_strategist"
    GROWTH_HACKER = "growth_hacker"
    PRICING_STRATEGIST = "pricing_strategist"
    PARTNERSHIP_MANAGER = "partnership_manager"
    INVESTOR_RELATIONS = "investor_relations"
    CRISIS_MANAGER = "crisis_manager"

    # Specialized Domain Agents (20)
    LEGAL_ASSISTANT = "legal_assistant"
    MEDICAL_ADVISOR = "medical_advisor"
    EDUCATION_SPECIALIST = "education_specialist"
    SUPPLY_CHAIN_SPECIALIST = "supply_chain_specialist"
    LOGISTICS_COORDINATOR = "logistics_coordinator"
    PROCUREMENT_SPECIALIST = "procurement_specialist"
    VENDOR_MANAGER = "vendor_manager"
    CUSTOMER_SERVICE_AGENT = "customer_service_agent"
    SUPPORT_AGENT = "support_agent"
    SALES_AGENT = "sales_agent"
    ACCOUNT_MANAGER = "account_manager"
    REAL_ESTATE_AGENT = "real_estate_agent"
    TRAVEL_PLANNER = "travel_planner"
    EVENT_PLANNER = "event_planner"
    RESTAURANT_ADVISOR = "restaurant_advisor"
    FITNESS_COACH = "fitness_coach"
    NUTRITION_ADVISOR = "nutrition_advisor"
    MENTAL_HEALTH_COACH = "mental_health_coach"
    CAREER_COACH = "career_coach"
    LIFE_COACH = "life_coach"

    # Coordination & Management Agents (20)
    MASTER_ORCHESTRATOR = "master_orchestrator"
    TEAM_COORDINATOR = "team_coordinator"
    WORKFLOW_MANAGER = "workflow_manager"
    TASK_ALLOCATOR = "task_allocator"
    RESOURCE_MANAGER = "resource_manager"
    PRIORITY_MANAGER = "priority_manager"
    DEPENDENCY_TRACKER = "dependency_tracker"
    PROGRESS_MONITOR = "progress_monitor"
    QUALITY_CHECKER = "quality_checker"
    VALIDATOR = "validator"
    VERIFIER = "verifier"
    AGGREGATOR = "aggregator"
    SYNTHESIZER = "synthesizer"
    CONSOLIDATOR = "consolidator"
    REPORTER = "reporter"
    METRICS_COLLECTOR = "metrics_collector"
    PERFORMANCE_TRACKER = "performance_tracker"
    ERROR_HANDLER = "error_handler"
    FALLBACK_MANAGER = "fallback_manager"
    ESCALATION_MANAGER = "escalation_manager"


# Global factory instance
_agent_factory: Optional[AgentFactory] = None


def get_agent_factory() -> AgentFactory:
    """Get or create agent factory instance"""
    global _agent_factory
    if _agent_factory is None:
        _agent_factory = AgentFactory()
    return _agent_factory
