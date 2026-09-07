import pytest
import httpx
from app.main import app
from app.db.database import init_db


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_health_api():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_analyze_direct_url():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/analyze/url", json={"url": "https://www.wikipedia.org"})
        assert res.status_code == 200
        data = res.json()
        assert data["input_type"] == "URL"
        assert "risk_score" in data
        assert "detectors" in data


@pytest.mark.asyncio
async def test_analyze_direct_text():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/analyze/text", json={"text": "URGENT: Verify your bank password now!"})
        assert res.status_code == 200
        data = res.json()
        assert data["input_type"] == "TEXT"
        assert data["risk_score"] > 40
        assert "summary" in data and len(data["summary"]) > 0
        assert "why_suspicious" in data
        assert "recommended_actions" in data
        assert "multimodal_findings" in data


@pytest.mark.asyncio
async def test_history_and_get_by_id():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Create an analysis
        res1 = await client.post("/api/analyze/url", json={"url": "http://suspicious-test-login.xyz"})
        assert res1.status_code == 200
        analysis_id = res1.json()["analysis_id"]

        # Retrieve by id
        res2 = await client.get(f"/api/analysis/{analysis_id}")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["analysis_id"] == analysis_id
        assert "summary" in data2 and len(data2["summary"]) > 0
        assert "why_suspicious" in data2
        assert "recommended_actions" in data2
        assert "multimodal_findings" in data2

        # List history
        res3 = await client.get("/api/history?page=1&page_size=5")
        assert res3.status_code == 200
        assert res3.json()["total"] >= 1
