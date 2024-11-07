import time
import requests
from plyer import notification
from datetime import datetime, timedelta

# APIのURL
api_urls = {
    "ナワバリバトル": "https://spla3.yuu26.com/api/regular/now",
    "バンカラマッチ：チャレンジ": "https://spla3.yuu26.com/api/bankara-challenge/now",
    "バンカラマッチ：オープン": "https://spla3.yuu26.com/api/bankara-open/now",
    "Xマッチ": "https://spla3.yuu26.com/api/x/now",
    "フェス": "https://spla3.yuu26.com/api/fes/now",  # フェスの追加
}

# 現在のステージ情報を取得する関数
def get_stage_info(url):
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        stages = data['results'][0]['stages']

        # ISO 8601形式の文字列をdatetimeオブジェクトに変換
        start_time = data['results'][0]['start_time']
        end_time = data['results'][0]['end_time']

        start_time = datetime.fromisoformat(start_time)
        end_time = datetime.fromisoformat(end_time)

        # フェスの場合、現在開催中であれば情報を返す
        if 'fes' in url and start_time <= datetime.now() <= end_time:
            return [stage['name'] for stage in stages], start_time, end_time
        # フェスが開催されていない場合はNoneを返す
        elif 'fes' in url:
            return None
        else:
            return [stage['name'] for stage in stages], start_time, end_time
    else:
        print(f"Failed to fetch data from {url}. Status code: {response.status_code}")
        return None

# 通知を送る関数
def send_schedule_notification(mode, stages, start_time, end_time, next_schedule=False):
    time_format = "%H:%M"
    time_range = f"{start_time.strftime(time_format)}～{end_time.strftime(time_format)}"

    if next_schedule:
        title = "【次のスケジュール】"
    else:
        title = "【スケジュールが更新されました】\n"

    message = f"\n\nルール名：【{mode}】\nステージ：【{'】\n　　　　【'.join(stages)}】\n{time_range}"

    # タイトルとメッセージの区別
    notification.notify(
        title=title,
        message=message,
        timeout=10,
        app_icon="icon.ico"  # アイコンのパス
    )

# スケジュール更新時に通知を送る関数
def check_for_changes():
    prev_schedules = {}

    # 各ルールごとにスケジュールを取得
    for mode, url in api_urls.items():
        result = get_stage_info(url)
        if result:
            stages, start_time, end_time = result
            prev_schedules[mode] = (stages, start_time, end_time)
        else:
            print(f"Skipping {mode} due to failed data fetch or no ongoing event.")

    # 最初のスケジュールを通知
    for mode, (stages, start_time, end_time) in prev_schedules.items():
        send_schedule_notification(mode, stages, start_time, end_time)

    while True:
        for mode, url in api_urls.items():
            current_info = get_stage_info(url)
            if current_info:
                current_stages, current_start_time, current_end_time = current_info
                if (current_stages != prev_schedules[mode][0] or
                        current_start_time != prev_schedules[mode][1] or
                        current_end_time != prev_schedules[mode][2]):

                    # 10分前に通知
                    if current_start_time - timedelta(minutes=10) <= datetime.now() <= current_start_time:
                        send_schedule_notification(mode, current_stages, current_start_time, current_end_time,
                                                   next_schedule=True)

                    # スケジュール更新
                    send_schedule_notification(mode, current_stages, current_start_time, current_end_time)

                    prev_schedules[mode] = (current_stages, current_start_time, current_end_time)
            else:
                print(f"Skipping {mode} due to failed data fetch or no ongoing event.")

        time.sleep(60)  # 60秒ごとに確認

# プログラム開始
if __name__ == "__main__":
    check_for_changes()
