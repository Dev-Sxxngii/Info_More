import time
import subprocess
import schedule

SPIDER_NAME = "naver"

def run_spider():
    start_time = time.localtime()
    format_start_time = time.strftime('%Y-%m-%d %I:%M:%S', start_time)
    print(f'{format_start_time} 크롤러 실행\n')
    subprocess.run(["scrapy", "crawl", SPIDER_NAME], check=True)
    end_time = time.localtime()
    format_end_time = time.strftime('%Y-%m-%d %I:%M:%S', end_time)
    print(f'{format_end_time} 크롤러 실행 완료\n\n\n')

if __name__ == "__main__":
    # 스케줄 등록
    schedule.every().day.at("00:00").do(run_spider)
    schedule.every().day.at("06:00").do(run_spider)
    schedule.every().day.at("12:00").do(run_spider)
    schedule.every().day.at("18:00").do(run_spider)

    # 무한 반복
    while True:
        schedule.run_pending()
        time.sleep(1)