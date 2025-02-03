import json
from rich.console import Console
from bilibili_api import live, sync
from credit import credential1,live_id
from send_danmu import go_dm
import queue
import threading
import socket
import time

# room_id = 11652599
room_id = live_id

credential = credential1
room = live.LiveDanmaku(room_id, credential=credential)
console = Console()
danmu = queue.Queue(maxsize=10)
rec_queue = queue.Queue(maxsize=10)

def send_messages(client_socket):
    try:
        while True:
            # 发送消息给客户端
            try:
                message = danmu.get()
                client_socket.sendall(message.encode('utf-8'))
            except queue.Empty:
                print('消息队列为空')
            except ConnectionResetError:
                print('客户端已断开连接，发送线程关闭')
                break
    except KeyboardInterrupt:
        print('发送线程关闭')
    except Exception as e:
        print(f'发送线程发生错误: {e}')
    finally:
        # 关闭连接
        client_socket.close()

def receive_messages(client_socket):
    try:
        while True:
            # 接收消息并存放到rec_queue
            data = client_socket.recv(1024)
            if not data:
                print('客户端断开连接')
                break
            if rec_queue.full():
                rec_queue.get()
            rec_queue.put(data.decode('utf-8'))
    except KeyboardInterrupt:
        print('接收线程关闭')
    except Exception as e:
        print(f'接收线程发生错误: {e}')
    finally:
        # 关闭连接
        client_socket.close()

def handle_client(client_socket, client_address):
    try:
        print(f"客户端 {client_address} 已连接")
        
        # 创建发送和接收线程
        send_thread = threading.Thread(target=send_messages, args=(client_socket,))
        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
        
        send_thread.daemon = True
        receive_thread.daemon = True
        
        send_thread.start()
        receive_thread.start()
        
        # 等待线程结束
        send_thread.join()
        receive_thread.join()
        
    except Exception as e:
        print(f"处理客户端 {client_address} 时发生错误: {str(e)}")
    finally:
        client_socket.close()

def start_server():
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置端口复用
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', 9999))
        server.listen(5)
        print("服务器启动，等待连接...")

        while True:
            try:
                client, addr = server.accept()
                # 为每个客户端创建一个新线程
                client_thread = threading.Thread(target=handle_client, args=(client, addr))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                print(f"接受客户端连接时发生错误: {str(e)}")

    except Exception as e:
        print(f"服务器启动失败: {str(e)}")
    finally:
        server.close()

@room.on('DANMU_MSG')
async def on_danmaku(event):
    user_info = event['data']['info'][0][15]
    uname = user_info['user']['base']['name']
    extra_dict = json.loads(user_info['extra'])
    content = extra_dict['content']
    console.print(f"[bold magenta]{uname}[/bold magenta]: [green]{content}[/green]", style="bold")
    # chat1 = uname + '说：' + content
    if danmu.full():
        danmu.get()
    if uname!= 'M9图给我':
        danmu.put(content)

def run_danmu():
    sync(room.connect())

def run_send_danmu():
    while True:
        if not rec_queue.empty():
            message = rec_queue.get()
            go_dm(message)

if __name__ == '__main__':
    thread1 = threading.Thread(target=run_danmu)
    thread2 = threading.Thread(target=start_server)
    thread3 = threading.Thread(target=run_send_danmu)

    thread1.start()
    thread2.start()
    thread3.start()

    thread1.join()
    thread2.join()
    thread3.join()
    
