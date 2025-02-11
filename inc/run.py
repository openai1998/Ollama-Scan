import json
import random
import sys
from datetime import datetime
from time import sleep

import pytz
import requests
import requests.packages.urllib3
from openai import OpenAI
from requests.exceptions import RequestException
from rich.console import Console
from rich.table import Table
from termcolor import cprint

requests.packages.urllib3.disable_warnings()
outtime = 10

ua = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36,Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36,Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.17 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36,Mozilla/5.0 (X11; NetBSD) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/44.0.2403.155 Safari/537.36",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0",
    "Opera/9.80 (Windows NT 5.1; U; zh-sg) Presto/2.9.181 Version/12.00",
]


def JSON_handle(header1, header2):
    dict1 = json.loads(str(header1).replace("'", '"'))
    dict2 = json.loads(str(header2).replace("'", '"'))
    # 合并两个字典
    merged_dict = {**dict1, **dict2}
    # 将合并后的字典转换为 JSON 字符串
    result_json = json.dumps(merged_dict, indent=2)
    return result_json


def create_exec(urllist, command, proxies):
    print(command)
    if command.startswith("use"):
        model = command.split()[1]
        client = OpenAI(api_key="ollama", base_url=f"{urllist}v1")

        # Initialize chat history
        messages = [{"role": "system", "content": "You are a helpful assistant"}]

        # Initial greeting
        cprint(f"\n[+] 已连接到模型 {model}", "green")
        cprint("[i] 输入 'exit' 或 'quit' 退出对话", "cyan")
        cprint("[i] 输入 'clear' 清空对话历史\n", "cyan")

        while True:
            try:
                # Get user input with prompt
                user_input = input("\n🤔 You: ")

                # Check for exit commands
                if user_input.lower() in ["exit", "quit"]:
                    cprint("\n[i] 退出对话", "yellow")
                    break

                # Check for clear history command
                if user_input.lower() == "clear":
                    messages = [{"role": "system", "content": "You are a helpful assistant"}]
                    cprint("\n[i] 对话历史已清空", "yellow")
                    continue

                # Add user message to history
                messages.append({"role": "user", "content": user_input})

                # Get AI response
                cprint("\n🤖 Assistant: ", "green", end="")
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=False,
                )

                # Print response and add to history
                ai_response = response.choices[0].message.content
                print(ai_response)
                messages.append({"role": "assistant", "content": ai_response})

            except KeyboardInterrupt:
                cprint("\n\n[i] 用户中断，退出对话", "yellow")
                break
            except Exception as e:
                cprint(f"\n[-] 错误: {str(e)}", "red")
                continue
    else:
        try:
            url = urllist + f"api/{command}"
            response = requests.get(url, proxies=proxies)
            if response.status_code == 200:
                if command == "ps":
                    data = response.json()
                    # print(data)
                    if "models" in data and data["models"]:
                        console = Console()
                        table = Table(show_header=True, header_style="bold cyan", title="[bold cyan]Model Details")

                        # Add columns
                        table.add_column("ID", style="bright_black", width=12)
                        table.add_column("名称", style="cyan")
                        table.add_column("参数量", style="green", justify="right")
                        table.add_column("量化", style="yellow")
                        table.add_column("格式", style="magenta")
                        table.add_column("显存", style="blue", justify="right")
                        table.add_column("过期时间", style="red")

                        for model in data["models"]:
                            # Format data
                            model_id = model["digest"][:12]
                            name = model["name"]
                            param_size = model["details"].get("parameter_size", "N/A")
                            quant = model["details"].get("quantization_level", "N/A")
                            format_type = model["details"].get("format", "N/A")

                            # Format VRAM size
                            vram = model.get("size_vram", 0)
                            if vram > 1024 * 1024 * 1024:
                                vram_str = f"{vram / (1024 * 1024 * 1024):.1f}GB"
                            else:
                                vram_str = f"{vram / (1024 * 1024):.1f}MB"

                            # Format expiry time
                            try:
                                expires = datetime.fromisoformat(model["expires_at"])
                                now = datetime.now(pytz.timezone("Asia/Shanghai"))
                                diff = expires - now
                                if diff.days > 0:
                                    expires_str = f"{diff.days}天后"
                                elif diff.seconds > 3600:
                                    expires_str = f"{diff.seconds // 3600}小时后"
                                else:
                                    expires_str = f"{diff.seconds // 60}分钟后"
                            except:
                                expires_str = "N/A"

                            table.add_row(model_id, name, param_size, quant, format_type, vram_str, expires_str)

                        # Print table
                        console.print("\n")
                        console.print(table)
                        return None
                else:
                    print(response.json())
                return None
            else:
                cprint("\n[-] 创建命令执行失败，状态码:" + str(response.status_code), "magenta")
                print(response.text)
                return None
        except RequestException as e:
            cprint(f"\n[-] 连接出现异常: {e}", "red")
            return None


