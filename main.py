#!/usr/bin/env python3
"""
GitHub Automated Daily News Aggregator
Fetches news from RSS feeds, generates AI summaries via Google Gemini API,
and outputs a static HTML file for GitHub Pages deployment.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
import feedparser
import google.generativeai as genai
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsAggregator:
    """Main news aggregation engine"""
    
    # RSS Feed sources organized by category
    FEED_SOURCES = {
        "越南特刊": [
            {"name": "CafeF", "url": "https://cafef.vn/rss/news.rss"},
            {"name": "VnEconomy", "url": "https://vneconomy.vn/rss.xml"},
        ],
        "东亚/中国": [
            {"name": "新浪财经", "url": "http://feed.sina.com.cn/finance/"},
            {"name": "财新网", "url": "http://feed.caixin.com/rss/caixin.xml"},
            {"name": "东方财富", "url": "http://feed.eastmoney.com/"},
        ],
        "全球宏观": [
            {"name": "Bloomberg", "url": "https://feeds.bloomberg.com/markets/news.rss"},
            {"name": "Reuters", "url": "https://feeds.reuters.com/reuters/businessNews"},
            {"name": "Financial Times", "url": "https://feeds.ft.com/markets"},
        ]
    }
    
    def __init__(self):
        """Initialize the news aggregator with Gemini API"""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. "
                "Please set it before running this script."
            )
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.news_data = {}
        
        logger.info("NewsAggregator initialized successfully")
    
    def fetch_feeds(self) -> None:
        """Fetch and parse RSS feeds from all sources"""
        logger.info("Starting RSS feed fetching...")
        
        for category, sources in self.FEED_SOURCES.items():
            self.news_data[category] = []
            
            for source in sources:
                try:
                    logger.info(f"Fetching {source['name']} ({source['url']})")
                    feed = feedparser.parse(source['url'])
                    
                    # Get top 3 articles from each source
                    for entry in feed.entries[:3]:
                        article = {
                            "source": source['name'],
                            "title": entry.get('title', 'No title'),
                            "link": entry.get('link', '#'),
                            "published": entry.get('published', 'N/A'),
                            "summary": entry.get('summary', '')[:300],  # Truncate original summary
                        }
                        self.news_data[category].append(article)
                
                except Exception as e:
                    logger.warning(f"Error fetching {source['name']}: {str(e)}")
                    continue
        
        logger.info(f"RSS fetching completed. Total articles: {sum(len(v) for v in self.news_data.values())}")
    
    def generate_summary(self, title: str, summary: str, source: str) -> Optional[str]:
        """
        Generate AI-powered Chinese summary using Google Gemini API
        
        Args:
            title: Article title
            summary: Original article summary
            source: News source name
            
        Returns:
            100-word Chinese summary or None if generation fails
        """
        try:
            # Prepare prompt for Gemini
            prompt = f"""请用中文为以下新闻生成100字左右的摘要。摘要应该简洁、准确、突出核心观点。

新闻来源: {source}
标题: {title}
原文摘要: {summary}

