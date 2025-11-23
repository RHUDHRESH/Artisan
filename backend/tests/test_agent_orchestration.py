"""
Tests for agent orchestration system.
"""

import pytest
from backend.orchestration.agent_factory import (
    AgentFactory,
    AgentLibrary,
    AgentTemplate,
    AgentRole,
    AgentCapability
)


@pytest.mark.unit
def test_agent_factory_initialization():
    """Test agent factory initialization."""
    factory = AgentFactory()
    assert factory is not None


@pytest.mark.unit
def test_agent_template_creation(sample_agent_spec):
    """Test creating agent template."""
    template = AgentTemplate(
        name=sample_agent_spec["name"],
        role=AgentRole(sample_agent_spec["role"]),
        capabilities=[AgentCapability(cap) for cap in sample_agent_spec["capabilities"]],
        description=sample_agent_spec["description"],
        system_message=sample_agent_spec["system_message"]
    )

    assert template.name == "test_researcher"
    assert template.role == AgentRole.RESEARCH
    assert AgentCapability.WEB_SEARCH in template.capabilities


@pytest.mark.unit
def test_agent_library_has_agents():
    """Test that agent library contains agents."""
    # Check that library has expected agents
    assert hasattr(AgentLibrary, 'WEB_RESEARCHER')
    assert hasattr(AgentLibrary, 'MARKET_RESEARCHER')
    assert hasattr(AgentLibrary, 'CONTENT_WRITER')


@pytest.mark.unit
def test_agent_role_enum():
    """Test agent role enumeration."""
    assert AgentRole.RESEARCH.value == "research"
    assert AgentRole.ANALYSIS.value == "analysis"
    assert AgentRole.CONTENT.value == "content"


@pytest.mark.unit
def test_agent_capability_enum():
    """Test agent capability enumeration."""
    assert AgentCapability.WEB_SEARCH.value == "web_search"
    assert AgentCapability.DATA_ANALYSIS.value == "data_analysis"
    assert AgentCapability.CONTENT_GENERATION.value == "content_generation"


@pytest.mark.unit
def test_create_agent_from_template(sample_agent_spec):
    """Test creating an agent from a template."""
    factory = AgentFactory()

    # Create a custom agent
    agent_config = factory.create_agent(
        name=sample_agent_spec["name"],
        role=sample_agent_spec["role"],
        capabilities=sample_agent_spec["capabilities"],
        description=sample_agent_spec["description"]
    )

    assert agent_config is not None
    assert agent_config.get("name") == "test_researcher"


@pytest.mark.unit
def test_agent_library_categories():
    """Test that agent library has all categories."""
    # Check different categories exist
    research_agents = [
        AgentLibrary.WEB_RESEARCHER,
        AgentLibrary.MARKET_RESEARCHER,
        AgentLibrary.COMPETITIVE_ANALYST
    ]

    for agent in research_agents:
        assert agent is not None
        assert isinstance(agent, str)

    content_agents = [
        AgentLibrary.CONTENT_WRITER,
        AgentLibrary.SOCIAL_MEDIA_MANAGER,
        AgentLibrary.EMAIL_MARKETER
    ]

    for agent in content_agents:
        assert agent is not None
        assert isinstance(agent, str)


@pytest.mark.unit
def test_agent_count():
    """Test that agent library has 100+ agents."""
    # Count all agents in the library
    agent_count = 0

    for attr_name in dir(AgentLibrary):
        if not attr_name.startswith('_'):
            attr = getattr(AgentLibrary, attr_name)
            if isinstance(attr, str):
                agent_count += 1

    # We should have at least 100 agents
    assert agent_count >= 100, f"Expected at least 100 agents, found {agent_count}"
