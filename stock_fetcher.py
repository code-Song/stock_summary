# -*- coding: utf-8 -*-
"""주식 시장 지수 및 관련 뉴스 데이터 수집기."""
import yfinance as yf
import feedparser
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# 각 시장별 대표 지수 및 관심 종목
MARKET_TICKERS = {
    "kr": {
        "KOSPI": "^KS11",
        "KOSDAQ": "^KQ11",
        "삼성전자": "005930.KS",
        "SK하이닉스": "000660.KS"
    },
    "us": {
        "S&P 500": "^GSPC",
        "NASDAQ 100": "^NDX",
        "Apple": "AAPL",
        "Nvidia": "NVDA"
    }
}

# 관련 뉴스를 가져오기 위한 검색 키워드
NEWS_QUERIES = {
    "kr": "한국+증시+OR+코스피+OR+코스닥+OR+삼성전자+when:1d",
    "us": "미국+증시+OR+S&P500+OR+나스닥+OR+엔비디아+when:1d"
}

def fetch_stock_data(market: str) -> Dict[str, Any]:
    """지정된 시장의 최신 주식/지수 변동 데이터를 수집합니다."""
    tickers = MARKET_TICKERS.get(market, {})
    data = {}
    
    for name, symbol in tickers.items():
        try:
            stock = yf.Ticker(symbol)
            # 최근 2영업일의 데이터를 가져와 등락폭 계산
            hist = stock.history(period="5d")  # 휴일 고려 5일치 가져온 후 마지막 2일 접근
            
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                current = hist['Close'].iloc[-1]
                change = current - prev_close
                change_pct = (change / prev_close) * 100
                data[name] = {
                    "current": current,
                    "change": change,
                    "change_pct": change_pct
                }
            elif len(hist) == 1:
                data[name] = {
                    "current": hist['Close'].iloc[0],
                    "change": 0.0,
                    "change_pct": 0.0
                }
            else:
                data[name] = {"error": "No data"}
        except Exception as e:
            logger.error("Failed to fetch data for %s: %s", symbol, e)
            data[name] = {"error": str(e)}
            
    return data

def fetch_market_news(market: str, limit: int = 15) -> List[Dict[str, str]]:
    """Google 뉴스 RSS를 통해 해당 시장의 최근 1일치 핵심 뉴스를 수집합니다."""
    query = NEWS_QUERIES.get(market, "")
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        feed = feedparser.parse(rss_url)
        news_list = []
        for entry in feed.entries[:limit]:
            news_list.append({
                "title": entry.title,
                "link": entry.link,
                "published": getattr(entry, 'published', "")
            })
        return news_list
    except Exception as e:
        logger.error("Failed to fetch news for market %s: %s", market, e)
        return []
