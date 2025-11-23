# 🤖 Multi-Agent Orchestration System

Advanced AI agent coordination system with 100+ specialized agents, LangGraph workflows, and Redis-backed memory.

---

## 🌟 Overview

The Artisan Hub orchestration system is a powerful multi-agent framework that enables:

- **100+ Specialized Agents** - Pre-built agents for every task imaginable
- **LangGraph Workflows** - Complex multi-agent workflows with state management
- **Hierarchical Organization** - Master supervisors → Department supervisors → Worker agents
- **Tool Database** - Centralized registry of 1000+ tools with analytics
- **Agent Memory** - Redis-backed short-term, long-term, and shared memory
- **Dynamic Agent Creation** - Create custom agents on-the-fly
- **Real-time Monitoring** - Track agent performance and resource usage

---

## 🏗️ Architecture

```
Master Supervisor (Orchestrates everything)
├── Research Department
│   ├── Web Researcher
│   ├── Market Researcher
│   ├── Academic Researcher
│   └── Competitive Analyst
├── Analysis Department
│   ├── Data Analyst
│   ├── Financial Analyst
│   ├── Sentiment Analyst
│   └── Trend Analyst
├── Content Department
│   ├── Content Writer
│   ├── Technical Writer
│   ├── Copywriter
│   └── Editor
└── Development Department
    ├── Code Generator
    ├── Code Reviewer
    ├── Architecture Designer
    └── QA Engineer
```

---

## 📦 Components

### 1. **Agent Factory** (`agent_factory.py`)
Creates and manages specialized agents dynamically.

**100+ Agent Types:**
- **Research & Analysis** (20 agents)
- **Content & Communication** (20 agents)
- **Development & Technical** (20 agents)
- **Business & Strategy** (20 agents)
- **Specialized Domain** (20 agents)
- **Coordination & Management** (20 agents)

### 2. **LangGraph Orchestrator** (`graph_orchestrator.py`)
Coordinates complex multi-agent workflows using LangGraph.

**Features:**
- State-based execution
- Conditional routing
- Error handling
- Result aggregation
- Workflow visualization

### 3. **Tool Database** (`tool_database.py`)
SQLAlchemy-backed database for tool management.

**Tracks:**
- Tool definitions and schemas
- Usage statistics
- Performance metrics
- Agent-tool relationships

### 4. **Agent Memory** (`agent_memory.py`)
Redis-backed memory system for agents.

**Memory Types:**
- **Short-term**: Conversations, recent tasks (1 hour TTL)
- **Long-term**: Important results, learnings (24 hour+ TTL)
- **Shared**: Knowledge available to all agents

---

## 🚀 Quick Start

### 1. **Start the Stack**
```bash
# Includes Redis for agent memory
./docker-start.sh prod
```

### 2. **Create Your First Agent**
```python
import requests

# Create a specialized market researcher
response = requests.post("http://localhost:8000/orchestration/agents/create", json={
    "name": "Market Intelligence Agent",
    "role": "researcher",
    "capabilities": ["market_research", "trend_prediction", "analysis"],
    "description": "Analyzes market trends and predicts opportunities",
    "tools": ["web_search", "data_analysis", "trend_detection"]
})
```

### 3. **Execute a Workflow**
```python
# Execute multi-agent workflow
response = requests.post("http://localhost:8000/orchestration/workflow/execute", json={
    "task": "Find top suppliers for pottery materials in India",
    "agents": ["web_researcher", "data_analyst", "quality_checker"],
    "use_supervisor": True,
    "max_iterations": 10
})

print(response.json())
```

---

## 📊 API Endpoints

### Agent Management

**Create Agent**
```bash
POST /orchestration/agents/create
{
  "name": "Custom Agent",
  "role": "specialist",
  "capabilities": ["analysis", "reasoning"],
  "description": "Specialized agent for X",
  "tools": ["tool1", "tool2"]
}
```

**List Agents**
```bash
GET /orchestration/agents/list
```

**List Templates**
```bash
GET /orchestration/agents/templates
```

### Workflow Execution

**Execute Workflow**
```bash
POST /orchestration/workflow/execute
{
  "task": "Your task here",
  "agents": ["agent1", "agent2"],
  "use_supervisor": true,
  "max_iterations": 10
}
```

### Tool Management

