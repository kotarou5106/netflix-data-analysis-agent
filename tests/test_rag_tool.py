from src.tools.rag_tool import search_knowledge
from src.tools import rag_tool


def test_churn_rate_recalls_metric_definitions():
    results = search_knowledge("流失率")

    assert results
    assert results[0]["source"] == "metric_definitions.md"


def test_correlation_not_causation_recalls_churn_guide():
    results = search_knowledge("相关性不等于因果性")

    assert results
    assert results[0]["source"] == "churn_analysis_guide.md"


def test_heavy_users_recalls_segmentation_guide():
    results = search_knowledge("重度用户")

    assert results
    assert results[0]["source"] == "user_segmentation_guide.md"


def test_top_k_limits_results():
    results = search_knowledge("用户 分析 指标", top_k=2)

    assert len(results) <= 2


def test_unknown_query_does_not_error():
    results = search_knowledge("完全不存在的火星套餐字段", top_k=3)

    assert isinstance(results, list)


def test_chinese_churn_subscription_query_recalls_relevant_docs():
    results = search_knowledge("分析不同订阅类型的流失率", top_k=3)

    sources = {result["source"] for result in results}
    assert "churn_analysis_guide.md" in sources
    assert "metric_definitions.md" in sources


def test_embedding_unavailable_falls_back_to_keyword_search(monkeypatch):
    monkeypatch.setattr(rag_tool, "_embedding_search", lambda query, chunks: None)

    results = search_knowledge("分析不同订阅类型的流失率", top_k=3)

    sources = {result["source"] for result in results}
    assert "churn_analysis_guide.md" in sources
    assert "metric_definitions.md" in sources


def test_top_k_still_applies_with_rag_search():
    results = search_knowledge("分析不同订阅类型的流失率", top_k=1)

    assert len(results) <= 1
