"""
Newtype - RP Atmosphere Detection Server
황제서버 (140.245.68.52)에서 실행
Ollama를 사용하여 채팅 분위기 감지
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from collections import deque
import httpx
import json

app = FastAPI(title="Newtype Detection Server")

# CORS 설정 (FVTT에서 호출 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama 설정
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"

# 추후 n8n 워크플로우 호출용 (현재는 비활성)
N8N_WEBHOOK_URL = None  # 예: "http://localhost:5678/webhook/newtype/generate"

# 로그 저장 (최대 100개)
LOG_BUFFER = deque(maxlen=100)


def add_log(server: str, message: str):
    """로그 추가"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    LOG_BUFFER.append({
        "time": timestamp,
        "server": server,
        "message": message
    })
    print(f"[{server}] {message}")


# ============================================================================
# Pydantic Models
# ============================================================================

class Message(BaseModel):
    speaker: str
    content: str
    timestamp: Optional[int] = None
    actorId: Optional[str] = None

class AnalyzeRequest(BaseModel):
    messages: list[Message]

class AnalyzeResponse(BaseModel):
    mood: str
    intensity: int
    is_highlight: bool
    scene_summary: str = ""
    error: Optional[str] = None


# ============================================================================
# Ollama 분석 함수
# ============================================================================

async def analyze_with_ollama(messages: list[Message]) -> dict:
    """Ollama로 채팅 분위기 분석"""

    formatted = "\n".join([
        f"{m.speaker}: {m.content}" for m in messages
    ])

    prompt = f"""당신은 TRPG RP 분위기 분석가입니다.
다음 채팅 로그를 읽고 현재 장면의 분위기를 파악하세요.

## 분위기 카테고리
- combat: 전투, 액션, 긴장된 대치
- romance: 로맨스, 친밀한 순간
- drama: 감정적 장면, 갈등, 슬픔
- comedy: 유머, 가벼운 장면
- mystery: 미스터리, 조사, 긴장
- celebration: 축제, 승리, 기쁨
- neutral: 일상, 특별하지 않음

## 하이라이트 판단 기준
- 극적인 전투 장면
- 감정적으로 강렬한 순간 (고백, 이별, 재회)
- 중요한 스토리 전환점
- 시각적으로 인상적인 장면 묘사

## 채팅 로그
{formatted}

## 응답 형식 (JSON만 출력, 다른 텍스트 없이)
{{"mood": "카테고리", "intensity": 0-100, "is_highlight": true/false, "scene_summary": "장면 요약 (한국어, 2-3문장)"}}"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "format": "json"
                }
            )
            response.raise_for_status()

            result = response.json()
            content = result.get("message", {}).get("content", "{}")

            # JSON 파싱
            parsed = json.loads(content)
            return parsed

    except json.JSONDecodeError as e:
        add_log("Ollama", f"JSON 파싱 오류: {e}")
        return {
            "mood": "neutral",
            "intensity": 0,
            "is_highlight": False,
            "scene_summary": ""
        }
    except Exception as e:
        add_log("Ollama", f"오류: {e}")
        return {
            "mood": "neutral",
            "intensity": 0,
            "is_highlight": False,
            "scene_summary": "",
            "error": str(e)
        }


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {"service": "Newtype Detection Server", "status": "running"}

@app.get("/api/newtype/status")
async def status():
    """서버 상태 확인"""
    return {
        "status": "running",
        "ollama_url": OLLAMA_URL,
        "model": OLLAMA_MODEL,
        "n8n_configured": N8N_WEBHOOK_URL is not None
    }

@app.post("/api/newtype/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """RP 채팅 분위기 분석"""

    result = await analyze_with_ollama(request.messages)

    # 로그 출력
    mood = result.get("mood", "neutral")
    intensity = result.get("intensity", 0)
    is_highlight = result.get("is_highlight", False)
    summary = result.get("scene_summary", "")

    add_log("Newtype", f"분위기 감지! ({mood}, 강도: {intensity}%, 하이라이트: {is_highlight})")
    add_log("Newtype", f"장면 요약: {summary}")

    # 하이라이트 감지 시 n8n 호출 (추후 활성화)
    if is_highlight and intensity >= 70 and N8N_WEBHOOK_URL:
        add_log("Newtype", "하이라이트 감지! n8n 워크플로우 호출...")
        # TODO: n8n 웹훅 호출
        # async with httpx.AsyncClient() as client:
        #     await client.post(N8N_WEBHOOK_URL, json=result)

    return AnalyzeResponse(**result)


# ============================================================================
# 로그 API
# ============================================================================

@app.get("/api/logs")
async def get_logs():
    """로그 목록 반환"""
    return list(LOG_BUFFER)

@app.get("/logs", response_class=HTMLResponse)
async def logs_page():
    """로그 뷰어 페이지"""
    html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newtype Server Logs</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Consolas', 'Monaco', monospace;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
            min-height: 100vh;
        }
        h1 {
            color: #7c3aed;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        .status {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .status-item {
            background: #2a2a4a;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.9rem;
        }
        .status-item.online { border-left: 3px solid #22c55e; }
        .status-item.offline { border-left: 3px solid #ef4444; }
        .log-container {
            background: #0f0f1a;
            border-radius: 8px;
            padding: 16px;
            max-height: 70vh;
            overflow-y: auto;
        }
        .log-entry {
            padding: 8px 0;
            border-bottom: 1px solid #2a2a4a;
            display: flex;
            gap: 12px;
            font-size: 0.9rem;
        }
        .log-entry:last-child { border-bottom: none; }
        .log-time {
            color: #666;
            min-width: 70px;
        }
        .log-server {
            min-width: 80px;
            font-weight: bold;
        }
        .log-server.Newtype { color: #7c3aed; }
        .log-server.Ollama { color: #22c55e; }
        .log-server.n8n { color: #f97316; }
        .log-server.System { color: #3b82f6; }
        .log-message { color: #ccc; }
        .empty { color: #666; text-align: center; padding: 40px; }
        .refresh-info {
            text-align: right;
            color: #666;
            font-size: 0.8rem;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <h1>Newtype Server Logs</h1>

    <div class="status" id="status">
        <div class="status-item online">Newtype: 8000</div>
        <div class="status-item online">Ollama: 11434</div>
        <div class="status-item online">n8n: 5678</div>
        <div class="status-item online">Filebrowser: 8080</div>
    </div>

    <div class="log-container" id="logs">
        <div class="empty">로그를 불러오는 중...</div>
    </div>

    <div class="refresh-info">3초마다 자동 새로고침</div>

    <script>
        async function fetchLogs() {
            try {
                const res = await fetch('/api/logs');
                const logs = await res.json();

                const container = document.getElementById('logs');

                if (logs.length === 0) {
                    container.innerHTML = '<div class="empty">아직 로그가 없습니다</div>';
                    return;
                }

                container.innerHTML = logs.reverse().map(log => `
                    <div class="log-entry">
                        <span class="log-time">${log.time}</span>
                        <span class="log-server ${log.server}">${log.server}</span>
                        <span class="log-message">${log.message}</span>
                    </div>
                `).join('');

            } catch (e) {
                console.error('Failed to fetch logs:', e);
            }
        }

        fetchLogs();
        setInterval(fetchLogs, 3000);
    </script>
</body>
</html>
"""
    return html


# ============================================================================
# 서버 실행
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    add_log("System", "Newtype Detection Server 시작")
    uvicorn.run(app, host="0.0.0.0", port=8000)
