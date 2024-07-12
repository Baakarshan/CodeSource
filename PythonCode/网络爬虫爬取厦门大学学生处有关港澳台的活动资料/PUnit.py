import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

# 这个代码使用来对单个页面进行调试的 调试好了之后再应用到一键爬取所有页面

def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    print(f"创建目录: {path}")

def sanitize_filename(filename):
    # 移除非法字符
    return re.sub(r'[\/:*?"<>|]', '-', filename)

def download_attachment(url, folder_path, headers, filename):
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        # 检查内容类型，确保不是HTML页面
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            print(f"错误: 下载的文件似乎是HTML而不是预期的附件: {url}")
            print(f"响应内容: {response.text[:500]}")  # 打印前500个字符以调试
            return

        filename = sanitize_filename(filename)  # 移除非法字符
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        print(f"下载附件: {file_path}")
    except Exception as e:
        print(f"下载附件失败 {url}，错误: {e}")

def fetch_url(url, headers, retries=3):
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if response.status_code == 502 and i < retries - 1:
                print(f"Error {e}, retrying ({i + 1}/{retries})...")
            else:
                raise
    return None

def is_valid_notice(content):
    return '港澳台' in content

def extract_date(notice_soup):
    date_tag = notice_soup.find(string=re.compile(r'发布时间：\d{4}年\d{2}月\d{2}日'))
    if date_tag:
        date = re.search(r'\d{4}年\d{2}月\d{2}日', date_tag).group()
        return date.replace('年', '-').replace('月', '-').replace('日', '')
    return 'Unknown Date'

def save_text(content, folder_path, title):
    txt_path = os.path.join(folder_path, f"{sanitize_filename(title)}.txt")
    with open(txt_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"保存TXT文件: {txt_path}")

def html_to_text_with_newlines(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    for br in soup.find_all('br'):
        br.replace_with('\n')

    for block in soup.find_all(['p', 'div']):
        block.insert_after('\n')

    return soup.get_text()

# 伪装请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://xsc.xmu.edu.cn/info/1017/99181.htm'
}

# 单元测试通知页面URL
notice_url = "https://xsc.xmu.edu.cn/info/1017/99181.htm"
print(f"请求通知页面: {notice_url}")

try:
    notice_response = fetch_url(notice_url, headers=headers)
    if not notice_response:
        raise Exception("无法请求通知页面")
    notice_response.encoding = notice_response.apparent_encoding  # 确保正确的编码方式
except Exception as e:
    print(f"无法请求通知页面 {notice_url}，错误: {e}")
    exit(1)

notice_soup = BeautifulSoup(notice_response.text, 'html.parser')

# 获取发布时间
date = extract_date(notice_soup)

# 获取正文内容并保留换行
content_div = notice_soup.find('div', class_='v_news_content')
content = html_to_text_with_newlines(str(content_div)) if content_div else ''

print(f"检查通知内容是否包含 '港澳台': {'港澳台' in content}")

if is_valid_notice(content):
    title = notice_soup.find('title').text.strip()
    folder_name = f"[{date}] {title}"
    folder_name = sanitize_filename(folder_name)  # 移除非法字符
    folder_path = os.path.join('Data', folder_name)
    create_dir(folder_path)

    full_content = title + '\n' + content
    save_text(full_content, folder_path, title)

    for attachment in content_div.find_all('a', href=True):
        if '附件' in attachment.text:
            attachment_url = urljoin(notice_url, attachment['href'])
            filename = attachment.text.strip()
            print(f"生成的下载链接: {attachment_url}")
            # 下载并保存附件
            download_attachment(attachment_url, folder_path, headers, filename)

print("通知和附件下载完成。")
