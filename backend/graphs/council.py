"""
Council Graph Implementation - Multi-agent deliberation system
"""
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import asyncio
import uuid
from loguru import logger

from backend.graphs.council_blackboard import (
    CouncilBlackboard, CouncilNode, CouncilMove, DebateRound, 
    CouncilMetrics, MoveStatus
)


class CouncilGraph:
    """
    Council graph for running multi-agent deliberations
    Implements debate, critique, scoring, synthesis, and move generation
    """
    
    def __init__(self, llm_client: Any):
        self.llm = llm_client
        self.nodes: Dict[str, Callable] = {}
        self._setup_default_nodes()
        
    def _setup_default_nodes(self):
        """Setup default council nodes"""
        self.nodes = {
            "debate_node": self.debate_node,
            "critique_node": self.critique_node,
            "scoring_node": self.scoring_node,
            "synthesis_node": self.synthesis_node,
            "move_decomposition_node": self.move_decomposition_node,
            "tool_requirements_node": self.tool_requirements_node,
            "success_prediction_node": self.success_prediction_node,
            "kill_switch_node": self.kill_switch_node,
            "campaign_arc_generator_node": self.campaign_arc_generator_node
        }
        
    async def run_council(self, blackboard: CouncilBlackboard, include_campaign_arc: bool = False) -> CouncilBlackboard:
        """
        Run the full council deliberation process
        """
        try:
            logger.info(f"Starting council deliberation for workspace {blackboard.state['workspace_id']}")
            
            # Initialize council nodes
            await self._initialize_council_nodes(blackboard)
            
            # Run debate rounds
            for round_num in range(1, blackboard.state["max_rounds"] + 1):
                logger.info(f"Starting debate round {round_num}")
                
                # Check kill switch
                if blackboard.state["kill_switch_triggered"]:
                    logger.warning("Kill switch triggered, stopping deliberation")
                    break
                
                # Run debate
                await self.debate_node(blackboard, round_num)
                
                # Run critique
                await self.critique_node(blackboard, round_num)
                
                # Run scoring
                await self.scoring_node(blackboard, round_num)
                
                # Check consensus
                consensus_score = await self._check_consensus(blackboard)
                if consensus_score > 0.8:  # High consensus threshold
                    logger.info(f"High consensus achieved ({consensus_score:.2f}), ending debate")
                    break
            
            # Run synthesis
            await self.synthesis_node(blackboard)
            
            # Decompose into moves
            await self.move_decomposition_node(blackboard)
            
            # Refine with tool requirements
            await self.tool_requirements_node(blackboard)
            
            # Predict success
            await self.success_prediction_node(blackboard)
            
            # Filter via kill switch
            await self.kill_switch_node(blackboard)
            
            # Generate campaign arc if requested
            if include_campaign_arc and blackboard.state["target_icp"]:
                await self.campaign_arc_generator_node(blackboard)
            
            # Complete the council session
            blackboard.complete()
            
            logger.info("Council deliberation completed successfully")
            return blackboard
            
        except Exception as e:
            logger.error(f"Council deliberation failed: {e}")
            blackboard.add_error(f"Council execution error: {str(e)}")
            blackboard.complete()
            return blackboard
    
    async def _initialize_council_nodes(self, blackboard: CouncilBlackboard):
        """Initialize council nodes with roles and expertise"""
        nodes = [
            CouncilNode(
                name="strategist",
                role="Strategic Planning",
                expertise=["strategy", "planning", "market_analysis"],
                confidence=0.9
            ),
            CouncilNode(
                name="tactician",
                role="Tactical Execution",
                expertise=["execution", "operations", "logistics"],
                confidence=0.8
            ),
            CouncilNode(
                name="critic",
                role="Critical Analysis",
                expertise=["risk_assessment", "critical_thinking", "devil_advocate"],
                confidence=0.85
            ),
            CouncilNode(
                name="synthesizer",
                role="Synthesis & Integration",
                expertise=["integration", "synthesis", "holistic_thinking"],
                confidence=0.9
            ),
            CouncilNode(
                name="innovator",
                role="Innovation & Creativity",
                expertise=["innovation", "creative_thinking", "ideation"],
                confidence=0.8
            )
        ]
        
        for node in nodes:
            blackboard.add_council_node(node)
    
    async def debate_node(self, blackboard: CouncilBlackboard, round_num: int):
        """Run debate round among council nodes"""
        logger.info(f"Running debate round {round_num}")
        
        # Generate debate topic based on objective and previous rounds
        topic = f"How to achieve: {blackboard.state['objective']}"
        if round_num > 1:
            topic += f" (Building on round {round_num-1} insights)"
        
        # Collect arguments from each node
        arguments = {}
        participants = []
        
        for node in blackboard.state["council_nodes"]:
            try:
                # Generate argument using LLM
                prompt = f"""
                As {node.name} ({node.role}), debate the following topic:
                Topic: {topic}
                Context: {blackboard.state['details']}
                
                Provide your perspective and argument. Consider your expertise in: {', '.join(node.expertise)}
                
                Previous debate rounds:
                {self._format_previous_debates(blackboard.state['debate_history'])}
                
                Respond with a clear, concise argument (max 200 words).
                """
                
                response = await self.llm.generate_response(prompt)
                arguments[node.name] = response
                participants.append(node.name)
                
            except Exception as e:
                logger.error(f"Error getting argument from {node.name}: {e}")
                arguments[node.name] = f"Error: {str(e)}"
        
        # Calculate consensus score for this round
        consensus_score = await self._calculate_round_consensus(arguments)
        
        # Create debate round
        debate_round = DebateRound(
            round_number=round_num,
            topic=topic,
            participants=participants,
            arguments=arguments,
            consensus_score=consensus_score,
            outcome=f"Round {round_num} completed with {consensus_score:.2f} consensus"
        )
        
        blackboard.add_debate_round(debate_round)
    
    async def critique_node(self, blackboard: CouncilBlackboard, round_num: int):
        """Run critique of previous debate round"""
        logger.info(f"Running critique for round {round_num}")
        
        if not blackboard.state["debate_history"]:
            return
        
        latest_round = blackboard.state["debate_history"][-1]
        
        # Generate critiques
        critiques = {}
        for node_name, argument in latest_round.arguments.items():
            try:
                prompt = f"""
                Critically analyze this argument from {node_name}:
                Argument: {argument}
                
                Identify strengths, weaknesses, logical fallacies, and missing considerations.
                Provide constructive criticism (max 150 words).
                """
                
                critique = await self.llm.generate_response(prompt)
                critiques[node_name] = critique
                
            except Exception as e:
                logger.error(f"Error critiquing {node_name}: {e}")
                critiques[node_name] = f"Critique error: {str(e)}"
        
        # Store critiques in the latest round
        latest_round.arguments.update({f"{k}_critique": v for k, v in critiques.items()})
    
    async def scoring_node(self, blackboard: CouncilBlackboard, round_num: int):
        """Score arguments and positions"""
        logger.info(f"Running scoring for round {round_num}")
        
        if not blackboard.state["debate_history"]:
            return
        
        latest_round = blackboard.state["debate_history"][-1]
        
        # Score each argument
        scores = {}
        for node_name, argument in latest_round.arguments.items():
            if "_critique" in node_name:
                continue
                
            try:
                prompt = f"""
                Score this argument on a scale of 1-10:
                Argument: {argument}
                Context: {blackboard.state['objective']}
                
                Consider:
                - Relevance to objective
                - Logical coherence
                - Practical feasibility
                - Innovation
                
                Provide just the score (1-10).
                """
                
                response = await self.llm.generate_response(prompt)
                try:
                    score = float(response.strip())
                    scores[node_name] = max(1, min(10, score))  # Clamp between 1-10
                except ValueError:
                    scores[node_name] = 5.0  # Default score
                    
            except Exception as e:
                logger.error(f"Error scoring {node_name}: {e}")
                scores[node_name] = 5.0
        
        # Update node confidences based on scores
        for node in blackboard.state["council_nodes"]:
            if node.name in scores:
                node.confidence = scores[node.name] / 10.0
    
    async def synthesis_node(self, blackboard: CouncilBlackboard):
        """Synthesize all debate rounds into coherent insights"""
        logger.info("Running synthesis")
        
        if not blackboard.state["debate_history"]:
            return
        
        # Collect all arguments and insights
        all_arguments = []
        for round_data in blackboard.state["debate_history"]:
            for node_name, argument in round_data.arguments.items():
                if "_critique" not in node_name:
                    all_arguments.append(f"{node_name}: {argument}")
        
        try:
            prompt = f"""
            Synthesize these council deliberations into a coherent decree:
            
            Objective: {blackboard.state['objective']}
            Context: {blackboard.state['details']}
            
            Council Arguments:
            {' '.join(all_arguments)}
            
            Provide:
            1. A clear decree (final decision)
            2. Key insights from the debate
            3. Consensus areas
            4. Points of contention
            5. Recommended approach
            
            Keep the decree concise but comprehensive.
            """
            
            synthesis = await self.llm.generate_response(prompt)
            blackboard.set_decree(synthesis)
            
            # Generate consensus metrics
            await self._generate_consensus_metrics(blackboard)
            
        except Exception as e:
            logger.error(f"Error in synthesis: {e}")
            blackboard.add_error(f"Synthesis error: {str(e)}")
    
    async def move_decomposition_node(self, blackboard: CouncilBlackboard):
        """Decompose the decree into actionable moves"""
        logger.info("Running move decomposition")
        
        if not blackboard.state["decree"]:
            return
        
        try:
            prompt = f"""
            Decompose this decree into specific, actionable moves:
            
            Decree: {blackboard.state['decree']}
            Objective: {blackboard.state['objective']}
            
            For each move, provide:
            1. Clear name
            2. Detailed description
            3. Estimated difficulty (1-10)
            4. Expected impact (1-10)
            5. Dependencies
            
            Format as JSON array of moves.
            """
            
            response = await self.llm.generate_response(prompt)
            
            # Parse moves (simplified - in production would use proper JSON parsing)
            moves_text = response.split("Move")[1:]  # Simple parsing
            
            for i, move_text in enumerate(moves_text):
                if move_text.strip():
                    move = CouncilMove(
                        id=str(uuid.uuid4()),
                        name=f"Move {i+1}",
                        description=move_text.strip()[:200],  # Truncate for simplicity
                        proposed_by="council_synthesis"
                    )
                    blackboard.propose_move(move)
            
        except Exception as e:
            logger.error(f"Error in move decomposition: {e}")
            blackboard.add_error(f"Move decomposition error: {str(e)}")
    
    async def tool_requirements_node(self, blackboard: CouncilBlackboard):
        """Refine moves with tool requirements"""
        logger.info("Running tool requirements refinement")
        
        refined_moves = []
        for move in blackboard.state["proposed_moves"]:
            try:
                prompt = f"""
                Identify tool requirements for this move:
                
                Move: {move.name}
                Description: {move.description}
                
                What tools, resources, or capabilities are needed?
                Consider software, hardware, personnel, data, etc.
                
                List as comma-separated items.
                """
                
                response = await self.llm.generate_response(prompt)
                tools = [tool.strip() for tool in response.split(",") if tool.strip()]
                
                # Create refined move
                refined_move = CouncilMove(
                    id=move.id,
                    name=move.name,
                    description=move.description,
                    status=MoveStatus.REFINED,
                    tool_requirements=tools,
                    muse_prompt=f"Execute {move.name}: {move.description}",
                    proposed_by=move.proposed_by
                )
                
                refined_moves.append(refined_move)
                
            except Exception as e:
                logger.error(f"Error refining move {move.id}: {e}")
                refined_moves.append(move)  # Keep original move
        
        # Update blackboard with refined moves
        blackboard.state["refined_moves"] = refined_moves
    
    async def success_prediction_node(self, blackboard: CouncilBlackboard):
        """Predict success probability for each move"""
        logger.info("Running success prediction")
        
        for move in blackboard.state["refined_moves"]:
            try:
                prompt = f"""
                Predict success probability for this move:
                
                Move: {move.name}
                Description: {move.description}
                Tools required: {', '.join(move.tool_requirements)}
                
                Consider:
                - Technical feasibility
                - Resource availability
                - Market conditions
                - Risk factors
                
                Provide success probability (0-100) and risk score (0-100).
                Format: "SUCCESS: X, RISK: Y"
                """
                
                response = await self.llm.generate_response(prompt)
                
                # Parse response
                try:
                    if "SUCCESS:" in response and "RISK:" in response:
                        parts = response.split(",")
                        success_part = parts[0].split("SUCCESS:")[1].strip()
                        risk_part = parts[1].split("RISK:")[1].strip()
                        
                        move.success_prediction = float(success_part) / 100.0
                        move.risk_score = float(risk_part) / 100.0
                except:
                    move.success_prediction = 0.5
                    move.risk_score = 0.5
                
            except Exception as e:
                logger.error(f"Error predicting success for {move.id}: {e}")
                move.success_prediction = 0.5
                move.risk_score = 0.5
    
    async def kill_switch_node(self, blackboard: CouncilBlackboard):
        """Apply kill switch filters"""
        logger.info("Running kill switch filter")
        
        approved_moves = []
        discarded_moves = []
        
        for move in blackboard.state["refined_moves"]:
            # Apply filters
            if (move.success_prediction >= 0.3 and  # Minimum success probability
                move.risk_score <= 0.8 and          # Maximum acceptable risk
                len(move.tool_requirements) <= 10):  # Reasonable tool requirements
                
                move.status = MoveStatus.APPROVED
                approved_moves.append(move)
            else:
                move.status = MoveStatus.DISCARDED
                discarded_moves.append(move)
        
        blackboard.state["approved_moves"] = approved_moves
        blackboard.state["discarded_moves"] = discarded_moves
    
    async def campaign_arc_generator_node(self, blackboard: CouncilBlackboard):
        """Generate 90-day campaign arc"""
        logger.info("Generating campaign arc")
        
        try:
            prompt = f"""
            Generate a 90-day campaign arc for:
            
            Objective: {blackboard.state['objective']}
            Target ICP: {blackboard.state['target_icp']}
            Approved Moves: {len(blackboard.state['approved_moves'])}
            
            Create a structured campaign with:
            1. Campaign title
            2. 90-day timeline with phases
            3. Key milestones
            4. Resource allocation
            5. Success metrics
            
            Format as JSON.
            """
            
            response = await self.llm.generate_response(prompt)
            blackboard.state["campaign_arc"] = {
                "title": f"Campaign for {blackboard.state['objective']}",
                "arc_data": response,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating campaign arc: {e}")
            blackboard.add_error(f"Campaign arc generation error: {str(e)}")
    
    async def _check_consensus(self, blackboard: CouncilBlackboard) -> float:
        """Check overall consensus score"""
        if not blackboard.state["debate_history"]:
            return 0.0
        
        latest_round = blackboard.state["debate_history"][-1]
        return latest_round.consensus_score
    
    async def _calculate_round_consensus(self, arguments: Dict[str, str]) -> float:
        """Calculate consensus score for a round"""
        if len(arguments) < 2:
            return 1.0
        
        # Simple consensus calculation based on argument similarity
        # In production, would use more sophisticated NLP
        try:
            prompt = f"""
            Calculate consensus score (0-1) for these arguments:
            
            {arguments}
            
            Consider agreement, alignment, and complementary nature.
            Return just the score (0-1).
            """
            
            response = await self.llm.generate_response(prompt)
            try:
                return float(response.strip())
            except ValueError:
                return 0.5  # Default consensus
                
        except Exception:
            return 0.5  # Default on error
    
    async def _generate_consensus_metrics(self, blackboard: CouncilBlackboard):
        """Generate comprehensive consensus metrics"""
        if not blackboard.state["debate_history"]:
            return
        
        # Calculate metrics
        total_rounds = len(blackboard.state["debate_history"])
        avg_consensus = sum(r.consensus_score for r in blackboard.state["debate_history"]) / total_rounds
        participation_rate = len(blackboard.state["council_nodes"]) / 5.0  # Assuming 5 is max nodes
        
        metrics = CouncilMetrics(
            consensus_alignment=avg_consensus,
            debate_quality=min(1.0, avg_consensus + 0.1),  # Slightly optimistic
            decision_confidence=avg_consensus,
            participation_rate=participation_rate,
            expert_agreement=avg_consensus
        )
        
        blackboard.set_consensus_metrics(metrics)
    
    def _format_previous_debates(self, debate_history: List[DebateRound]) -> str:
        """Format previous debates for context"""
        if not debate_history:
            return "No previous rounds"
        
        formatted = []
        for round_data in debate_history[-2:]:  # Last 2 rounds
            formatted.append(f"Round {round_data.round_number}: {round_data.topic}")
            for node_name, argument in round_data.arguments.items():
                if "_critique" not in node_name:
                    formatted.append(f"  {node_name}: {argument[:100]}...")
        
        return "\n".join(formatted)
