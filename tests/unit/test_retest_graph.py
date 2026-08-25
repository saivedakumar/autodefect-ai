from unittest.mock import patch

from app.agents import retest_graph


def test_llm_cannot_override_a_real_pytest_failure():
    with patch(
        "app.agents.retest_graph.ask_json",
        return_value={"passed": True, "summary": "looks fine to me"},
    ):
        state = retest_graph.llm_summarize({"report": "1 failed", "passed": False})
    assert state["passed"] is False


def test_llm_summary_is_recorded_when_tests_passed():
    with patch(
        "app.agents.retest_graph.ask_json",
        return_value={"passed": True, "summary": "all good"},
    ):
        state = retest_graph.llm_summarize({"report": "3 passed", "passed": True})
    assert state["passed"] is True
    assert state["ai_summary"] == "all good"
