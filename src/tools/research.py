import os
import re
import ssl
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from config import OLLAMA_HOST, LOCAL_MODEL

logger = logging.getLogger("jarvis.tools.research")

# Output directory for research reports
RESEARCH_DIR = Path.home() / "Documents" / "Jarvis_Research"
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def _clean_url(url: str) -> str:
    """Clean DuckDuckGo tracking parameters from URL."""
    url = urllib.parse.unquote(url)
    if "&amp;rut=" in url:
        url = url.split("&amp;rut=")[0]
    elif "&rut=" in url:
        url = url.split("&rut=")[0]
    return url.strip()

def _query_duckduckgo_web(query: str) -> List[Dict[str, str]]:
    """Query DuckDuckGo Web Search HTML using browser User-Agent for comprehensive results."""
    results = []
    try:
        ctx = ssl._create_unverified_context()
        encoded_q = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_q}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        with urllib.request.urlopen(req, context=ctx, timeout=10.0) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        raw_links = re.findall(r'<a[^>]+href=\"//duckduckgo.com/l/\?[^\"]*uddg=([^\"]+)\"[^>]*>(.*?)</a>', html, re.DOTALL)
        snippets_raw = re.findall(r'<a class=\"result__snippet[^\">]*>(.*?)</a>', html, re.DOTALL)

        seen_urls = set()
        for idx, (raw_url, raw_title) in enumerate(raw_links):
            clean_u = _clean_url(raw_url)
            clean_t = re.sub(r'<[^>]+>', '', raw_title).strip()
            
            if clean_t and clean_u not in seen_urls and not clean_u.startswith("https://duckduckgo.com"):
                seen_urls.add(clean_u)
                snippet_text = re.sub(r'<[^>]+>', '', snippets_raw[idx]).strip() if idx < len(snippets_raw) else clean_t
                results.append({
                    "title": clean_t,
                    "snippet": snippet_text or clean_t,
                    "url": clean_u
                })
                if len(results) >= 8:
                    break
    except Exception as e:
        logger.warning(f"DuckDuckGo web fetch failed: {e}")
    return results

