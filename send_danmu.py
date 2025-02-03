
from credit import credential1,live_id
from bilibili_api import live, sync, Danmaku
import time,random

room_id = live_id

lived = live.LiveRoom(room_id,credential=credential1)
async def senddm(text):
            if len(text) > 3:
                  for i in range(0, len(text), 19):
                    result = text[i:i+19]
                    danmu = Danmaku(text=result)
                    try:
                        await lived.send_danmaku(danmu)
                        random_number = random.uniform(0.8, 1.3)
                        time.sleep(random_number)
                    except Exception as e:
                            print(e)         
            else:
                  print("弹幕内容过短，请重新输入！")

def go_dm(text):
      sync(senddm(text))
if __name__ == '__main__':
    text = input("请输入弹幕内容：")
    go_dm(text)
       