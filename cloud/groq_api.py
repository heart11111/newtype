"""Groq API Manager for Newtype RP Analysis"""
import os
import json

try:
    from groq import Groq
except ImportError:
    Groq = None

class GroqAPIManager:
    def __init__(self):
        self.api_key = os.environ.get('GROQ_API_KEY')
        self.client = None
        if self.api_key and Groq:
            self.client = Groq(api_key=self.api_key)

    def set_api_key(self, key: str):
        self.api_key = key
        if Groq:
            self.client = Groq(api_key=key)

    def is_configured(self) -> bool:
        return self.client is not None

    def analyze_atmosphere(self, messages: list) -> dict:
        """RP 채팅 분석하여 분위기 반환"""
        if not self.client:
            return {
                "mood": "neutral",
                "intensity": 0,
                "is_highlight": False,
                "scene_summary": "",
                "error": "Groq API not configured"
            }

        formatted = "\n".join([
            f"{m.get('speaker', 'Unknown')}: {m.get('content', '')}"
            for m in messages
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
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )

            result_text = response.choices[0].message.content.strip()

            # JSON 파싱 시도
            # 마크다운 코드 블록 제거
            if result_text.startswith('```'):
                result_text = result_text.split('\n', 1)[1]
                result_text = result_text.rsplit('```', 1)[0]

            return json.loads(result_text)

        except json.JSONDecodeError as e:
            print(f"[Groq] JSON parse error: {e}")
            return {
                "mood": "neutral",
                "intensity": 0,
                "is_highlight": False,
                "scene_summary": ""
            }
        except Exception as e:
            print(f"[Groq] API error: {e}")
            return {
                "mood": "neutral",
                "intensity": 0,
                "is_highlight": False,
                "scene_summary": "",
                "error": str(e)
            }

# Global instance
groq_manager = GroqAPIManager()
