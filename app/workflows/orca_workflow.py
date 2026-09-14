from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent

from agents.planner import planner_agent
from agents.data_agents import (
    ResolveLocationAgent,
    OceanDataAgent,
    WeatherDataAgent,
    GeofenceDataAgent,
    RiskAssessmentAgent,
    RecheckAgent,
    ReviewGateAgent,
)
from agents.reasoning_agents import (
    ocean_reasoner,
    weather_reasoner,
    fishery_reasoner,
    safety_reasoner,
    peer_review_agent,
)
from agents.review_agent import review_agent
from agents.synthesis_agent import synthesis_agent


resolve_location_agent = ResolveLocationAgent(
    name="resolve_location",
    description="Resolve the location before data retrieval.",
)

data_collection_parallel = ParallelAgent(
    name="parallel_data_collection",
    description="Retrieve independent environmental and geospatial evidence concurrently.",
    sub_agents=[
        OceanDataAgent(
            name="ocean_data_collector",
            description="Collect Copernicus Marine point observations.",
        ),
        WeatherDataAgent(
            name="weather_data_collector",
            description="Collect current and forecast weather.",
        ),
        GeofenceDataAgent(
            name="geofence_data_collector",
            description="Check configured geospatial restrictions.",
        ),
    ],
)

specialist_parallel = ParallelAgent(
    name="parallel_specialist_reasoning",
    description="Run independent domain interpretations concurrently.",
    sub_agents=[
        ocean_reasoner,
        weather_reasoner,
        fishery_reasoner,
        safety_reasoner,
    ],
)

risk_agent = RiskAssessmentAgent(
    name="deterministic_risk_assessment",
    description="Calculate a deterministic marine risk score from retrieved evidence.",
)

review_loop = LoopAgent(
    name="evidence_review_loop",
    description="Iteratively review evidence and re-fetch only when another pass may help.",
    max_iterations=2,
    sub_agents=[
        peer_review_agent,
        review_agent,
        RecheckAgent(
            name="targeted_recheck",
            description="Re-fetch only domains identified by the quality reviewer.",
        ),
        ReviewGateAgent(
            name="review_exit_gate",
            description="Stops the review loop when evidence is sufficient or blocked.",
        ),
    ],
)


orca_workflow = SequentialAgent(
    name="orca_marine_workflow",
    description="Agentic marine-intelligence workflow with planning, parallel evidence collection, specialist collaboration, iterative review and synthesis.",
    sub_agents=[
        planner_agent,
        resolve_location_agent,
        data_collection_parallel,
        specialist_parallel,
        risk_agent,
        review_loop,
        synthesis_agent,
    ],
)
