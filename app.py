\
import streamlit as st
from datetime import datetime, date
from gnews import GNews
from dateutil import parser
import pandas as pd
import random
import time
import io

st.set_page_config(page_title="医药企业新闻调研工具", layout="wide")
st.title("📊 谷歌新闻调研工具")

st.markdown("""
本工具将从 **Google News** 抓取指定关键词在指定日期范围内的新闻，  
并生成 **Excel** 与 **HTML 报告** 供下载。  

**优点：**  
- 将 Daily Research 的工作流程化  
- 根据设置好的关键词挨个进行检索整理，节省人力成本  

**缺点：**  
- 整理的新闻来源仅限谷歌新闻  
- 若谷歌新闻查不到的信息，将无法收录  
""")


# -------------------------------
# 侧边栏设置
# -------------------------------
with st.sidebar:
    st.header("参数设置")
    default_keywords = [
        "辉瑞", "阿斯利康", "罗氏", "赛诺菲", "诺华", "诺和诺德", "拜耳",
        "强生", "武田", "默沙东", "默克", "葛兰素史克", "礼来",
        "勃林格殷格翰", "雅培", "美敦力", "百时美施贵宝", "欧加隆", "安捷伦", "赛默飞世尔"
    ]

    st.caption("可在下方自定义关键词（每行一个；留空则使用默认清单）：")
    custom_kw_text = st.text_area(
        "自定义关键词（可选）",
        value="",
        height=160,
        placeholder="例如：\n辉瑞\n阿斯利康\n罗氏"
    )

    if custom_kw_text.strip():
        selected_keywords = [k.strip() for k in custom_kw_text.splitlines() if k.strip()]
    else:
        selected_keywords = st.multiselect("选择要抓取的企业关键词：", default_keywords, default=default_keywords[:6])

    col_a, col_b = st.columns(2)
    with col_a:
        start_date = st.date_input("开始日期", date(2025, 8, 5))
    with col_b:
        end_date = st.date_input("结束日期", date(2025, 9, 8))

    max_results = st.slider("每个关键词最多抓取数量", min_value=10, max_value=100, value=30, step=10)

    pause_min = st.slider("请求间隔（秒，随机）—最小", 0.5, 5.0, 1.0, 0.5)
    pause_max = st.slider("请求间隔（秒，随机）—最大", 1.0, 8.0, 2.0, 0.5)

    only_title_contains_keyword = st.checkbox("只保留标题中包含关键词的新闻（推荐）", value=True)

# -------------------------------
# 校验参数
# -------------------------------
if start_date > end_date:
    st.error("开始日期不能晚于结束日期。请重新选择。")
    st.stop()

if not selected_keywords:
    st.warning("请选择或输入至少一个关键词。")
    st.stop()

# -------------------------------
# 运行按钮
# -------------------------------
run = st.button("🚀 开始抓取")

