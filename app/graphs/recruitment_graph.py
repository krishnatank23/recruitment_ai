#recruitment grpah
from langgraph.graph import StateGraph
from app.graphs.state import RecruitmentState

from app.agents.jd_parser import jd_parser
from app.agents.resume_parser import resume_parser
from app.agents.semantic_matcher import semantic_matcher
from app.agents.job_fit_evaluator import job_fit_evaluator
from app.agents.ranking import ranking_agent
from app.agents.export_agent import export_agent


def build_recruitment_graph():
    graph = StateGraph(RecruitmentState)

    graph.add_node("jd_parser", jd_parser)
    graph.add_node("resume_parser", resume_parser)
    graph.add_node("semantic_matcher", semantic_matcher)
    graph.add_node("job_fit_evaluator", job_fit_evaluator)
    graph.add_node("ranking", ranking_agent)
    graph.add_node("export", export_agent)

    graph.set_entry_point("jd_parser")

    graph.add_edge("jd_parser", "resume_parser")
    graph.add_edge("resume_parser", "semantic_matcher")
    graph.add_edge("semantic_matcher", "job_fit_evaluator")
    graph.add_edge("job_fit_evaluator", "ranking")
    graph.add_edge("ranking", "export")

    return graph.compile()
