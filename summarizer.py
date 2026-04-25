# -*- coding: utf-8 -*-
"""주식 데이터 및 뉴스를 바탕으로 Gemini를 통해 시황을 분석, 요약합니다."""
import logging
import re
from datetime import datetime
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL
from stock_fetcher import fetch_stock_data, fetch_market_news

logger = logging.getLogger(__name__)

def generate_stock_summary(market: str) -> str:
    """주식 데이터와 뉴스를 가져와 Gemini 모델을 사용해 시황 요약을 HTML로 생성합니다."""
    # 1. 데이터 수집
    logger.info("데이터 수집 시작 (시장: %s)", market)
    stock_data = fetch_stock_data(market)
    news_list = fetch_market_news(market, limit=15)
    
    market_name = "한국 증시" if market == "kr" else "미국 증시"
    today_str = datetime.now().strftime("%Y년 %m월 %d일")
    
    # 2. 프롬프트 구성
    prompt = f"당신은 전문적인 금융 분석가입니다. 오늘 {today_str}의 {market_name} 마감 시황(또는 최신 시황)과 그 변동 이유를 심층 분석하여 이메일 본문에 들어갈 세련된 HTML 위주 문자열로 작성해 주세요. <html>, <head>, <body> 태그는 생략하고 내부에 들어갈 내용만 작성하세요.\n\n"
    
    prompt += "### [1. 주요 지수 및 관심 종목 변동 데이터]\n"
    for name, info in stock_data.items():
        if "error" in info:
            prompt += f"- {name}: 데이터 조회 실패\n"
        else:
            trend = "상승" if info['change_pct'] > 0 else "하락" if info['change_pct'] < 0 else "보합"
            prompt += f"- {name}: {info['current']:,.2f} ({trend} {info['change']:,.2f}, {info['change_pct']:.2f}%)\n"
            
    prompt += "\n### [2. 오늘 수집된 주요 증시 뉴스 헤드라인]\n"
    if not news_list:
        prompt += "- 관련 뉴스 수집 실패 또는 뉴스 없음.\n"
    else:
        for idx, news in enumerate(news_list, 1):
            prompt += f"{idx}. {news['title']}\n"
            
    prompt += """\n### 작성 가이드라인 (반드시 지킬 것!):
1. '📈 주요 지수 & 관종 요약'과 '🧐 주요 변동 이유 및 시장 트렌드 분석'을 나누어 설명해 주세요.
2. 수집된 뉴스 헤드라인과 실제 데이터를 종합하여 **왜 이런 변동이 일어났는지 인과관계**를 명확하고 친절하게 설명해 주세요.
3. 디자인 가이드: <h3>, <ul>, <li>, <strong> 등을 적절히 사용해 이메일에서 예쁘게 보이도록 구성하세요. 상승은 빨간색(#e53935), 하락은 파란색(#1e88e5) 속성(style)을 적용해 가시성을 높이세요.
4. 코드 블록(```html) 마크다운을 절대 씌우지 말고, 순수 HTML 태그 문자열만 반환하세요."""

    # 3. Gemini 호출
    logger.info("Gemini 요약 요청 중...")
    if not GEMINI_API_KEY:
        return "<p>Gemini API 키가 설정되지 않았습니다.</p>"
        
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=2500, temperature=0.3)
        )
        
        summary = response.text.strip()
        # Clean potential markdown (방어 코드)
        summary = re.sub(r"^```(?:html|text)?\s*", "", summary, flags=re.IGNORECASE)
        summary = re.sub(r"\s*```$", "", summary)
        
        logger.info("Gemini 요약 성공")
        return summary
    except Exception as e:
        logger.exception("Gemini 요약 생성 실패:")
        return f"<p>AI 요약 생성 중 오류가 발생했습니다: {e}</p>"
