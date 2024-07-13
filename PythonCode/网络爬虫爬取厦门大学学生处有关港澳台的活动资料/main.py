import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# 整体代码说明
# 这段代码是一个用于爬取厦门大学学生处(与港澳台学生相关的)通知页面及其附件的程序。它通过多线程处理加快了爬取速度。以下是代码实现的主要步骤和使用的知识点：
#
# 创建目录：用于存储下载的文件。
# 文件名清理：确保文件名合法。
# 下载附件：从通知页面下载附件并保存到指定目录。
# 网页请求：使用 requests 库请求网页内容，最多重试3次。
# 通知内容检查：检查通知内容是否包含特定关键字（如“港澳台”、“奖学金”、“奖金”、“奖项”）。
# 日期提取：从通知页面提取发布日期，并将其格式化为“YYYY-MM-DD”。
# 保存文本内容：将通知内容保存到文本文件中。
# HTML 转换为文本：将HTML内容转换为纯文本，并保留换行符。
# 处理通知页面：处理单个通知页面，提取信息并保存内容。如果通知日期为2020年或更早，程序将停止运行。
# 处理列表页面：处理通知列表页面，找到所有通知页面的链接，并并行处理每个通知页面。
# 主函数：创建线程池并处理所有页面列表，最大线程数为6。
# 整个程序通过多线程并行处理，极大地提高了爬取速度，并通过详细的错误处理和日志记录，确保程序在遇到问题时能够提供足够的信息以进行调试。

# 创建文件夹的函数
def create_dir(path):
    # 如果路径不存在，则创建一个新的目录
    if not os.path.exists(path):
        os.makedirs(path)
    print(f"创建目录: {path}")


# 清理文件名中的非法字符，以确保文件名合法
def sanitize_filename(filename):
    return re.sub(r'[\/:*?"<>|]', '-', filename)


# 下载附件文件并保存到指定目录
def download_attachment(url, folder_path, headers, filename):
    try:
        # 发送GET请求下载文件
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        # 检查下载的内容是否是HTML
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            print(f"错误: 下载的文件似乎是HTML而不是预期的附件: {url}")
            print(f"响应内容: {response.text[:500]}")  # 打印前500个字符以调试
            return

        # 清理文件名并保存文件到指定目录
        filename = sanitize_filename(filename)
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'wb') as file:
            # 分块写入文件
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        print(f"下载附件: {file_path}")
    except Exception as e:
        # 处理下载过程中出现的错误
        print(f"下载附件失败 {url}，错误: {e}")


# 请求指定的URL，最多重试3次
def fetch_url(url, headers, retries=3):
    for i in range(retries):
        try:
            # 发送GET请求
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            # 如果发生502错误，则重试
            if response.status_code == 502 and i < retries - 1:
                print(f"Error {e}, retrying ({i + 1}/{retries})...")
            else:
                raise
    return None


# 检查通知内容中是否包含关键字 '港澳台'
def is_valid_notice(content):
    return '港澳台' in content


# 检查通知内容中是否包含与奖金相关的关键词
def contains_bonus_keywords(content):
    return any(keyword in content for keyword in ['奖学金', '奖金', '奖项'])


# 从通知页面中提取发布日期，并将其格式化为 "YYYY-MM-DD"
def extract_date(notice_soup):
    date_tag = notice_soup.find(string=re.compile(r'发布时间：\d{4}年\d{2}月\d{2}日'))
    if date_tag:
        date = re.search(r'\d{4}年\d{2}月\d{2}日', date_tag).group()
        return date.replace('年', '-').replace('月', '-').replace('日', '')
    return 'Unknown Date'


# 将文本内容保存到指定目录中的文件
def save_text(content, folder_path, title):
    txt_path = os.path.join(folder_path, f"{sanitize_filename(title)}.txt")
    with open(txt_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"保存TXT文件: {txt_path}")