**Register Tool**
```bash
POST /orchestration/tools/register
{
  "name": "my_tool",
  "description": "What it does",
  "category": "category_name",
  "parameters_schema": {...},
  "implementation": "module.path.to.function"
}
```

**List Tools**
```bash
GET /orchestration/tools/list?category=web_scraping
```

**Tool Analytics**
```bash
GET /orchestration/tools/my_tool/analytics
```

### Memory Management

**Get Memory Stats**
```bash
GET /orchestration/memory/{agent_id}/stats
```

**Clear Memory**
```bash
DELETE /orchestration/memory/{agent_id}/clear?memory_type=short_term
```

### Hierarchical Organization

**Create Hierarchy**
```bash
POST /orchestration/hierarchy/create
{
  "research_dept": ["researcher1", "researcher2"],
  "analysis_dept": ["analyst1", "analyst2"],
  "content_dept": ["writer1", "editor1"]
}
```

---

## 💡 Use Cases

### 1. **Automated Research Pipeline**
```python
workflow = {
    "task": "Research emerging craft trends in India",
    "agents": [
        "web_researcher",      # Finds information
        "data_analyst",        # Analyzes data
        "trend_predictor",     # Predicts trends
        "report_writer"        # Creates report
    ],
    "use_supervisor": True
}
```

### 2. **Content Creation System**
```python
workflow = {
    "task": "Create marketing content for new product",
    "agents": [
        "market_researcher",   # Research target audience
        "copywriter",          # Write content
        "seo_specialist",      # Optimize for SEO
        "editor",              # Polish and finalize
        "quality_checker"      # Final review
    ]
}
```

### 3. **E-commerce Intelligence**
```python
workflow = {
    "task": "Analyze competitors and pricing strategy",
    "agents": [
        "competitive_analyst", # Analyze competitors
        "pricing_strategist",  # Recommend pricing
        "market_researcher",   # Market positioning
        "financial_analyst"    # Profit optimization
    ]
}
```

---

## 🏢 Agent Library

### Research & Analysis Agents
- `web_researcher` - Web search and information gathering
- `academic_researcher` - Scholarly research
- `market_researcher` - Market analysis
- `competitive_analyst` - Competitor analysis
- `data_analyst` - Data analysis and insights
- `financial_analyst` - Financial analysis
- `sentiment_analyst` - Sentiment analysis
- `trend_analyst` - Trend detection
- `risk_analyst` - Risk assessment
- `opportunity_analyst` - Opportunity identification
- ...and 10 more

### Content & Communication Agents
- `content_writer` - General content writing
- `technical_writer` - Technical documentation
- `copywriter` - Marketing copy
- `content_summarizer` - Content summarization
- `translator` - Multi-language translation
- `editor` - Content editing
- `proofreader` - Grammar and style checking
- `seo_specialist` - SEO optimization
- `social_media_manager` - Social media content
- `email_composer` - Email writing
- ...and 10 more

### Development & Technical Agents
- `code_generator` - Code generation
- `code_reviewer` - Code review
- `debug_assistant` - Debugging help
- `architecture_designer` - System architecture
- `database_designer` - Database design
- `api_designer` - API design
- `test_generator` - Test generation
- `security_auditor` - Security audit
- `performance_optimizer` - Performance optimization
- `devops_specialist` - DevOps automation
- ...and 10 more

### Business & Strategy Agents
- `business_strategist` - Business strategy
- `strategic_planner` - Strategic planning
- `operations_manager` - Operations optimization
- `project_manager` - Project management
- `product_manager` - Product strategy
- `sales_strategist` - Sales strategy
- `marketing_strategist` - Marketing strategy
- `growth_hacker` - Growth strategies
- `pricing_strategist` - Pricing optimization
- `crisis_manager` - Crisis management
- ...and 10 more

### Specialized Domain Agents
- `legal_assistant` - Legal research
- `medical_advisor` - Medical information
- `supply_chain_specialist` - Supply chain optimization
- `customer_service_agent` - Customer support
- `real_estate_agent` - Real estate analysis
- `travel_planner` - Travel planning
- `event_planner` - Event organization
- `fitness_coach` - Fitness guidance
- `career_coach` - Career advice
- `life_coach` - Life coaching
- ...and 10 more

