from unittest.mock import patch

from langgraph.graph import END

from app.agents import review_graph


def test_llm_review_maps_approve_to_verdict():
    with patch(
        "app.agents.review_graph.ask_json",
        return_value={"approve": True, "summary": "looks good", "comments": []},
    ):
        state = review_graph.llm_review({"diff": "diff", "issue_context": "ctx"})
    assert state["verdict"] == "approve"


def test_llm_review_maps_rejection_to_request_changes():
    with patch(
        "app.agents.review_graph.ask_json",
        return_value={"approve": False, "summary": "needs work", "comments": ["fix x"]},
    ):
        state = review_graph.llm_review({"diff": "diff", "issue_context": "ctx"})
    assert state["verdict"] == "request_changes"
    assert "fix x" in state["comments"]


def test_route_after_review_merges_on_approve():
    assert review_graph.route_after_review({"verdict": "approve"}) == "merge_pr"


def test_route_after_review_ends_on_request_changes():
    assert review_graph.route_after_review({"verdict": "request_changes"}) == END
