#!/usr/bin/env python3
"""
GitHub Automated Daily News Aggregator V2.0
Deep Analysis Edition with Immersive Accordion UI

Features:
- Three regional categories: China & US, Vietnam Biz, Global & EU/East Asia
- AI-powered deep analysis by "Chief Macro Economist" persona
- Accordion-style expand/collapse UI without page redirects
"""

import os
import sys
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
import feedparser
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsAggregatorV2:
    """V2.0 News Aggregation Engine with Deep Analysis"""
    
    # RSS Feed sources organized by regional category
    FEED_SOURCES = {
        "中美政经": [
            {"name": "Reuters US", "url": "https://feeds.reuters.com/reuters/topNews"},
            {"name": "Bloomberg Politics", "url": "https://feeds.bloomberg.com/politics/news.rss"},
            {"name": "SCMP China", "url": "https://www.scmp.com/rss/91/feed"},
            {"name": "Caixin Global", "url": "https://www.caixinglobal.com/rss.xml"},
            {"name": "WSJ World", "url": "https://feeds.a]wsj.com/wsj/xml/rss/3_7085.xml"},
        ],
        "越南市场": [
            {"name": "CafeF", "url": "https://cafef.vn/rss/thi-truong-chung-khoan.rss"},
            {"name": "VnExpress Business", "url": "https://vnexpress.net/rss/kinh-doanh.rss"},
            {"name": "VnEconomy", "url": "https://vneconomy.vn/rss/chung-khoan.rss"},
            {"name": "Vietnam Investment Review", "url": "https://vir.com.vn/rss/investment.rss"},
        ],
        "全球宏观": [
            {"name": "FT Markets", "url": "https://www.ft.com/rss/home"},
            {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews"},
            {"name": "BBC Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml"},
            {"name": "Nikkei Asia", "url": "https://asia.nikkei.com/rss/feed/nar"},
            {"name": "DW Business", "url": "https://rss.dw.com/xml/rss-en-bus"},
        ]
    }
    
    # Deep Analysis Prompt Template
    ANALYST_PROMPT = """你是一位拥有20年经验的首席宏观经济分析师，曾任职于高盛、摩根士丹利等顶级投行。

请根据以下新闻信息，撰写一篇200-300字的深度研报摘要。

【新闻来源】{source}
【新闻标题】{title}
【原文摘要】{summary}

你的研报必须包含以下三个部分，请用清晰的段落分隔：

📌 核心事实：
用2-3句话精准概括新闻的核心内容，提炼关键数据和事件。

📊 经济影响：
分析此事件对相关经济体、行业或市场的短期和中期影响。如涉及中美关系，需分析对双边贸易、供应链的影响；如涉及越南，需关注FDI和出口；如涉及全球宏观，需关注货币政策和资本流动。

⚠️ 潜在风险：
指出投资者和决策者需要警惕的风险因素，包括政策不确定性、市场波动、地缘政治风险等。

请直接输出研报内容，使用中文，语言专业但易于理解。不要添加任何开场白或结束语。"""

    def __init__(self):
        """Initialize the V2.0 news aggregator with Gemini API"""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. "
                "Please set it before running this script."
            )
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.news_data = {}
        
        logger.info("NewsAggregatorV2 initialized successfully")
    
    def fetch_feeds(self) -> None:
        """Fetch and parse RSS feeds from all sources"""
        logger.info("Starting RSS feed fetching...")
        
        for category, sources in self.FEED_SOURCES.items():
            self.news_data[category] = []
            
            for source in sources:
                try:
                    logger.info(f"Fetching {source['name']} ({source['url']})")
                    feed = feedparser.parse(source['url'])
                    
                    if feed.bozo and not feed.entries:
                        logger.warning(f"Feed error for {source['name']}: {feed.bozo_exception}")
                        continue
                    
                    # Get top 2 articles from each source
                    for entry in feed.entries[:2]:
                        # Extract and clean summary
                        raw_summary = entry.get('summary', entry.get('description', ''))
                        # Remove HTML tags for cleaner text
                        import re
                        clean_summary = re.sub(r'<[^>]+>', '', raw_summary)[:500]
                        
                        article = {
                            "source": source['name'],
                            "title": entry.get('title', 'No title'),
                            "link": entry.get('link', '#'),
                            "published": entry.get('published', entry.get('updated', 'N/A')),
                            "summary": clean_summary,
                        }
                        self.news_data[category].append(article)
                        logger.info(f"  Added: {article['title'][:50]}...")
                
                except Exception as e:
                    logger.warning(f"Error fetching {source['name']}: {str(e)}")
                    continue
        
        total = sum(len(v) for v in self.news_data.values())
        logger.info(f"RSS fetching completed. Total articles: {total}")
    
    def generate_deep_analysis(self, title: str, summary: str, source: str) -> Optional[str]:
        """
        Generate AI-powered deep analysis using Google Gemini API
        
        Args:
            title: Article title
            summary: Original article summary
            source: News source name
            
        Returns:
            200-300 word deep analysis or None if generation fails
        """
        try:
            prompt = self.ANALYST_PROMPT.format(
                source=source,
                title=title,
                summary=summary
            )
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                return response.text.strip()
            else:
                logger.warning(f"Empty response from Gemini for: {title}")
                return None
        
        except Exception as e:
            logger.error(f"Gemini API error for '{title}': {str(e)}")
            return None
    
    def process_articles(self) -> None:
        """Process articles with deep AI analysis"""
        logger.info("Processing articles with Gemini API deep analysis...")
        
        for category, articles in self.news_data.items():
            logger.info(f"Processing category: {category} ({len(articles)} articles)")
            
            for i, article in enumerate(articles):
                logger.info(f"  [{i+1}/{len(articles)}] Analyzing: {article['title'][:40]}...")
                
                # Generate deep analysis
                analysis = self.generate_deep_analysis(
                    article['title'],
                    article['summary'],
                    article['source']
                )
                
                article['deep_analysis'] = analysis or "深度分析生成失败，请稍后重试。"
        
        logger.info("Article processing completed")
    
    def generate_html(self, output_file: str = "index.html") -> None:
        """
        Generate static HTML file with accordion UI
        
        Args:
            output_file: Output HTML file path
        """
        logger.info(f"Generating HTML file: {output_file}")
        
        html_content = self._build_html()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML file generated successfully: {output_file}")
    
    def _build_html(self) -> str:
        """Build complete HTML content with accordion UI"""
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        # Category icons and colors
        category_config = {
            "中美政经": {"icon": "🇺🇸🇨🇳", "color": "#e74c3c", "subtitle": "China & US Policy"},
            "越南市场": {"icon": "🇻🇳", "color": "#27ae60", "subtitle": "Vietnam Business"},
            "全球宏观": {"icon": "🌍", "color": "#3498db", "subtitle": "Global & EU/East Asia"},
        }
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日深度研报 | Daily Deep Analysis</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a24;
            --bg-card-hover: #222230;
            --text-primary: #f0f0f5;
            --text-secondary: #a0a0b0;
            --text-muted: #606070;
            --border-color: #2a2a3a;
            --accent-blue: #3498db;
            --accent-red: #e74c3c;
            --accent-green: #27ae60;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.7;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* Header */
        .header {{
            text-align: center;
            padding: 60px 20px;
            background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 40px;
        }}
        
        .header h1 {{
            font-size: 2.8em;
            font-weight: 700;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #fff 0%, #a0a0b0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            color: var(--text-secondary);
            margin-bottom: 20px;
        }}
        
        .header .timestamp {{
            font-size: 0.9em;
            color: var(--text-muted);
            padding: 8px 16px;
            background: var(--bg-card);
            border-radius: 20px;
            display: inline-block;
        }}
        
        /* Category Section */
        .category {{
            margin-bottom: 50px;
        }}
        
        .category-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid var(--border-color);
        }}
        
        .category-icon {{
            font-size: 1.8em;
        }}
        
        .category-title {{
            font-size: 1.6em;
            font-weight: 600;
            color: var(--text-primary);
        }}
        
        .category-subtitle {{
            font-size: 0.9em;
            color: var(--text-muted);
            margin-left: auto;
        }}
        
        /* Article Card - Accordion */
        .article {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 16px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .article:hover {{
            background: var(--bg-card-hover);
            border-color: #3a3a4a;
        }}
        
        .article-header {{
            padding: 20px 24px;
            cursor: pointer;
            display: flex;
            align-items: flex-start;
            gap: 16px;
            user-select: none;
        }}
        
        .article-header:hover {{
            background: rgba(255, 255, 255, 0.02);
        }}
        
        .article-indicator {{
            width: 4px;
            height: 4px;
            background: var(--accent-color);
            border-radius: 50%;
            margin-top: 10px;
            flex-shrink: 0;
        }}
        
        .article-main {{
            flex: 1;
        }}
        
        .article-source {{
            font-size: 0.75em;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        
        .article-title {{
            font-size: 1.15em;
            font-weight: 600;
            color: var(--text-primary);
            line-height: 1.5;
            margin-bottom: 8px;
        }}
        
        .article-meta {{
            font-size: 0.85em;
            color: var(--text-muted);
        }}
        
        .article-toggle {{
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg-secondary);
            border-radius: 8px;
            flex-shrink: 0;
            transition: transform 0.3s ease;
        }}
        
        .article-toggle svg {{
            width: 16px;
            height: 16px;
            fill: var(--text-muted);
            transition: transform 0.3s ease;
        }}
        
        .article.expanded .article-toggle svg {{
            transform: rotate(180deg);
        }}
        
        /* Article Content - Expandable */
        .article-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s ease-out;
        }}
        
        .article.expanded .article-content {{
            max-height: 2000px;
            transition: max-height 0.6s ease-in;
        }}
        
        .article-body {{
            padding: 0 24px 24px 44px;
            border-top: 1px solid var(--border-color);
        }}
        
        .analysis-section {{
            padding-top: 20px;
        }}
        
        .analysis-label {{
            font-size: 0.8em;
            color: var(--accent-color);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .analysis-label::before {{
            content: "";
            width: 20px;
            height: 2px;
            background: var(--accent-color);
        }}
        
        .analysis-text {{
            font-size: 1em;
            color: var(--text-secondary);
            line-height: 1.9;
            white-space: pre-wrap;
        }}
        
        .analysis-text p {{
            margin-bottom: 16px;
        }}
        
        .source-link {{
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px dashed var(--border-color);
        }}
        
        .source-link a {{
            font-size: 0.8em;
            color: var(--text-muted);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: color 0.2s;
        }}
        
        .source-link a:hover {{
            color: var(--accent-blue);
        }}
        
        .source-link a svg {{
            width: 12px;
            height: 12px;
            fill: currentColor;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 40px 20px;
            border-top: 1px solid var(--border-color);
            margin-top: 60px;
        }}
        
        .footer p {{
            font-size: 0.85em;
            color: var(--text-muted);
            margin-bottom: 8px;
        }}
        
        .footer .powered {{
            font-size: 0.75em;
            color: var(--text-muted);
            opacity: 0.7;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 15px;
            }}
            
            .header {{
                padding: 40px 15px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .category-header {{
                flex-wrap: wrap;
            }}
            
            .category-subtitle {{
                width: 100%;
                margin-left: 0;
                margin-top: 8px;
            }}
            
            .article-header {{
                padding: 16px;
            }}
            
            .article-body {{
                padding: 0 16px 20px 16px;
            }}
            
            .article-title {{
                font-size: 1.05em;
            }}
        }}
        
        /* Category-specific accent colors */
        .category-china-us {{ --accent-color: #e74c3c; }}
        .category-vietnam {{ --accent-color: #27ae60; }}
        .category-global {{ --accent-color: #3498db; }}
    </style>
</head>
<body>
    <header class="header">
        <h1>📊 每日深度研报</h1>
        <p class="subtitle">AI-Powered Macro Analysis · 首席分析师视角</p>
        <span class="timestamp">🕐 更新时间: {current_time}</span>
    </header>
    
    <main class="container">
"""
        
        # Generate category sections
        category_classes = {
            "中美政经": "category-china-us",
            "越南市场": "category-vietnam",
            "全球宏观": "category-global",
        }
        
        for category, articles in self.news_data.items():
            if not articles:
                continue
            
            config = category_config.get(category, {"icon": "📰", "color": "#666", "subtitle": ""})
            cat_class = category_classes.get(category, "")
            
            html += f"""
        <section class="category {cat_class}">
            <div class="category-header">
                <span class="category-icon">{config['icon']}</span>
                <h2 class="category-title">{category}</h2>
                <span class="category-subtitle">{config['subtitle']}</span>
            </div>
"""
            
            for idx, article in enumerate(articles):
                article_id = f"{category}-{idx}".replace(" ", "-")
                # Escape HTML special characters
                title_escaped = article['title'].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
                analysis_escaped = article.get('deep_analysis', '').replace('<', '&lt;').replace('>', '&gt;')
                
                html += f"""
            <article class="article" data-id="{article_id}">
                <div class="article-header" onclick="toggleArticle(this)">
                    <div class="article-indicator"></div>
                    <div class="article-main">
                        <div class="article-source">{article['source']}</div>
                        <h3 class="article-title">{title_escaped}</h3>
                        <div class="article-meta">{article['published']}</div>
                    </div>
                    <div class="article-toggle">
                        <svg viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
                    </div>
                </div>
                <div class="article-content">
                    <div class="article-body">
                        <div class="analysis-section">
                            <div class="analysis-label">深度分析 Deep Analysis</div>
                            <div class="analysis-text">{analysis_escaped}</div>
                        </div>
                        <div class="source-link">
                            <a href="{article['link']}" target="_blank" rel="noopener noreferrer">
                                <svg viewBox="0 0 24 24"><path d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>
                                Source Link · 原文链接
                            </a>
                        </div>
                    </div>
                </div>
            </article>
"""
            
            html += """
        </section>
"""
        
        html += """
    </main>
    
    <footer class="footer">
        <p>🤖 由 Google Gemini AI 深度分析驱动</p>
        <p class="powered">Automated by GitHub Actions · Hosted on GitHub Pages</p>
    </footer>
    
    <script>
        function toggleArticle(header) {
            const article = header.closest('.article');
            const wasExpanded = article.classList.contains('expanded');
            
            // Close all other articles (optional: remove these lines for multi-expand)
            // document.querySelectorAll('.article.expanded').forEach(a => {
            //     if (a !== article) a.classList.remove('expanded');
            // });
            
            // Toggle current article
            article.classList.toggle('expanded');
            
            // Smooth scroll into view if expanding
            if (!wasExpanded) {
                setTimeout(() => {
                    article.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
            }
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.article.expanded').forEach(a => {
                    a.classList.remove('expanded');
                });
            }
        });
    </script>
</body>
</html>"""
        
        return html
    
    def run(self, output_file: str = "index.html") -> None:
        """Execute the complete news aggregation pipeline"""
        try:
            logger.info("=" * 70)
            logger.info("Starting Daily News Aggregation Pipeline V2.0 - Deep Analysis Edition")
            logger.info("=" * 70)
            
            self.fetch_feeds()
            self.process_articles()
            self.generate_html(output_file)
            
            logger.info("=" * 70)
            logger.info("Pipeline V2.0 completed successfully!")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            sys.exit(1)


def main():
    """Main entry point"""
    try:
        aggregator = NewsAggregatorV2()
        aggregator.run()
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