请直接输出中文摘要，不需要其他说明。"""
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                # Truncate to approximately 100 words (300 characters in Chinese)
                return response.text[:300]
            else:
                logger.warning(f"Empty response from Gemini for: {title}")
                return None
        
        except Exception as e:
            logger.error(f"Gemini API error for '{title}': {str(e)}")
            return None
    
    def process_articles(self) -> None:
        """Process articles with AI summaries"""
        logger.info("Processing articles with Gemini API...")
        
        for category, articles in self.news_data.items():
            for article in articles:
                # Generate AI summary
                ai_summary = self.generate_summary(
                    article['title'],
                    article['summary'],
                    article['source']
                )
                
                article['ai_summary'] = ai_summary or "摘要生成失败"
                logger.info(f"Processed: {article['title'][:50]}...")
        
        logger.info("Article processing completed")
    
    def generate_html(self, output_file: str = "index.html") -> None:
        """
        Generate static HTML file for GitHub Pages
        
        Args:
            output_file: Output HTML file path
        """
        logger.info(f"Generating HTML file: {output_file}")
        
        # Build HTML content
        html_content = self._build_html()
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML file generated successfully: {output_file}")
    
    def _build_html(self) -> str:
        """Build complete HTML content"""
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日新闻聚合 | Daily News Digest</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #333;
            line-height: 1.6;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 0.95em;
            opacity: 0.9;
        }}
        
        .timestamp {{
            font-size: 0.85em;
            opacity: 0.8;
            margin-top: 15px;
            font-weight: 500;
        }}
        
        .content {{
            padding: 30px 20px;
        }}
        
        .category {{
            margin-bottom: 40px;
        }}
        
        .category-title {{
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            font-weight: 700;
        }}
        
        .articles {{
            display: grid;
            gap: 20px;
        }}
        
        .article {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }}
        
        .article:hover {{
            background: #f0f2f8;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
            transform: translateX(4px);
        }}
        
        .article-source {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        .article-title {{
            font-size: 1.2em;
            color: #333;
            margin-bottom: 10px;
            font-weight: 600;
            line-height: 1.4;
        }}
        
        .article-title a {{
            color: #667eea;
            text-decoration: none;
            transition: color 0.2s;
        }}
        
        .article-title a:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}
        
        .article-summary {{
            color: #555;
            font-size: 0.95em;
            margin-bottom: 12px;
            line-height: 1.6;
        }}
        
        .article-meta {{
            font-size: 0.85em;
            color: #999;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .read-more {{
            display: inline-block;
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s;
        }}
        
        .read-more:hover {{
            color: #764ba2;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 0.9em;
            border-top: 1px solid #eee;
        }}
        
        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        .footer a:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .category-title {{
                font-size: 1.4em;
            }}
            
            .article-title {{
                font-size: 1.05em;
            }}
            
            .content {{
                padding: 20px 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 每日新闻聚合</h1>
            <p>Daily News Digest | 智能摘要 · 全球视野</p>
            <div class="timestamp">更新时间: {current_time}</div>
        </div>
        
        <div class="content">
"""
        
        # Add categories and articles
        for category, articles in self.news_data.items():
            if not articles:
                continue
            
            html += f'            <div class="category">\n'
            html += f'                <h2 class="category-title">{category}</h2>\n'
            html += f'                <div class="articles">\n'
            
            for article in articles:
                html += self._build_article_html(article)
            
            html += f'                </div>\n'
            html += f'            </div>\n'
        
        html += """        </div>
        
        <div class="footer">
            <p>🤖 由 Google Gemini AI 驱动 | Powered by Google Gemini API</p>
            <p>自动更新于 GitHub Actions | Auto-updated by GitHub Actions</p>
            <p><a href="https://github.com">GitHub</a> | <a href="https://pages.github.com">GitHub Pages</a></p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _build_article_html(self, article: Dict) -> str:
        """Build HTML for a single article"""
        return f"""                    <div class="article">
                        <span class="article-source">{article['source']}</span>
                        <h3 class="article-title">
                            <a href="{article['link']}" target="_blank" rel="noopener noreferrer">
                                {article['title']}
                            </a>
                        </h3>
                        <div class="article-summary">{article.get('ai_summary', '摘要生成失败')}</div>
                        <div class="article-meta">
                            <span>{article['published']}</span>
                            <a href="{article['link']}" target="_blank" rel="noopener noreferrer" class="read-more">
                                阅读全文 →
                            </a>
                        </div>
                    </div>
"""
    
    def run(self, output_file: str = "index.html") -> None:
        """Execute the complete news aggregation pipeline"""
        try:
            logger.info("=" * 60)
            logger.info("Starting Daily News Aggregation Pipeline")
            logger.info("=" * 60)
            
            self.fetch_feeds()
            self.process_articles()
            self.generate_html(output_file)
            
            logger.info("=" * 60)
            logger.info("Pipeline completed successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            sys.exit(1)


def main():
    """Main entry point"""
    try:
        aggregator = NewsAggregator()
        aggregator.run()
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