def _query_duckduckgo_api(query: str) -> List[Dict[str, str]]:
    """Query DuckDuckGo Instant Answer API."""
    results = []
    try:
        ctx = ssl._create_unverified_context()
        encoded_q = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_q}&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        
        with urllib.request.urlopen(req, context=ctx, timeout=6.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        abstract = data.get("AbstractText", "").strip()
        abstract_url = data.get("AbstractURL", "").strip()
        heading = data.get("Heading", "").strip() or query

        if abstract:
            results.append({
                "title": heading,
                "snippet": abstract,
                "url": abstract_url or f"https://duckduckgo.com/?q={encoded_q}"
            })

        for item in data.get("RelatedTopics", [])[:5]:
            text = item.get("Text", "").strip()
            first_url = item.get("FirstURL", "").strip()
            if text:
                title = text.split(" - ")[0] if " - " in text else text[:40]
                results.append({
                    "title": title,
                    "snippet": text,
                    "url": first_url or f"https://duckduckgo.com/?q={encoded_q}"
                })
    except Exception as e:
        logger.warning(f"DuckDuckGo API search failed: {e}")
    return results

def _query_wikipedia(query: str) -> List[Dict[str, str]]:
    """Query Wikipedia Search API."""
    results = []
    try:
        ctx = ssl._create_unverified_context()
        encoded_q = urllib.parse.quote(query)
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_q}&format=json"
        req = urllib.request.Request(search_url, headers={"User-Agent": USER_AGENT})

        with urllib.request.urlopen(req, context=ctx, timeout=6.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        search_items = data.get("query", {}).get("search", [])[:3]
        for item in search_items:
            title = item.get("title", "")
            snippet_raw = item.get("snippet", "")
            snippet = re.sub(r'<[^>]+>', '', snippet_raw).strip()
            page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"

            if title and snippet:
                results.append({
                    "title": f"Wikipedia: {title}",
                    "snippet": snippet,
                    "url": page_url
                })
    except Exception as e:
        logger.warning(f"Wikipedia search failed: {e}")
    return results

def _synthesize_with_llm(topic: str, source_notes: str) -> str:
    """Use Ollama Gemma model for deep research synthesis with full token limit and 180s timeout."""
    prompt = f"""TOPIC: {topic}

SOURCE NOTES:
{source_notes}

Write your response in this exact structure:

## Summary
2-4 sentences giving the direct answer to the topic, in plain language (under 80 words).

## Key Findings
- Bullet points of the most important facts (maximum 5 bullets), each grounded in the source notes
- Include specific details, numbers, specs, comparisons, or findings from the source notes
- If sources disagree on something, say so explicitly
- Do not repeat the same point twice

## Sources
List each source used, numbered, with its title/url.

Rules:
- If the source notes don't contain enough information to answer part of the topic, say "Not enough information found".
- Do not use flowery language or filler phrases.
- Keep Key Findings to 5 bullets maximum."""

    try:
        url = f"{OLLAMA_HOST.rstrip('/')}/api/chat"
        payload = {
            "model": LOCAL_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 768}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )

        # Allow up to 180 seconds for deep, thorough CPU inference
        with urllib.request.urlopen(req, timeout=180.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                msg_content = data.get("message", {}).get("content", "").strip()
                if msg_content:
                    return msg_content
    except Exception as e:
        logger.warning(f"LLM deep research synthesis failed: {e}")

    return ""

def _format_fallback_report(topic: str, results: List[Dict[str, str]]) -> str:
    """Deterministic fallback formatter adhering strictly to user rules."""
    key_findings = []
    sources = []

    for idx, res in enumerate(results[:5], 1):
        t = res["title"]
        u = res["url"]
        s = res["snippet"]
        sources.append(f"{idx}. {t} — {u}")
        if s and len(key_findings) < 5:
            key_findings.append(f"- Source {idx} ({t}): {s}")

    if results:
        top_snippet = results[0]["snippet"]
        summary_text = f"Analysis of {topic.title()}: {top_snippet[:220].rstrip('.')}."
    else:
        summary_text = "Not enough information found."

    lines = [
        f"TOPIC: {topic}\n",
        "## Summary",
        summary_text,
        "\n## Key Findings"
    ]

    if key_findings:
        lines.extend(key_findings)
    else:
        lines.append("- Not enough information found")

    lines.append("\n## Sources")
    lines.extend(sources)

    return "\n".join(lines)

def perform_deep_research(topic: str) -> Dict[str, Any]:
    """
    Perform deep web research on a topic, synthesize thorough findings,
    and save a structured markdown research report adhering strictly to user format rules.
    """
    clean_topic = topic.strip()
    if not clean_topic:
        return {"success": False, "message": "Research topic cannot be empty"}

    logger.info(f"Initiating Thorough Deep Research on topic: '{clean_topic}'")

    # Clean query for search APIs
    search_query = re.sub(r'^(?:which|what|how|where|should i buy|can i|get me info on|do research on)\s+', '', clean_topic, flags=re.IGNORECASE).strip() or clean_topic

    # Gather comprehensive multi-source web results
    results = _query_duckduckgo_web(search_query)
    if len(results) < 4:
        results.extend(_query_duckduckgo_api(search_query))
        results.extend(_query_wikipedia(search_query))

    # Format source notes block: [Source N: title/url] — extracted text or summary
    source_notes_list = []
    sources_formatted = []
    key_findings_fallback = []
    for idx, item in enumerate(results, 1):
        source_notes_list.append(f"[Source {idx}: {item['title']} ({item['url']})] — {item['snippet']}")
        sources_formatted.append(f"{idx}. {item['title']} — {item['url']}")
        if len(key_findings_fallback) < 5:
            key_findings_fallback.append(f"- Source {idx} ({item['title']}): {item['snippet']}")

    source_notes_str = "\n".join(source_notes_list) if source_notes_list else "Not enough information found."

    # Perform Deep LLM synthesis with full token window
    report_body = _synthesize_with_llm(clean_topic, source_notes_str)

    # Fallback if synthesis times out or is empty
    if not report_body:
        report_body = _format_fallback_report(clean_topic, results)
    else:
        # Guarantee ## Key Findings section is present
        if "## Key Findings" not in report_body and key_findings_fallback:
            kf_block = "\n\n## Key Findings\n" + "\n".join(key_findings_fallback)
            if "## Sources" in report_body:
                report_body = report_body.replace("## Sources", kf_block + "\n\n## Sources")
            else:
                report_body += kf_block

        # Guarantee ## Sources section has sources populated below it
        if "## Sources" not in report_body or report_body.rstrip().endswith("## Sources"):
            report_body = re.sub(r'## Sources.*', '', report_body).strip()
            report_body += "\n\n## Sources\n" + "\n".join(sources_formatted)

    full_report = f"TOPIC: {clean_topic}\n\n" + report_body.replace(f"TOPIC: {clean_topic}\n", "").strip()

    # Save to Documents/Jarvis_Research/
    slug = re.sub(r'[^a-zA-Z0-9\_]+', '_', clean_topic.lower()).strip('_')[:40]
    filename = f"Research_{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_file = RESEARCH_DIR / filename

    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(full_report)
        
        spoken_summary = f"I've completed thorough deep research on {clean_topic}. I analyzed {len(results)} sources and saved the full report to your Documents folder."
        
        return {
            "success": True,
            "topic": clean_topic,
            "findings_count": len(results),
            "report_path": str(report_file),
            "report_content": full_report,
            "spoken_summary": spoken_summary,
            "message": f"Deep research completed! Full report saved to {report_file.name}"
        }
    except Exception as e:
        logger.error(f"Failed to save research report file: {e}")
        return {"success": False, "message": f"Error saving report: {e}"}
