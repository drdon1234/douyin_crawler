import aiohttp
import asyncio
import re
import json
from datetime import datetime

class DouyinParser:
    semaphore = asyncio.Semaphore(10)  # 类变量，所有实例共享

    def __init__(self, session):
        self.session = session
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'Referer': 'https://www.douyin.com/?is_from_mobile_home=1&recommend=1'
        }

    async def get_redirected_url(self, url):
        async with self.session.head(url, allow_redirects=True) as response:
            return str(response.url)

    def extract_router_data(self, text):
        # 定位 window._ROUTER_DATA
        start_flag = 'window._ROUTER_DATA = '
        start_idx = text.find(start_flag)
        if start_idx == -1:
            return None
        brace_start = text.find('{', start_idx)
        if brace_start == -1:
            return None
        # 用栈法匹配完整 JSON
        i = brace_start
        stack = []
        while i < len(text):
            if text[i] == '{':
                stack.append('{')
            elif text[i] == '}':
                stack.pop()
                if not stack:
                    return text[brace_start:i+1]
            i += 1
        return None

    async def fetch_video_info(self, video_id):
        url = f'https://www.iesdouyin.com/share/video/{video_id}/'
        try:
            async with self.session.get(url, headers=self.headers) as response:
                response_text = await response.text()
                json_str = self.extract_router_data(response_text)
                if not json_str:
                    print('未找到 _ROUTER_DATA')
                    return None
                # 处理转义
                json_str = json_str.replace('\\u002F', '/').replace('\\/', '/')
                try:
                    json_data = json.loads(json_str)
                except Exception as e:
                    print('JSON解析失败', e)
                    return None
                loader_data = json_data.get('loaderData', {})
                video_info = None
                for v in loader_data.values():
                    if isinstance(v, dict) and 'videoInfoRes' in v:
                        video_info = v['videoInfoRes']
                        break
                if not video_info or 'item_list' not in video_info or not video_info['item_list']:
                    print('未找到视频信息')
                    return None
                item = video_info['item_list'][0]
                nickname = item['author']['nickname']
                title = item['desc']
                timestamp = datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d')
                video_url = item['video']['play_addr']['url_list'][0]
                return {
                    'nickname': nickname,
                    'title': title,
                    'timestamp': timestamp,
                    'video_url': video_url,
                }
        except aiohttp.ClientError as e:
            print(f'请求错误：{e}')
            return None

    async def parse(self, url):
        async with self.semaphore:  # 使用类变量信号量
            redirected_url = await self.get_redirected_url(url)
            match = re.search(r'(\d+)', redirected_url)
            if match:
                video_id = match.group(1)
                return await self.fetch_video_info(video_id)
            else:
                return None

    @staticmethod
    def extract_video_links(input_text):
        douyin_video_pattern = r'https?://(?:www\.|v\.)?douyin\.com/(?:video/\d+|[^\s]+)'
        video_links = re.findall(douyin_video_pattern, input_text)
        return video_links

    async def parse_urls(self, urls):
        tasks = [self.parse(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

async def main():
    input_text = """
    9.71 a@a.nQ 02/11 Slp:/ # 肯恰那 https://v.douyin.com/5JJ_ZvXkGz0/ 复制此链接，打开Dou音搜索，直接观看视频！
    """

    urls = DouyinParser.extract_video_links(input_text)

    async with aiohttp.ClientSession() as session:
        parser = DouyinParser(session)
        results = await parser.parse_urls(urls)

        for url, result in zip(urls, results):
            if result:
                print(f"URL: {url}")
                print(f"作者：{result['nickname']}")
                print(f"标题：{result['title']}")
                print(f"发布时间：{result['timestamp']}")
                print(f"视频直链：{result['video_url']}\n\n")
            else:
                print(f"解析失败！URL: {url}")

if __name__ == "__main__":
    asyncio.run(main())
