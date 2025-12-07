# 황제서버 (Oracle Cloud)

## 서버 정보

| 항목 | 값 |
|------|-----|
| 서버 IP | 140.245.68.52 |
| OS | Ubuntu 24.04 (ARM64) |
| 스펙 | 4 OCPU / 24GB RAM |

## 서비스 목록

| 서비스 | 포트 | URL |
|--------|------|-----|
| Newtype API | 8000 | http://140.245.68.52:8000 |
| Newtype 로그 | 8000 | http://140.245.68.52:8000/logs |
| n8n | 5678 | http://140.245.68.52:5678 |
| Ollama | 11434 | http://140.245.68.52:11434 |
| Filebrowser | 8080 | http://140.245.68.52:8080 |

---

## Filebrowser (파일 매니저)

### 접속 정보
- **URL**: http://140.245.68.52:8080
- **ID**: `admin`

### 파일 저장 경로
- 서버 내 경로: `/srv/files`

---

## Ollama (AI 모델)

| 항목 | 값 |
|------|-----|
| 설치된 모델 | llama3.2 (3B) |

## API 엔드포인트

### Base URL
```
http://140.245.68.52:11434
```

### n8n 내부에서 호출 시
```
http://host.docker.internal:11434
```

---

## API 호출 예시

### 1. 채팅 완성 (Chat Completion)
```bash
curl http://140.245.68.52:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {"role": "user", "content": "안녕하세요"}
  ],
  "stream": false
}'
```

### 2. 텍스트 생성 (Generate)
```bash
curl http://140.245.68.52:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "한국의 수도는?",
  "stream": false
}'
```

### 3. 모델 목록 조회
```bash
curl http://140.245.68.52:11434/api/tags
```

### 4. 모델 정보 조회
```bash
curl http://140.245.68.52:11434/api/show -d '{
  "name": "llama3.2"
}'
```

---

## JavaScript/TypeScript 호출 예시

```javascript
// 채팅 API 호출
async function chat(message) {
  const response = await fetch('http://140.245.68.52:11434/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'llama3.2',
      messages: [{ role: 'user', content: message }],
      stream: false
    })
  });
  const data = await response.json();
  return data.message.content;
}

// 사용 예시
const answer = await chat('안녕하세요');
console.log(answer);
```

### 스트리밍 응답 처리
```javascript
async function chatStream(message, onChunk) {
  const response = await fetch('http://140.245.68.52:11434/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'llama3.2',
      messages: [{ role: 'user', content: message }],
      stream: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n').filter(line => line.trim());

    for (const line of lines) {
      const json = JSON.parse(line);
      if (json.message?.content) {
        onChunk(json.message.content);
      }
    }
  }
}

// 사용 예시
await chatStream('이야기 해줘', (text) => {
  process.stdout.write(text);
});
```

---

## n8n에서 Ollama 노드 설정

1. **Ollama 노드** 추가
2. **Credentials** 설정:
   - Base URL: `http://host.docker.internal:11434`
3. **Model**: `llama3.2`

---

## 추가 모델 설치

SSH 접속 후:
```bash
# 다른 모델 설치 예시
ollama pull mistral
ollama pull codellama
ollama pull gemma2

# 설치된 모델 확인
ollama list
```

---

## 서버 관리 명령어

```bash
# Ollama 서비스 상태 확인
sudo systemctl status ollama

# Ollama 재시작
sudo systemctl restart ollama

# n8n 컨테이너 상태 확인
sudo docker ps

# n8n 로그 확인
sudo docker logs n8n

# n8n 재시작
sudo docker restart n8n
```
