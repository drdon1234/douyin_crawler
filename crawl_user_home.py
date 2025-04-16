import requests
import time
import json

def crawl_douyin_videos(user_home_link, video_type="favorite", max_cursor="0", count="100"):
    has_more = 1
    max_retries = 3
    if video_type.lower() == "post":
        base_url = "https://www.douyin.com/aweme/v1/web/aweme/post/"
        print("正在爬取用户发布的视频...")
    else:
        base_url = "https://www.douyin.com/aweme/v1/web/aweme/favorite/"
        print("正在爬取用户收藏的视频...")
    with open(f'aweme_ids_{video_type}.txt', 'a', encoding='utf-8') as f:
        while has_more:
            for _ in range(max_retries):
                try:
                    response = requests.get(
                        url=base_url,
                        params={
                            "device_platform": "webapp",
                            "aid": "6383",
                            "sec_user_id": "",
                            "max_cursor": max_cursor,
                            "count": count,
                        },
                        headers={
                            "User-Agent": "Mozilla/5.0",
                            "Cookie": "",
                            "Referer": user_home_link
                        },
                        timeout=10
                    )
                    if response.status_code != 200:
                        print(f"请求失败，状态码：{response.status_code}")
                        continue
                    data = response.json()
                    for index, video in enumerate(data.get('aweme_list', [])):
                        aweme_id = video.get('aweme_id')
                        if aweme_id:
                            f.write(f"{aweme_id}\n")
                            f.flush()
                            print(
                                f"[{index + 1}] 已保存aweme_id: {aweme_id}, video_url: https://www.douyin.com/video/{aweme_id}")
                    has_more = data.get('has_more', 0)
                    max_cursor = str(data.get('max_cursor', 0))
                    print(f"当前max_cursor: {max_cursor}, 剩余数据: {has_more}")
                    if not has_more:
                        print("没有更多数据了，爬取完成")
                        break
                    time.sleep(2)
                    break
                except requests.exceptions.RequestException as e:
                    print(f"网络请求异常: {e}")
                    time.sleep(5)
                except json.JSONDecodeError:
                    print("JSON解析失败，响应内容：", response.text)
                    time.sleep(5)
            else:
                print("达到最大重试次数，终止爬取")
                return


if __name__ == "__main__":
    user_home_link = input("请输入需要爬取用户的主页链接:\n")
    while True:
        video_type = input("请选择要爬取的内容类型 (作品: 1 | 喜欢: 2)\n")
        if video_type in ["1", "2"]:
            video_type = "post" if video_type == "1" else "favorite"
            break
        else:
            print("输入错误，请输入 1 或 2")
    try:
        count = input("请输入每次请求的数量(默认100，最大约50): ").strip()
        count = count if count.isdigit() else "10"
    except:
        count = "10"
    crawl_douyin_videos(user_home_link=user_home_link, video_type=video_type, count=count)