if run:
    gnews_client = GNews(language='zh', country='CN', max_results=int(max_results))

    collected_news = {kw: [] for kw in selected_keywords}
    seen_titles = set()
    seen_links = set()

    progress = st.progress(0)
    status = st.empty()

    total = len(selected_keywords)
    for idx, keyword in enumerate(selected_keywords, 1):
        status.write(f"🔍 抓取关键词：**{keyword}**（{idx}/{total}）")
        results = []
        # 简单重试
        for attempt in range(2):
            try:
                results = gnews_client.get_news(keyword) or []
                if results:
                    break
            except Exception as e:
                st.warning(f"⚠️ 第 {attempt+1} 次请求失败：{e}")

        for r in results:
            try:
                title = (r.get('title') or '').strip()
                link = r.get('url', '').strip()
                media = (r.get('publisher') or {}).get('title', '未知')

                date_str = r.get('published date')
                pub_date = None
                if date_str:
                    try:
                        pub_date = parser.parse(date_str)
                    except Exception:
                        pub_date = None

                pub_date_date = pub_date.date() if pub_date else datetime.today().date()

                if start_date <= pub_date_date <= end_date:
                    ok = True
                    if only_title_contains_keyword:
                        ok = (keyword.lower() in title.lower())
                    if ok and title and link and (title not in seen_titles) and (link not in seen_links):
                        news_item = {
                            'title': title,
                            'link': link,
                            'datetime': pub_date.strftime("%Y-%m-%d") if pub_date else "未知日期",
                            'media': media
                        }
                        collected_news[keyword].append(news_item)
                        seen_titles.add(title)
                        seen_links.add(link)
            except Exception as e:
                st.error(f"⚠️ 单条解析异常：{e}")
                continue

        # 进度与节流
        progress.progress(idx / total)
        wait = random.uniform(float(pause_min), float(pause_max))
        time.sleep(wait)

    st.success("✅ 抓取完成！")

    # 汇总表
    rows = []
    for company, news_list in collected_news.items():
        for news in news_list:
            rows.append({
                "企业名称": company,
                "发布媒体": news['media'],
                "发布时间": news['datetime'],
                "新闻标题": news['title'],
                "新闻链接": news['link']
            })

    if not rows:
        st.warning("⚠️ 没有抓取到符合条件的数据。请尝试扩大日期范围或放宽条件。")
        st.stop()

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    # 导出 Excel
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    st.download_button(
        label="📥 下载 Excel",
        data=excel_buffer.getvalue(),
        file_name=f"新闻筛选结果_{start_date}_to_{end_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 生成 HTML 报告
    def build_html(collected, start_date, end_date):
        html_parts = []
        html_parts.append("""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>新闻简报</title>
<style>
    body { font-family: 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', Arial, sans-serif; margin: 40px auto; max-width: 900px; line-height: 1.6; color: #333; }
    h1 { text-align: center; color: #2c3e50; }
    h2 { margin-top: 32px; border-bottom: 2px solid #34495e; padding-bottom: 8px; color: #34495e; }
    h3 { margin: 16px 0 10px; color: #3498db; border-left: 4px solid #3498db; padding-left: 10px;}
    ul { list-style: none; padding-left: 0; }
    li { background-color: #f8f9f9; border: 1px solid #e1e8ed; padding: 10px 15px; margin-bottom: 10px; border-radius: 6px; }
    a { text-decoration: none; color: #007acc; font-weight: bold; }
    a:hover { text-decoration: underline; }
    small { color: #888; font-size: 0.9em; }
    .summary { text-align: center; font-size: 1.05em; color: #555; background-color: #ecf0f1; padding: 12px; border-radius: 6px; margin-bottom: 24px; }
</style>
</head>
<body>""")
        html_parts.append(f"<h1>新闻简报<br><small>{start_date} 至 {end_date}</small></h1>\n")
        html_parts.append("<h2>详细新闻列表</h2>\n")
        for keyword, news_list in collected.items():
            if news_list:
                html_parts.append(f"<h3>{keyword}</h3>\n<ul>\n")
                for item in news_list:
                    html_parts.append("<li>")
                    html_parts.append(f"<a href='{item['link']}' target='_blank'>{item['title']}</a><br>")
                    html_parts.append(f"<small>{item['datetime']} ｜ {item['media']}</small>")
                    html_parts.append("</li>\n")
                html_parts.append("</ul>\n")
            else:
                html_parts.append(f"<h3>{keyword}</h3><p>⚠️ 没有抓取到新闻</p>\n")
        html_parts.append("</body>\n</html>")
        return "".join(html_parts)

    html_content = build_html(collected_news, start_date, end_date)
    st.download_button(
        label="📥 下载 HTML 报告",
        data=html_content.encode("utf-8"),
        file_name=f"新闻筛选结果_{start_date}_to_{end_date}.html",
        mime="text/html"
    )

    with st.expander("查看分组结果（按企业）"):
        for kw, news_list in collected_news.items():
            st.subheader(kw)
            if news_list:
                tmp_df = pd.DataFrame(news_list)
                st.dataframe(tmp_df, use_container_width=True)
            else:
                st.caption("无数据")