def url(urllist, proxies, header_new):
    cprint("\n====== Ollama Model Scanner ======", "cyan")
    header = {"User-Agent": random.choice(ua)}
    newheader = json.loads(str(JSON_handle(header, header_new)).replace("'", '"'))
    urlnew = urllist + "/api/tags"
    try:
        response = requests.get(url=urlnew, headers=newheader, timeout=outtime, allow_redirects=False, verify=False, proxies=proxies)
        if (response.status_code == 200) and ("models" in response.text):
            containers = response.json()
            if containers:
                # Create and configure table
                console = Console()
                table = Table(show_header=True, header_style="bold cyan", title="[bold cyan]Available Models")
                table.add_column("ID", style="bright_black", width=12)
                table.add_column("名称/标签", style="cyan")
                table.add_column("大小", style="green", justify="right")
                table.add_column("创建时间", style="yellow")

                # Add rows to table
                for container in containers["models"]:
                    # Generate a short ID (similar to Docker's short hash)
                    short_id = container.get("digest", "")[:12] if container.get("digest") else "N/A"

                    # Format size (similar to docker images output)
                    size = container.get("size", 0)
                    if size > 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024 * 1024):.2f}GB"
                    else:
                        size_str = f"{size / (1024 * 1024):.2f}MB"

                    # Format name and tags
                    name = container["name"]

                    # Format timestamp
                    try:
                        dt = datetime.fromisoformat(container["modified_at"])
                        # Get current time
                        now = datetime.now(pytz.timezone("Asia/Shanghai"))
                        diff = now - dt

                        if diff.days > 30:
                            time_str = dt.strftime("%Y-%m-%d %H:%M")
                        elif diff.days > 0:
                            time_str = f"{diff.days} days ago"
                        elif diff.seconds > 3600:
                            hours = diff.seconds // 3600
                            time_str = f"{hours} hours ago"
                        elif diff.seconds > 60:
                            minutes = diff.seconds // 60
                            time_str = f"{minutes} minutes ago"
                        else:
                            time_str = f"{diff.seconds} seconds ago"
                    except (ValueError, TypeError):
                        time_str = container["modified_at"]

                    table.add_row(short_id, name, size_str, time_str)

                # Print the table
                console.print("\n")
                console.print(table)

                cprint("\n[i] 可用命令:", "cyan")
                cprint("    ps                显示所有模型", "cyan")
                cprint("    use <model>       使用指定模型进行对话", "cyan")
                # cprint("    pull <model>      拉取指定模型", "cyan")
                # cprint("    rm <model>        删除指定模型", "cyan")
                # cprint("    info <model>      查看模型详细信息", "cyan")
                cprint("    exit              退出程序", "cyan")

                while True:
                    command = input("\n[?] ollama> ").strip()
                    if not command:
                        continue

                    cmd_parts = command.split()
                    cmd_type = cmd_parts[0].lower()

                    if cmd_type == "exit":
                        cprint("\n[-] 退出程序", "yellow")
                        sys.exit()
                    elif cmd_type in ["use", "ps"]:
                        # if len(cmd_parts) < 2:
                        #     cprint("\n[-] 错误: 请指定模型名称", "red")
                        #     continue
                        create_exec(urllist, command, proxies)
                    else:
                        cprint("\n[-] 未知命令。使用以下命令: use, ps, exit", "yellow")
            else:
                cprint("\n[-] 没有模型被读取到", "red")
        else:
            cprint(f"\n[-] 连接失败，状态码: {response.status_code}", "red")
    except KeyboardInterrupt:
        cprint("\n[-] Ctrl + C 手动终止了进程", "yellow")
        sys.exit()
    except RequestException as e:
        cprint(f"\n[-] 连接出现异常: {e}", "red")
    except Exception:
        cprint(f"\n[-] URL为 {urllist} 的目标积极拒绝请求，予以跳过！", "red")
    sys.exit()


def file(filename, proxies, header_new):
    f1 = open("output.txt", "wb+")
    f1.close()
    cprint("\n====== 开始尝试读取目标TXT内是否存在Docker敏感端点 ======", "cyan")
    sleeps = input("\n[?] 是否要延时扫描 (默认0.2秒): ")
    if sleeps == "":
        sleeps = "0.2"
    with open(filename, "r") as temp:
        for url in temp.readlines():
            url = url.strip()
            if "://" not in url:
                url = str("http://") + str(url)
            # if str(url[-1]) != "/":
            #     u = url + "/containers/json?all=true"
            # else:
            #     u = url + "containers/json?all=true"
            header = {"User-Agent": random.choice(ua)}
            newheader = json.loads(str(JSON_handle(header, header_new)).replace("'", '"'))
            try:
                requests.packages.urllib3.disable_warnings()
                r = requests.get(url=url, headers=newheader, timeout=outtime, allow_redirects=False, verify=False, proxies=proxies)
                sleep(int(float(sleeps)))
                if (r.status_code == 200) and ("Ollama" in r.text) and ("running" in r.text):
                    cprint("\n[+] 发现Ollama端点泄露，URL: " + url + " " + "页面长度为:" + str(len(r.content)), "green")
                    f2 = open("output.txt", "a")
                    f2.write(url + "\n")
                    f2.close()
                elif r.status_code == 200:
                    cprint("\n[+] 状态码%d" % r.status_code + " " + "但无法获取信息 URL为:" + url, "cyan")
                else:
                    cprint("\n[-] 状态码%d" % r.status_code + " " + "无法访问URL为:" + url, "yellow")
            except KeyboardInterrupt:
                cprint("\n[-] Ctrl + C 手动终止了进程", "yellow")
                sys.exit()
            except Exception as e:
                cprint("\n[-] URL " + url + " 连接错误，已记入日志error.log", "red")
                f2 = open("error.log", "a")
                f2.write(str(e) + "\n")
                f2.close()
    count = len(open("output.txt", "r").readlines())
    if count >= 1:
        cprint("\n[+] 发现目标TXT内存在Ollama敏感端点泄露，已经导出至 output.txt ，共%d行记录" % count, "green")
    sys.exit()
