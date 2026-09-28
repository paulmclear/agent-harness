from workflows.dev_loop.graph import build_graph


def test_graph_compiles():
    assert build_graph() is not None


def test_debug_run_without_model_calls():
    result = build_graph().invoke({"debug": True})

    assert result["debug"] is True
