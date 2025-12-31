#!/usr/bin/env python3
"""
GitHub Automated Daily News Aggregator V3.0
Historical Archives Edition with Deep Vietnam Coverage

Features:
- Historical archives with date-based backup files
- Enhanced Vietnam market coverage (10-15 articles)
- Auto-generated history navigation menu
- Dark mode immersive accordion UI
"""

import os
import sys
import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional
import feedparser
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsAggregatorV3:
    """V3.0 News Aggregation Engine with Historical Archives"""
    
    # RSS Feed sources organized by regional category
    # Vietnam section significantly expanded with higher limits
    FEED_SOURCES = {
        "中美政经": {
            "limit": 6,
            "sources": [
                {"name": "Reuters US", "url": "https://feeds.reuters.com/reuters/topNews"},
                {"name": "Bloomberg Politics", "url": "https://feeds.bloomberg.com/politics/news.rss"},
                {"name": "SCMP China", "url": "https://www.scmp.com/rss/91/feed"},
                {"name": "Caixin Global", "url": "https://www.caixinglobal.com/rss.xml"},
                {"name": "WSJ World", "url": "https://feeds.wsj.com/wsj/xml/rss/3_7085.xml"},
            ]
        },
        "越南市场": {
            "limit": 12,  # Increased limit for Vietnam deep dive
            "sources": [
                {"name": "CafeF", "url": "https://cafef.vn/rss/thi-truong-chung-khoan.rss"},
                {"name": "VnExpress Business", "url": "https://vnexpress.net/rss/kinh-doanh.rss"},
                {"name": "VnEconomy", "url": "https://vneconomy.vn/rss/chung-khoan.rss"},
                {"name": "Vietnam Investment Review", "url": "https://vir.com.vn/rss/investment.rss"},
                # New sources for V3.0
                {"name": "VnExpress International", "url": "https://e.vnexpress.net/rss/business.rss"},
                {"name": "VietnamNet Global", "url": "https://vietnamnet.vn/rss/business.rss"},
                {"name": "The Saigon Times", "url": "https://english.thesaigontimes.vn/feed/"},
            ]
        },
        "全球宏观": {
            "limit": 6,
            "sources": [
                {"name": "FT Markets", "url": "https://www.ft.com/rss/home"},
                {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews"},
                {"name": "BBC Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml"},
                {"name": "Nikkei Asia", "url": "https://asia.nikkei.com/rss/feed/nar"},
                {"name": "DW Business", "url": "https://rss.dw.com/xml/rss-en-bus"},
            ]
        }
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
        """Initialize the V3.0 news aggregator with Gemini API"""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. "
                "Please set it before running this script."
            )
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.news_data = {}
        self.archives_dir = Path("archives")
        self.today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Ensure archives directory exists
        self.archives_dir.mkdir(exist_ok=True)
        
        logger.info("NewsAggregatorV3 initialized successfully")
    
    def fetch_feeds(self) -> None:
        """Fetch and parse RSS feeds from all sources"""
        logger.info("Starting RSS feed fetching...")
        
        for category, config in self.FEED_SOURCES.items():
            self.news_data[category] = []
            sources = config["sources"]
            limit = config["limit"]
            articles_per_source = max(2, limit // len(sources) + 1)
            
            logger.info(f"Category: {category} (target: {limit} articles, ~{articles_per_source} per source)")
            
            for source in sources:
                try:
                    logger.info(f"  Fetching {source['name']}...")
                    feed = feedparser.parse(source['url'])
                    
                    if feed.bozo and not feed.entries:
                        logger.warning(f"  Feed error for {source['name']}: {feed.bozo_exception}")
                        continue
                    
                    # Get articles from each source
                    for entry in feed.entries[:articles_per_source]:
                        # Extract and clean summary
                        raw_summary = entry.get('summary', entry.get('description', ''))
                        clean_summary = re.sub(r'<[^>]+>', '', raw_summary)[:500]
                        
                        article = {
                            "source": source['name'],
                            "title": entry.get('title', 'No title'),
                            "link": entry.get('link', '#'),
                            "published": entry.get('published', entry.get('updated', 'N/A')),
                            "summary": clean_summary,
                        }
                        self.news_data[category].append(article)
                        logger.info(f"    Added: {article['title'][:40]}...")
                
                except Exception as e:
                    logger.warning(f"  Error fetching {source['name']}: {str(e)}")
                    continue
            
            # Trim to limit
            if len(self.news_data[category]) > limit:
                self.news_data[category] = self.news_data[category][:limit]
            
            logger.info(f"  {category}: {len(self.news_data[category])} articles collected")
        
        total = sum(len(v) for v in self.news_data.values())
        logger.info(f"RSS fetching completed. Total articles: {total}")
    
    def generate_deep_analysis(self, title: str, summary: str, source: str) -> Optional[str]:
        """Generate AI-powered deep analysis using Google Gemini API"""
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
                
                analysis = self.generate_deep_analysis(
                    article['title'],
                    article['summary'],
                    article['source']
                )
                
                article['deep_analysis'] = analysis or "深度分析生成失败，请稍后重试。"
        
        logger.info("Article processing completed")
    
    def scan_archives(self) -> List[Dict[str, str]]:
        """Scan archives folder and return list of historical files"""
        archives = []
        
        if self.archives_dir.exists():
            for file in sorted(self.archives_dir.glob("*.html"), reverse=True):
                # Extract date from filename (e.g., 2025-01-01.html)
                date_str = file.stem
                try:
                    # Validate date format
                    datetime.strptime(date_str, "%Y-%m-%d")
                    archives.append({
                        "date": date_str,
                        "path": f"archives/{file.name}",
                        "display": date_str
                    })
                except ValueError:
                    continue
        
        logger.info(f"Found {len(archives)} historical archives")
        return archives
    
    def generate_html(self, output_file: str = "index.html", is_archive: bool = False) -> None:
        """Generate static HTML file with accordion UI and history navigation"""
        logger.info(f"Generating HTML file: {output_file}")
        
        # Scan existing archives for navigation
        archives = self.scan_archives()
        
        html_content = self._build_html(archives, is_archive)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML file generated successfully: {output_file}")
    
    def generate_archive(self) -> None:
        """Generate archive file for today"""
        archive_file = self.archives_dir / f"{self.today}.html"
        logger.info(f"Generating archive file: {archive_file}")
        
        # Scan existing archives (including today's if it exists)
        archives = self.scan_archives()
        
        # Add today if not already in list
        today_entry = {"date": self.today, "path": f"archives/{self.today}.html", "display": self.today}
        if not any(a["date"] == self.today for a in archives):
            archives.insert(0, today_entry)
        
        html_content = self._build_html(archives, is_archive=True)
        
        with open(archive_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Archive file generated successfully: {archive_file}")
    
    def _build_html(self, archives: List[Dict], is_archive: bool = False) -> str:
        """Build complete HTML content with accordion UI and history navigation"""
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        # Category icons and colors
        category_config = {
            "中美政经": {"icon": "🇺🇸🇨🇳", "color": "#e74c3c", "subtitle": "China & US Policy"},
            "越南市场": {"icon": "🇻🇳", "color": "#27ae60", "subtitle": "Vietnam Business · Deep Dive"},
            "全球宏观": {"icon": "🌍", "color": "#3498db", "subtitle": "Global & EU/East Asia"},
        }
        
        # Build history dropdown HTML
        history_items = ""
        for archive in archives[:30]:  # Limit to last 30 entries
            # Adjust path for archive pages (they're in archives/ subfolder)
            link_path = f"../{archive['path']}" if is_archive else archive['path']
            if archive['date'] == self.today:
                link_path = "../index.html" if is_archive else "index.html"
                history_items += f'<a href="{link_path}" class="history-item current">{archive["display"]} (今日)</a>\n'
            else:
                history_items += f'<a href="{link_path}" class="history-item">{archive["display"]}</a>\n'
        
        # Home link for archive pages
        home_link = "../index.html" if is_archive else "index.html"
        
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
        
        /* Navigation Bar */
        .navbar {{
            position: sticky;
            top: 0;
            z-index: 1000;
            background: rgba(10, 10, 15, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border-color);
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .navbar-brand {{
            font-size: 1.2em;
            font-weight: 600;
            color: var(--text-primary);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .navbar-brand:hover {{
            color: var(--accent-blue);
        }}
        
        /* History Dropdown */
        .history-dropdown {{
            position: relative;
        }}
        
        .history-btn {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9em;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
        }}
        
        .history-btn:hover {{
            background: var(--bg-card-hover);
            color: var(--text-primary);
        }}
        
        .history-btn svg {{
            width: 16px;
            height: 16px;
            fill: currentColor;
            transition: transform 0.2s;
        }}
        
        .history-dropdown.open .history-btn svg {{
            transform: rotate(180deg);
        }}
        
        .history-menu {{
            position: absolute;
            top: calc(100% + 8px);
            right: 0;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            min-width: 200px;
            max-height: 400px;
            overflow-y: auto;
            display: none;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        }}
        
        .history-dropdown.open .history-menu {{
            display: block;
        }}
        
        .history-menu-header {{
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.8em;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .history-item {{
            display: block;
            padding: 10px 16px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.9em;
            transition: all 0.2s;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .history-item:last-child {{
            border-bottom: none;
        }}
        
        .history-item:hover {{
            background: var(--bg-card-hover);
            color: var(--text-primary);
        }}
        
        .history-item.current {{
            color: var(--accent-blue);
            font-weight: 600;
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
        
        .header .vietnam-badge {{
            display: inline-block;
            margin-top: 15px;
            padding: 6px 14px;
            background: linear-gradient(135deg, var(--accent-green) 0%, #1e8449 100%);
            color: white;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
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
        
        .category-count {{
            background: var(--accent-color);
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
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
            .navbar {{
                padding: 10px 15px;
            }}
            
            .navbar-brand {{
                font-size: 1em;
            }}
            
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
            
            .history-menu {{
                right: -10px;
                min-width: 180px;
            }}
        }}
        
        /* Category-specific accent colors */
        .category-china-us {{ --accent-color: #e74c3c; }}
        .category-vietnam {{ --accent-color: #27ae60; }}
        .category-global {{ --accent-color: #3498db; }}
        
        /* Scrollbar styling */
        .history-menu::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .history-menu::-webkit-scrollbar-track {{
            background: var(--bg-secondary);
        }}
        
        .history-menu::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <!-- Navigation Bar with History Dropdown -->
    <nav class="navbar">
        <a href="{home_link}" class="navbar-brand">
            📊 每日深度研报
        </a>
        <div class="history-dropdown" id="historyDropdown">
            <button class="history-btn" onclick="toggleHistory()">
                📅 往期回顾
                <svg viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
            </button>
            <div class="history-menu">
                <div class="history-menu-header">Historical Archives</div>
                {history_items}
            </div>
        </div>
    </nav>
    
    <header class="header">
        <h1>📊 每日深度研报</h1>
        <p class="subtitle">AI-Powered Macro Analysis · 首席分析师视角</p>
        <span class="timestamp">🕐 更新时间: {current_time}</span>
        <div><span class="vietnam-badge">🇻🇳 越南深度版 V3.0</span></div>
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
                <span class="category-count">{len(articles)} 篇</span>
                <span class="category-subtitle">{config['subtitle']}</span>
            </div>
"""
            
            for idx, article in enumerate(articles):
                article_id = f"{category}-{idx}".replace(" ", "-")
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
        <p class="powered">V3.0 Historical Archives Edition</p>
    </footer>
    
    <script>
        function toggleArticle(header) {
            const article = header.closest('.article');
            const wasExpanded = article.classList.contains('expanded');
            
            article.classList.toggle('expanded');
            
            if (!wasExpanded) {
                setTimeout(() => {
                    article.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
            }
        }
        
        function toggleHistory() {
            const dropdown = document.getElementById('historyDropdown');
            dropdown.classList.toggle('open');
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('historyDropdown');
            if (!dropdown.contains(e.target)) {
                dropdown.classList.remove('open');
            }
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.article.expanded').forEach(a => {
                    a.classList.remove('expanded');
                });
                document.getElementById('historyDropdown').classList.remove('open');
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
            logger.info("Starting Daily News Aggregation Pipeline V3.0")
            logger.info("Historical Archives Edition with Deep Vietnam Coverage")
            logger.info("=" * 70)
            
            self.fetch_feeds()
            self.process_articles()
            
            # Generate main index.html
            self.generate_html(output_file, is_archive=False)
            
            # Generate archive file for today
            self.generate_archive()
            
            logger.info("=" * 70)
            logger.info("Pipeline V3.0 completed successfully!")
            logger.info(f"Generated: {output_file}")
            logger.info(f"Archived: archives/{self.today}.html")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            sys.exit(1)


def main():
    """Main entry point"""
    try:
        aggregator = NewsAggregatorV3()
        aggregator.run()
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