### Coordination & Management Agents
- `master_orchestrator` - Top-level coordination
- `team_coordinator` - Team management
- `workflow_manager` - Workflow optimization
- `task_allocator` - Task distribution
- `resource_manager` - Resource allocation
- `quality_checker` - Quality assurance
- `validator` - Validation and verification
- `aggregator` - Result aggregation
- `reporter` - Report generation
- `metrics_collector` - Metrics tracking
- ...and 10 more

---

## 🔧 Configuration

### Environment Variables
```env
# Redis (required for agent memory)
REDIS_URL=redis://localhost:6379

# LLM Provider
LLM_PROVIDER=groq
GROQ_API_KEY=your-key-here

# Database
DATABASE_URL=sqlite:///./data/tools.db  # Tool database
```

### Docker Compose
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  backend:
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
```

---

## 📈 Monitoring & Analytics

### Tool Analytics
```bash
# Get most used tools
GET /orchestration/tools/top?limit=10

# Get tool performance
GET /orchestration/tools/web_search/analytics
```

### Memory Stats
```bash
# Check memory usage
GET /orchestration/memory/agent_123/stats
```

### System Health
```bash
# Overall system health
GET /orchestration/health
```

---

## 🎯 Advanced Features

### 1. **Dynamic Agent Creation**
Create agents programmatically based on task requirements:
```python
factory = get_agent_factory()
agent = factory.create_specialized_agent(
    name="Domain Expert",
    purpose="Pottery supply chain analysis",
    capabilities=[AgentCapability.ANALYSIS, AgentCapability.RESEARCH],
    llm_manager=llm
)
```

### 2. **Multi-Level Supervision**
```python
# Create hierarchical structure
hierarchy = get_hierarchical_orchestrator(llm)

# Add departments
hierarchy.create_department("research", {
    "web_researcher": web_research_func,
    "data_analyst": data_analysis_func
})

hierarchy.create_department("content", {
    "writer": writing_func,
    "editor": editing_func
})

# Create master supervisor
hierarchy.create_master_supervisor()

# Execute hierarchical task
result = await hierarchy.execute_hierarchical_task(
    "Complete market research and create report"
)
```

### 3. **Conversation Memory**
```python
from agent_memory import ConversationBuffer

buffer = ConversationBuffer(memory_manager, agent_id="agent_123")
await buffer.add_message("user", "Find suppliers in India")
await buffer.add_message("assistant", "Found 10 suppliers")

# Retrieve conversation history
messages = await buffer.get_messages()
```

### 4. **Shared Knowledge**
```python
# Store knowledge accessible to all agents
await memory_manager.store_shared_knowledge(
    key="india_suppliers_database",
    value={"suppliers": [...]}
)

# Any agent can retrieve it
suppliers = await memory_manager.get_shared_knowledge(
    "india_suppliers_database"
)
```

---

## 🔍 Tool Database Schema

### Tools Table
- `id` - Unique identifier
- `name` - Tool name
- `description` - What it does
- `category` - Tool category
- `parameters_schema` - JSON schema for inputs
- `usage_count` - Times used
- `success_count` - Successful executions
- `avg_execution_time` - Average execution time

### Tool Executions Table
- Tracks every tool execution
- Input parameters
- Output data
- Execution time
- Success/failure
- Error messages

---

## 🚨 Error Handling

All orchestration endpoints include comprehensive error handling:

```json
{
  "success": false,
  "errors": ["Agent not found", "Tool execution failed"],
  "results": {},
  "iterations": 3
}
```

---

## 📚 Examples

See `/examples/orchestration/` for:
- `create_custom_agent.py` - Create specialized agents
- `multi_agent_workflow.py` - Complex workflows
- `hierarchical_organization.py` - Multi-level coordination
- `tool_registration.py` - Register custom tools
- `memory_management.py` - Agent memory patterns

---

## 🎓 Best Practices

1. **Use Supervisors** - For complex multi-step tasks
2. **Cache Results** - Store in agent memory for reuse
3. **Monitor Tools** - Track usage and performance
4. **Cleanup Memory** - Clear old short-term memories
5. **Validate Outputs** - Always use a quality_checker agent
6. **Handle Errors** - Set appropriate max_iterations

---

## 🔗 Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guide
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [LangChain Docs](https://python.langchain.com/docs/) - LangChain reference
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/) - LangGraph guide

---

**Built with ❤️ for Artisan Hub - Making AI accessible to craftspeople worldwide**