# 将HTML内容转换为纯文本，并保留换行符
def html_to_text_with_newlines(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # 将HTML中的换行符转换为文本中的换行符
    for br in soup.find_all('br'):
        br.replace_with('\n')

    # 在<p>和<div>标签后插入换行符
    for block in soup.find_all(['p', 'div']):
        block.insert_after('\n')

    return soup.get_text()


# 处理单个通知页面，提取信息并保存内容
def process_notice_page(notice_url, headers):
    print(f"请求通知页面: {notice_url}")

    try:
        # 请求通知页面的内容
        notice_response = fetch_url(notice_url, headers=headers)
        if not notice_response:
            raise Exception("无法请求通知页面")
        notice_response.encoding = notice_response.apparent_encoding
    except Exception as e:
        # 处理请求过程中出现的错误
        print(f"无法请求通知页面 {notice_url}，错误: {e}")
        return

    # 解析通知页面的内容
    notice_soup = BeautifulSoup(notice_response.text, 'html.parser')

    # 提取发布日期
    date = extract_date(notice_soup)
    print(f"通知发布日期: {date}")

    # 如果发布日期为2020年或更早，停止程序
    if re.match(r'2020-\d{2}-\d{2}', date) or date < '2020':
        print("遇到2020年或更早的通知，停止程序。")
        sys.exit(0)

    # 提取通知内容并转换为纯文本
    content_div = notice_soup.find('div', class_='v_news_content')
    content = html_to_text_with_newlines(str(content_div)) if content_div else ''

    print(f"检查通知内容是否包含 '港澳台': {'港澳台' in content}")

    # 如果通知内容包含 '港澳台'
    if is_valid_notice(content):
        title = notice_soup.find('title').text.strip()
        folder_name = f"[{date}] {title}"
        if contains_bonus_keywords(content):
            folder_name += " (有奖金)"
        folder_name = sanitize_filename(folder_name)
        folder_path = os.path.join('Data', folder_name)
        create_dir(folder_path)

        # 保存通知内容到文件
        full_content = title + '\n' + content
        save_text(full_content, folder_path, title)

        # 下载通知中的所有附件
        for attachment in content_div.find_all('a', href=True):
            if '附件' in attachment.text:
                attachment_url = urljoin(notice_url, attachment['href'])
                filename = attachment.text.strip()
                print(f"生成的下载链接: {attachment_url}")
                download_attachment(attachment_url, folder_path, headers, filename)


# 处理通知列表页面，找到所有通知页面的链接，并并行处理每个通知页面
def process_list_page(list_url, headers, executor):
    print(f"请求列表页面: {list_url}")

    try:
        # 请求列表页面的内容
        list_response = fetch_url(list_url, headers=headers)
        if not list_response:
            raise Exception("无法请求列表页面")
        list_response.encoding = list_response.apparent_encoding
    except Exception as e:
        # 处理请求过程中出现的错误
        print(f"无法请求列表页面 {list_url}，错误: {e}")
        return

    # 解析列表页面的内容
    list_soup = BeautifulSoup(list_response.text, 'html.parser')

    futures = []
    # 查找所有通知页面的链接，并提交给线程池处理
    for notice in list_soup.find_all('a', href=True):
        notice_url = urljoin(list_url, notice['href'])
        if notice_url.startswith('https://xsc.xmu.edu.cn/info/1017/'):
            futures.append(executor.submit(process_notice_page, notice_url, headers))

    # 等待所有通知页面处理完成
    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            print(f"处理通知页面时出错: {e}")


# 主函数，创建线程池并处理所有页面列表
def main():
    # 基础URL
    base_url = "https://xsc.xmu.edu.cn/gztz"
    # 请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://xsc.xmu.edu.cn/info/1017/99181.htm'
    }

    # 创建一个线程池，最大线程数为6
    with ThreadPoolExecutor(max_workers=6) as executor:
        # 遍历所有页面
        for page_num in range(1, 444):
            if page_num == 1:
                url = f"{base_url}.htm"
            else:
                url = f"{base_url}/{444 - page_num}.htm"
            process_list_page(url, headers, executor)


if __name__ == "__main__":
    main()

print("所有页面的通知和附件下载完成。")
