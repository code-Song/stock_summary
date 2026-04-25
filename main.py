# -*- coding: utf-8 -*-
import argparse
import logging
import sys
from datetime import datetime

from email_sender import send_email
from summarizer import generate_stock_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

def run(market: str):
    logger.info("=" * 60)
    logger.info("증시 요약 작업 시작 (market: %s)", market)
    logger.info("=" * 60)
    
    html_summary = generate_stock_summary(market)
    
    market_name = "한국 증시" if market == "kr" else "미국 증시"
    today = datetime.now().strftime("%Y년 %m월 %d일")
    subject = f"📊 [{market_name}] 마감 시황 및 변동 요약 - {today}"
    
    logger.info("이메일 발송 중...")
    success = send_email(html_body=html_summary, subject=subject)
    
    if success:
        logger.info("✅ 이메일 전송 완료!")
    else:
        logger.error("❌ 이메일 전송 실패!")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="주식 시장 요약 생성기")
    parser.add_argument("--market", choices=["kr", "us"], required=True, help="조회할 시장 (kr 또는 us)")
    args = parser.parse_args()
    
    run(args.market)
