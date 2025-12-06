# Newtype Cloud Server 설정 가이드

## 개요

Newtype 모듈의 백엔드는 클라우드 서버(168.107.21.4)에서 실행됩니다.
기존 MCP 서버(`/home/ubuntu/mcp/server_http.py`)에 Newtype 엔드포인트를 추가하는 방식입니다.

## 서버 정보

- **Host**: 168.107.21.4
- **Port**: 8000
- **Base URL**: http://168.107.21.4:8000
- **Python 환경**: /home/ubuntu/venv

## 파일 구조

```
/home/ubuntu/mcp/
├── server_http.py      # 메인 서버 (Newtype 엔드포인트 포함)
├── groq_api.py         # Groq API 클라이언트
└── ...
```

## 설치 방법

### 1. Groq 패키지 설치

```bash
ssh ubuntu@168.107.21.4
source /home/ubuntu/venv/bin/activate
pip install groq
```

### 2. groq_api.py 배포

```bash
# 로컬에서 클라우드로 복사
scp -i ~/.ssh/cloud_key cloud/groq_api.py ubuntu@168.107.21.4:/home/ubuntu/mcp/
```

### 3. server_http.py 수정

`server_endpoints.py` 파일의 내용을 참고하여 기존 server_http.py에 추가:

```python
# Import 추가
from groq_api import groq_manager

# Pydantic 모델 추가
class NewtypeAnalyzeRequest(BaseModel):
    messages: list

class NewtypeAnalyzeResponse(BaseModel):
    mood: str
    intensity: int
    is_highlight: bool
    scene_summary: str = ""
    error: Optional[str] = None

# 엔드포인트 추가
@app.post("/api/newtype/configure")
async def configure_newtype(api_key: str):
    groq_manager.set_api_key(api_key)
    return {"success": True, "configured": groq_manager.is_configured()}

@app.get("/api/newtype/status")
async def newtype_status():
    return {
        "configured": groq_manager.is_configured(),
        "model": "llama-3.3-70b-versatile"
    }

@app.post("/api/newtype/analyze", response_model=NewtypeAnalyzeResponse)
async def newtype_analyze(request: NewtypeAnalyzeRequest):
    result = groq_manager.analyze_atmosphere(request.messages)
    return NewtypeAnalyzeResponse(**result)
```

### 4. Groq API 키 설정

```bash
# 환경 변수로 설정 (권장)
export GROQ_API_KEY=your_api_key_here

# 또는 서버 실행 시
GROQ_API_KEY=xxx uvicorn server_http:app --host 0.0.0.0 --port 8000
```

### 5. 서버 재시작

```bash
ssh ubuntu@168.107.21.4
pkill -9 -f uvicorn
cd /home/ubuntu/mcp
nohup /home/ubuntu/venv/bin/uvicorn server_http:app --host 0.0.0.0 --port 8000 > /tmp/mcp.log 2>&1 &
```

## API 엔드포인트

### GET /api/newtype/status

Newtype 서비스 상태 확인

**Response:**
```json
{
  "configured": true,
  "model": "llama-3.3-70b-versatile"
}
```

### POST /api/newtype/configure

Groq API 키 설정

**Request:**
```
?api_key=your_groq_api_key
```

**Response:**
```json
{
  "success": true,
  "configured": true
}
```

### POST /api/newtype/analyze

RP 채팅 분위기 분석

**Request:**
```json
{
  "messages": [
    {
      "speaker": "Eleanor",
      "content": "칼을 뽑아들며 적을 노려본다.",
      "timestamp": 1701936000000,
      "actorId": "aF4H3juUSLgnJPkW"
    },
    {
      "speaker": "Marcus",
      "content": "방패를 들어 엘레노어를 보호하며 외친다. '내가 막겠다!'",
      "timestamp": 1701936060000,
      "actorId": "bG5I4kvVTMhoKQlX"
    }
  ]
}
```

**Response:**
```json
{
  "mood": "combat",
  "intensity": 85,
  "is_highlight": true,
  "scene_summary": "엘레노어와 마커스가 적과 대치하며 전투가 시작되려 한다. 마커스가 엘레노어를 보호하며 방패를 들어 올린다."
}
```

## 분위기 카테고리

| 카테고리 | 설명 |
|---------|------|
| combat | 전투, 액션, 긴장된 대치 |
| romance | 로맨스, 친밀한 순간 |
| drama | 감정적 장면, 갈등, 슬픔 |
| comedy | 유머, 가벼운 장면 |
| mystery | 미스터리, 조사, 긴장 |
| celebration | 축제, 승리, 기쁨 |
| neutral | 일상, 특별하지 않음 |

## 하이라이트 기준

- intensity >= 70 이상
- is_highlight = true
- 다음과 같은 장면:
  - 극적인 전투 장면
  - 감정적으로 강렬한 순간 (고백, 이별, 재회)
  - 중요한 스토리 전환점
  - 시각적으로 인상적인 장면 묘사

## Groq API 정보

- **모델**: llama-3.3-70b-versatile
- **무료 티어**: 30 req/min, 14,400 req/day
- **API 키 발급**: https://console.groq.com

## 테스트

```bash
# 상태 확인
curl http://168.107.21.4:8000/api/newtype/status

# 분석 테스트
curl -X POST http://168.107.21.4:8000/api/newtype/analyze \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"speaker": "Test", "content": "테스트 메시지입니다."}]}'
```

## 로그 확인

```bash
ssh ubuntu@168.107.21.4
tail -f /tmp/mcp.log
```

## 문제 해결

### Groq API 미설정
```
{"error": "Groq API not configured"}
```
→ GROQ_API_KEY 환경 변수 설정 또는 /api/newtype/configure 호출

### 서버 연결 불가
1. 서버 실행 확인: `pgrep -f uvicorn`
2. 포트 확인: `netstat -tlnp | grep 8000`
3. 방화벽 확인: `sudo ufw status`

---

*Last Updated: 2025-12-07*
