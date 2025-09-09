\
# 医药企业新闻调研工具（Streamlit）

这是一个基于 Streamlit 的网页应用，抓取 Google News 上关于指定医药企业关键词、指定日期范围内的新闻，并导出 Excel 和 HTML 报告。

## 本地运行（可选）
1. 安装 Python 3.9+
2. 安装依赖：`pip install -r requirements.txt`
3. 运行：`streamlit run app.py`

## 部署到 Streamlit Cloud（免费）
1. 将 `app.py` 与 `requirements.txt` 上传到 GitHub 新仓库
2. 打开 https://share.streamlit.io/ -> New app -> 选择仓库与 `app.py`
3. 点击 Deploy，部署完成后会生成一个可分享的网址

## 使用
- 打开网页，选择关键词与时间范围，点击 **开始抓取**
- 抓取完成后可下载 **Excel** 与 **HTML** 报告
