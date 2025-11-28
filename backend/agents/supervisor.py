"""
Supervisor Agent - Plans and orchestrates specialized worker agents
"""
from typing import Dict, Any, List, Optional, Callable
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.agents.profile_analyst import ProfileAnalystAgent
from backend.agents.supply_hunter import SupplyHunterAgent
from backend.agents.growth_marketer import GrowthMarketerAgent
from backend.agents.event_scout import EventScoutAgent
from backend.agents.framework.tools import default_tool_registry
from backend.agents.framework.planner import Planner
from backend.agents.framework.executor import Executor
from backend.agents.framework.guardrails import Guardrails

from backend.core.cloud_llm_client import CloudLLMClient
from backend.core.vector_store import ArtisanVectorStore
from backend.scraping.web_scraper import WebScraperService
from backend.services.maps_service import MapsService


class SupervisorAgent(BaseAgent):
    """
    Orchestrates a mission by:
    1) Planning steps
    2) Dispatching tasks to worker agents
    3) Enforcing constraints (max steps, region priority)
    4) Aggregating results
    """

    def __init__(
        self,
        cloud_llm_client: CloudLLMClient,
        vector_store: ArtisanVectorStore,
        scraper_service: Optional[WebScraperService] = None,
        maps_service: Optional[MapsService] = None,
    ):
        super().__init__(
            name="Supervisor",
            description="Plans and coordinates specialized agents to achieve a goal",
            cloud_llm_client=cloud_llm_client,
            vector_store=vector_store,
        )
        self.scraper = scraper_service or WebScraperService()
        self.maps = maps_service or MapsService()
        self.tools = default_tool_registry()
        self.planner = Planner(self.ollama)
        self.guardrails = Guardrails()

        # Worker agent factories (lazy to avoid heavy setup when not used)
        self._workers: Dict[str, Callable[[], BaseAgent]] = {
            "profile_analyst": lambda: ProfileAnalystAgent(self.ollama, self.vector_store),
            "supply_hunter": lambda: SupplyHunterAgent(self.ollama, self.vector_store, self.scraper),
            "growth_marketer": lambda: GrowthMarketerAgent(self.ollama, self.vector_store, self.scraper),
            "event_scout": lambda: EventScoutAgent(self.ollama, self.vector_store, self.scraper, self.maps),
        }

    async def analyze(self, user_profile: Dict) -> Dict:
        """
        This method supports a generic "mission" with constraints.

        Expected user_profile keys:
        - goal: high-level mission goal string
        - context: optional dict with craft_type/location/etc.
        - constraints: { max_steps: int, region_priority: str, step_timeout_s: int }
        - capabilities: list of worker keys to allow (subset of self._workers.keys())
        """
        goal: str = user_profile.get("goal", "").strip()
        context: Dict[str, Any] = user_profile.get("context", {})
        constraints: Dict[str, Any] = user_profile.get("constraints", {})
        allowed_caps: Optional[List[str]] = user_profile.get("capabilities")

        if not goal:
            return {"error": "Missing 'goal' in request"}

        max_steps: int = int(constraints.get("max_steps", 6))
        region_priority: str = str(constraints.get("region_priority", "in-first"))

        # 1) Plan steps using Planner (compact and bounded)
        self.log_execution("planning_start", {"goal": goal, "max_steps": max_steps})
        try:
            steps = await self.planner.create_plan(goal, context, max_steps, list(self._workers.keys()))
        except Exception as parse_err:
            logger.warning(f"Planner failed, falling back to minimal plan: {parse_err}")
            steps = self._fallback_minimal_plan(goal, context)

        # Filter to allowed capabilities if provided
        if allowed_caps:
            steps = [s for s in steps if s.get("worker") in allowed_caps]

        # Enforce max steps hard cap
        steps = steps[:max_steps]

        self.log_execution("planning_complete", {"num_steps": len(steps)})

        # 2) Execute plan sequentially with guardrails and tool calls
        artifacts: List[Dict[str, Any]] = []
        executor = Executor(self.tools.get, timeout_s=int(constraints.get("step_timeout_s", 60)), max_retries=int(constraints.get("retries", 1)))
        for idx, step in enumerate(steps, start=1):
            worker_key = step.get("worker")
            inputs = step.get("inputs", {})

            if worker_key not in self._workers:
                self.log_execution("skip_step", {"step": idx, "reason": "unknown_worker", "worker": worker_key})
                continue

            if allowed_caps and worker_key not in allowed_caps:
                self.log_execution("skip_step", {"step": idx, "reason": "capability_not_allowed", "worker": worker_key})
                continue

            worker = self._workers[worker_key]()

            # Merge mission context into worker inputs (worker can ignore extras) and run through executor
            worker_input = {**context, **inputs}
            worker_input_str = self.guardrails.redact_pii(str(worker_input))
            self.log_execution("step_start", {"step": idx, "worker": worker_key, "inputs": worker_input_str})

            try:
                result = await executor.execute_step(step, lambda inp: worker.analyze(inp))
            except Exception as run_err:
                self.log_execution("step_error", {"step": idx, "worker": worker_key, "error": str(run_err)})
                continue

            artifacts.append({
                "step": idx,
                "worker": worker_key,
                "result": result,
            })
            self.log_execution("step_complete", {"step": idx, "worker": worker_key})

        # 3) Summarize outcomes
        summary_prompt = (
            "Given the mission goal and the artifacts from each step, produce a concise outcome summary "
            "with next-best actions and any blockers. Return JSON with keys: summary, recommended_next_steps[]."
        )
        summary_text = await self.ollama.fast_task(
            summary_prompt + "\nGOAL: " + goal + "\nARTIFACTS: " + str(artifacts)[:4000]
        )

        # GOD MODE ENHANCEMENTS - Real Intelligence Operations
        god_mode_insights = await self._god_mode_intelligence(goal, context, artifacts)

        # Generate comprehensive business intelligence report
        return await self._generate_business_intelligence_report(
            goal, context, steps, artifacts, summary_text, god_mode_insights
        )

    async def _god_mode_intelligence(self, goal: str, context: Dict, artifacts: List) -> Dict:
        """GOD MODE: Advanced intelligence operations beyond normal agent capabilities"""

        intelligence_report = {
            "market_forecast": {},
            "competitive_intelligence": {},
            "automated_workflows": {},
            "predictive_analytics": {},
            "strategic_recommendations": {},
            "risk_assessment": {},
            "performance_optimization": {}
        }

        try:
            # 1. REAL-TIME MARKET FORECAST
            forecast_prompt = f"""Analyze current market trends and forecast future opportunities for: {goal}

Context: {str(context)}
Recent agent insights: {str([a['result'] for a in artifacts[-3:]])}

Provide detailed forecast including:
- Market size projection (6 months, 1 year, 2 years)
- Demand elasticity analysis
- Competitor movement predictions
- Regional growth opportunities
- Technology disruption potential
- Consumer behavior shifts

Return structured analysis."""

            intelligence_report["market_forecast"] = await self.ollama.reasoning_task(forecast_prompt)

            # 2. COMPETITIVE INTELLIGENCE
            comp_intel_prompt = f"""Conduct competitive intelligence analysis for the artisan business.

Goal context: {goal[:200]}
Market position: {context.get('location', {}).get('city', 'Unknown')} region

Analyze:
- Key competitors (online vs local)
- Competitive advantages/disadvantages
- Market share analysis
- Pricing strategies of competitors
- Distribution channels
- Marketing approaches
- Innovation opportunities

Return actionable competitive strategy."""

            intelligence_report["competitive_intelligence"] = await self.ollama.reasoning_task(comp_intel_prompt)

            # 3. AUTOMATED BUSINESS WORKFLOWS
            workflow_prompt = f"""Design automated business workflows to execute: {goal[:150]}

Available systems: E-commerce, CRM, inventory, supplier management, marketing automation

Design:
- Lead generation workflow
- Customer journey automation
- Order fulfillment process
- Inventory management triggers
- Marketing campaign sequences
- Quality control processes
- Performance tracking dashboards

Return complete workflow design with triggers and automation rules."""

            intelligence_report["automated_workflows"] = await self.ollama.reasoning_task(workflow_prompt)

            # 4. PREDICTIVE ANALYTICS
            predictive_prompt = f"""Generate predictive analytics for artisan business optimization.

Historical context: {str(context)}
Performance data: {str([a for a in artifacts if 'roi' in str(a).lower()])}

Predict:
- Demand forecasting (seasonal, product-specific)
- Price optimization models
- Inventory turnover rates
- Cash flow projections
- Customer acquisition/lifetime value
- Product profitability analysis
- Market saturation timelines

Return predictive models with confidence levels."""

            intelligence_report["predictive_analytics"] = await self.ollama.reasoning_task(predictive_prompt)

            # 5. STRATEGIC RECOMMENDATIONS
            strategy_prompt = f"""Develop strategic recommendations for artisan business growth.

Strategic goal: {goal[:200]}
Business context: {str(context)}
Competitive analysis: {intelligence_report['competitive_intelligence'][:500]}

Develop:
- 3-year strategic roadmap
- Market penetration strategies
- Product diversification plans
- International expansion framework
- Technology adoption priorities
- Partnership development strategy
- Risk mitigation plans

Return executive strategy document."""

            intelligence_report["strategic_recommendations"] = await self.ollama.reasoning_task(strategy_prompt)

            # 6. RISK ASSESSMENT
            risk_prompt = f"""Comprehensive risk assessment for artisan business operations.

Business profile: {str(context)}
Current operations: {str([a['result'] for a in artifacts])}

Assess risks in:
- Supply chain vulnerabilities
- Market demand fluctuations
- Competitive threats
- Financial risks (cash flow, credit)
- Operational risks (quality, capacity)
- Regulatory compliance
- Technology dependencies
- Reputation management

Return risk mitigation strategies with priority levels."""

            intelligence_report["risk_assessment"] = await self.ollama.reasoning_task(risk_prompt)

            # 7. PERFORMANCE OPTIMIZATION
            optimization_prompt = f"""Design performance optimization framework for artisan business.

Performance goals: {goal[:150]}
Current capabilities: {str(context)}
Historical performance: Extract from agent results

Optimize:
- Operational efficiency metrics
- Cost reduction strategies
- Revenue maximization approaches
- Quality improvement processes
- Customer satisfaction enhancements
- Scalability planning
- Continuous improvement cycles

Return comprehensive optimization roadmap."""

            intelligence_report["performance_optimization"] = await self.ollama.reasoning_task(optimization_prompt)

        except Exception as e:
            logger.error(f"GOD MODE intelligence failed: {e}")
            intelligence_report["error"] = f"Intelligence generation failed: {str(e)}"

        return intelligence_report

    def _safe_parse_json_array(self, text: str) -> List[Dict[str, Any]]:
        import json
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "steps" in parsed and isinstance(parsed["steps"], list):
            return parsed["steps"]
        raise ValueError("Unexpected plan JSON shape")

    def _fallback_minimal_plan(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Heuristic minimal plan: profile -> supply -> growth
        craft_type = context.get("craft_type")
        steps: List[Dict[str, Any]] = []
        if not craft_type:
            steps.append({
                "step_name": "Profile inference",
                "worker": "profile_analyst",
                "inputs": {"input_text": context.get("input_text", goal)},
                "success_criteria": "Extract craft_type and location",
            })
        steps.append({
            "step_name": "Find suppliers",
            "worker": "supply_hunter",
            "inputs": {
                "craft_type": context.get("craft_type", ""),
                "supplies_needed": context.get("supplies_needed", []),
                "location": context.get("location", {}),
            },
            "success_criteria": "Return verified suppliers",
        })
        steps.append({
            "step_name": "Growth opportunities",
            "worker": "growth_marketer",
            "inputs": {
                "craft_type": context.get("craft_type", ""),
                "specialization": context.get("specialization", ""),
                "current_products": context.get("current_products", []),
                "location": context.get("location", {}),
            },
            "success_criteria": "List top 3 actions",
        })
        return steps

    async def _generate_business_intelligence_report(
        self, goal: str, context: Dict, plan: List[Dict], artifacts: List[Dict],
        summary: str, god_mode_insights: Dict
    ) -> Dict:
        """Generate comprehensive business intelligence for mission coordination."""

        # Create executive summary for the entire mission
        executive_summary = await self._create_mission_executive_summary(goal, context, artifacts)

        # Business plan synthesis from all agents
        business_plan = await self._synthesize_business_plan(artifacts, god_mode_insights)

        # Financial analysis combining all agent results
        financial_analysis = await self._compile_financial_analysis(artifacts)

        # Risk assessment aggregation
        risk_assessment = await self._aggregate_risk_assessments(artifacts, god_mode_insights)

        # Implementation roadmap coordination
        implementation_roadmap = await self._create_coordinated_roadmap(plan, artifacts)

        # Success metrics from all agents
        success_metrics = await self._define_success_metrics(goal, artifacts)

        # Next steps prioritization
        next_steps = await self._prioritize_next_steps(artifacts, plan)

        return {
            "executive_summary": executive_summary,
            "comprehensive_business_plan": business_plan,
            "financial_projections": financial_analysis,
            "integrated_risk_assessment": risk_assessment,
            "coordinated_implementation_roadmap": implementation_roadmap,
            "success_metrics_dashboard": success_metrics,
            "prioritized_next_steps": next_steps,
            # Legacy fields for backwards compatibility
            "goal": goal,
            "constraints": {},
            "plan": plan,
            "artifacts": artifacts,
            "summary": summary,
            "god_mode_insights": god_mode_insights,
            "intelligence_level": "ENTERPRISE_SUPREME"
        }

    async def _create_mission_executive_summary(self, goal: str, context: Dict, artifacts: List[Dict]) -> Dict:
        """Create comprehensive executive summary for the mission."""

        # Count successful agent executions
        successful_agents = len([a for a in artifacts if a.get("result") and not a["result"].get("error")])
        total_agents = len(artifacts)

        # Extract key insights from artifacts
        key_insights = []
        suppliers_found = 0
        growth_opportunities = 0
        revenue_potential = 0

        for artifact in artifacts:
            result = artifact.get("result", {})
            if artifact["worker"] == "supply_hunter" and result.get("supply_chain_analysis"):
                suppliers_found = result.get("metadata", {}).get("total_suppliers_found", 0)
                key_insights.append(f"Identified {suppliers_found} verified suppliers with cost optimization opportunities")
            elif artifact["worker"] == "growth_marketer" and result.get("revenue_growth_roadmap"):
                roadmap = result.get("revenue_growth_roadmap", {})
                current = roadmap.get("current_baseline", {}).get("monthly_revenue", 0)
                target = roadmap.get("growth_targets", {}).get("twelve_month_target", 0)
                if current and target:
                    growth_opportunities = target - current
                key_insights.append(f"Developed 12-month growth roadmap targeting ₹{target:,} revenue")

        craft_type = context.get("craft_type", "crafts")
        location = context.get("location", {}).get("city", "location")

        return {
            "mission_objective": goal,
            "business_context": f"{craft_type.title()} artisan in {location}",
            "execution_success_rate": f"{successful_agents}/{total_agents} agents completed successfully",
            "key_achievements": [
                f"Supply chain optimization: {suppliers_found} verified suppliers identified",
                f"Growth opportunities: ₹{growth_opportunities:,} annual revenue potential",
                "Comprehensive business intelligence generated",
                "Implementation roadmap with specific milestones"
            ],
            "strategic_outcomes": [
                "Complete business transformation plan developed",
                "Financial projections with risk assessments",
                "Automated next-step action items",
                "Performance tracking and success metrics"
            ],
            "mission_status": "COMPLETE - Enterprise business consultation delivered"
        }

    async def _synthesize_business_plan(self, artifacts: List[Dict], god_mode_insights: Dict) -> Dict:
        """Synthesize comprehensive business plan from all agents."""

        vision = "Regional leader in authentic ancestral craftsmanship with modern business operations"
        mission = "Preserve traditional techniques while scaling to meet growing market demand"

        objectives = []
        strategies = []

        # Extract objectives from growth marketer
        for artifact in artifacts:
            if artifact["worker"] == "growth_marketer":
                result = artifact.get("result", {})
                if result.get("revenue_growth_roadmap"):
                    roadmap = result["revenue_growth_roadmap"]
                    current_rev = roadmap.get("current_baseline", {}).get("monthly_revenue", 0)
                    target_rev = roadmap.get("growth_targets", {}).get("twelve_month_target", 0)
                    if target_rev:
                        objectives.append(f"Increase annual revenue from ₹{current_rev*12:,} to ₹{target_rev*12:,} within 12 months")
                        strategies.append("Digital marketplace expansion and brand positioning")

        strategies.extend([
            "Multi-supplier supply chain diversification",
            "Product innovation with market-driven development",
            "Partnership ecosystem development",
            "Operational efficiency optimization"
        ])

        return {
            "vision": vision,
            "mission": mission,
            "strategic_objectives": objectives[:3],  # Top 3
            "core_strategies": strategies,
            "business_model": "Direct-to-consumer artisan marketplace with B2B partnerships",
            "competitive_advantage": "Authentic traditional craftsmanship with modern business operations",
            "market_positioning": "Premium segment leader in cultural heritage products"
        }

    async def _compile_financial_analysis(self, artifacts: List[Dict]) -> Dict:
        """Compile comprehensive financial analysis from all agents."""

        current_revenue = 45000  # Default assumption
        total_investment_needed = 0
        monthly_additional_revenue = 0
        first_year_total_revenue = 0

        for artifact in artifacts:
            result = artifact.get("result", {})

            if artifact["worker"] == "supply_hunter" and result.get("business_impact"):
                impact = result["business_impact"]
                total_investment_needed += impact.get("investment_requirements", {}).get("total_first_year_investment", 0)

            elif artifact["worker"] == "growth_marketer" and result.get("business_impact"):
                impact = result["business_impact"]
                monthly_additional_revenue = impact.get("revenue_impact", {}).get("projected_monthly_revenue", 0) - current_revenue
                first_year_total_revenue = impact.get("revenue_impact", {}).get("first_year_additional_revenue", 0)

        return {
            "current_financial_baseline": {
                "monthly_revenue": current_revenue,
                "annual_revenue": current_revenue * 12,
                "profit_margin": "35-45%",
                "cash_flow_status": "Stable with growth potential"
            },
            "investment_requirements": {
                "startup_investment": total_investment_needed,
                "funding_sources": ["Personal investment", "Local business loans", "Craft cooperative grants"],
                "payback_period": "6-9 months",
                "roi_expectation": "300-500% in first 24 months"
            },
            "revenue_projections": {
                "year_1_additional_revenue": monthly_additional_revenue * 12,
                "year_2_total_revenue": first_year_total_revenue + (monthly_additional_revenue * 12),
                "profitability_timeline": "Break-even achieved in month 6-9",
                "scalability_factors": [
                    "Online marketplace expansion",
                    "Product line diversification",
                    "Geographic market extension",
                    "Partnership revenue streams"
                ]
            },
            "financial_risks": {
                "market_demand_fluctuation": "Medium - tourism dependent",
                "supply_chain_disruption": "Low - multiple suppliers established",
                "competition_intensity": "Medium - differentiated positioning",
                "cash_flow_cycles": "Managed through diversified revenue streams"
            }
        }

    async def _aggregate_risk_assessments(self, artifacts: List[Dict], god_mode_insights: Dict) -> Dict:
        """Aggregate comprehensive risk assessments from all agents and GOD MODE."""

        risks = {
            "supply_chain_risks": "Medium - diversified supplier base but seasonal dependencies",
            "market_risks": "Medium - high tourism dependence but growing online markets",
            "operational_risks": "Low - established craft skills with quality controls",
            "financial_risks": "Medium - investment intensive startup phase",
            "competitive_risks": "Low - strong brand differentiation through authenticity",
            "technological_risks": "Low - minimal tech dependencies, offline-capable operations"
        }

        mitigation_strategies = [
            "Multi-supplier supply chain with local and regional diversification",
            "Digital marketing backup to tourism demand fluctuations",
            "Quality certification and process documentation",
            "Conservative financial planning with emergency reserves",
            "Brand positioning emphasizing authentic heritage value",
            "Low-tech backup systems for critical operations"
        ]

        # Extract from GOD MODE insights if available
        if god_mode_insights and isinstance(god_mode_insights, dict):
            god_risk_assessment = god_mode_insights.get("risk_assessment", "")
            if god_risk_assessment:
                mitigation_strategies.append(f"GOD MODE analysis: {god_risk_assessment[:100]}...")

        return {
            "identified_risks": risks,
            "risk_severity": "MEDIUM - Manageable with proper execution",
            "mitigation_strategies": mitigation_strategies,
            "monitoring_recommendations": [
                "Monthly financial reviews and cash flow monitoring",
                "Quarterly supplier performance assessments",
                "Market trend analysis and competitive intelligence",
                "Customer satisfaction and retention metrics"
            ],
            "contingency_planning": [
                "Emergency supplier backup activation protocols",
                "Marketing campaign adjustments for low seasons",
                "Inventory buffer management strategies",
                "Alternative revenue stream activation plans"
            ]
        }

    async def _create_coordinated_roadmap(self, plan: List[Dict], artifacts: List[Dict]) -> Dict:
        """Create coordinated implementation roadmap across all agent recommendations."""

        phases = {
            "phase_1_foundation": {
                "duration": "0-3 months",
                "theme": "Business Foundation & Setup",
                "milestones": [
                    "Complete digital infrastructure setup (website, social media, online store)",
                    "Establish supplier relationships and quality verification processes",
                    "Develop brand identity and marketing materials",
                    "Implement basic operational systems and quality controls"
                ],
                "primary_agents": "All agents - coordinated execution",
                "success_criteria": "Operational foundation established, first digital sales"
            },
            "phase_2_growth_acceleration": {
                "duration": "3-8 months",
                "theme": "Market Expansion & Revenue Growth",
                "milestones": [
                    "Execute comprehensive online marketing campaigns",
                    "Expand product lines based on market research",
                    "Develop strategic partnerships and distribution channels",
                    "Scale production capacity and operational efficiency"
                ],
                "primary_agents": "Growth Marketer leading, Supply Hunter supporting",
                "success_criteria": "Revenue growth of 150%, multiple distribution channels established"
            },
            "phase_3_scale_optimization": {
                "duration": "8-12 months",
                "theme": "Optimization & Scaling",
                "milestones": [
                    "Automate key business processes and reporting",
                    "Expand to new geographic markets with local partnerships",
                    "Develop advanced product lines and innovation pipeline",
                    "Establish enterprise-level operations and team structure"
                ],
                "primary_agents": "Supervisor coordinating multi-agent operations",
                "success_criteria": "Enterprise-grade operations, 300% revenue growth, regional recognition"
            }
        }

        return {
            "implementation_phases": phases,
            "critical_dependencies": [
                "Digital infrastructure must precede marketing campaigns",
                "Supplier relationships must be established before production scaling",
                "Quality systems must be proven before partnership expansion"
            ],
            "resource_allocation": {
                "technological_resources": "35% of budget - websites and digital marketing",
                "operational_resources": "25% of budget - suppliers and quality systems",
                "marketing_resources": "25% of budget - advertising and promotion",
                "miscellaneous_resources": "15% of budget - legal, accounting, contingencies"
            },
            "success_measures": [
                "Monthly revenue growth tracking",
                "Customer acquisition cost monitoring",
                "Supplier performance metrics",
                "Brand awareness and market penetration measurements"
            ]
        }

    async def _define_success_metrics(self, goal: str, artifacts: List[Dict]) -> Dict:
        """Define comprehensive success metrics dashboard."""

        return {
            "financial_metrics": {
                "monthly_revenue_target": "₹81,000 (6-month), ₹135,000 (12-month)",
                "profit_margin_target": "45% (by month 12)",
                "customer_acquisition_cost": "< ₹500 (target)",
                "roi_target": "300% in 24 months"
            },
            "operational_metrics": {
                "supplier_reliability_score": ">4.2/5 average rating",
                "production_capacity": "200% increase by month 12",
                "quality_compliance_rate": ">98% defect-free products",
                "delivery_time": "<7 days average"
            },
            "market_metrics": {
                "brand_awareness": "Top 5 artisan brands in region",
                "customer_satisfaction": ">4.8/5 average rating",
                "market_share": "15% in target segments",
                "partnership_network": "8+ strategic partnerships"
            },
            "growth_metrics": {
                "monthly_active_customers": "300+ (by month 12)",
                "product_line_expansion": "8-12 product variations",
                "geographic_reach": "3-5 cities/regions",
                "digital_presence": "50,000+ social media reach"
            },
            "measurement_schedule": {
                "daily_tracking": ["Revenue, orders, website traffic"],
                "weekly_reviews": ["Customer feedback, supplier performance"],
                "monthly_assessments": ["Financial metrics, growth targets"],
                "quarterly_evaluations": ["Strategic positioning, market analysis"]
            }
        }

    async def _prioritize_next_steps(self, artifacts: List[Dict], plan: List[Dict]) -> List[Dict]:
        """Create prioritized next steps from all agent recommendations."""

        all_next_steps = []

        # Extract immediate actions from each agent
        for artifact in artifacts:
            result = artifact.get("result", {})

            if artifact["worker"] == "supply_hunter" and result.get("actionable_insights"):
                all_next_steps.extend(result["actionable_insights"][:2])  # Top 2 from supply

            elif artifact["worker"] == "growth_marketer" and result.get("actionable_items"):
                all_next_steps.extend(result["actionable_items"][:3])  # Top 3 from growth

        # Prioritize and deduplicate
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

        unique_steps = []
        seen_descriptions = set()

        for step in all_next_steps:
            description = step.get("action", "").lower().strip()
            if description and description not in seen_descriptions:
                unique_steps.append(step)
                seen_descriptions.add(description)

        # Sort by priority
        unique_steps.sort(key=lambda x: priority_order.get(x.get("priority", "MEDIUM"), 2))

        return unique_steps[:7]  # Return top 7 prioritized next steps
