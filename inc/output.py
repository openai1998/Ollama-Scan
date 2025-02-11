# -*- coding: utf-8 -*-
"""
@ Author: b3nguang
@ Date: 2025-02-12 01:30:26
"""


def logo():
    logo0 = r"""
  ____  ____                    ____            
 / __ \/ / /__ ___ _  ___ _____/ __/______ ____ 
/ /_/ / / / _ `/  ' \/ _ `/___/\ \/ __/ _ `/ _ \
\____/_/_/\_,_/_/_/_/\_,_/   /___/\__/\_,_/_//_/
           [+]Version: 1.0   [+] Author: 本光(@b3nguang)
"""
    print(logo0)


def usage():
    print("""
用法:
        对单一URL进行Ollama端点探测:       python3 Ollama-Scan.py -u http://example.com/
        读取目标TXT进行Ollama端点探测:     python3 Ollama-Scan.py -uf url.txt
        使用HTTP代理并自动进行连通性测试:    python3 Ollama-Scan.py -p <代理IP:端口>
        从TXT文件中导入自定义HTTP头部:       python3 Ollama-Scan.py -t header.txt
        通过ZoomEye密钥进行API下载数据:      python3 Ollama-Scan.py -z <ZoomEye的API-KEY>
        通过Fofa密钥进行API下载数据:         python3 Ollama-Scan.py -f <Fofa的API-KEY>
        通过Hunter密钥进行API下载数据:       python3 Ollama-Scan.py -y <Hunter的API-KEY>

免责声明：
        1.如果您下载、安装、使用、修改本工具及相关代码，即表明您信任本工具
        2.在使用本工具时造成对您自己或他人任何形式的损失和伤害，我们不承担任何责任
        3.如您在使用本工具的过程中存在任何非法行为，您需自行承担相应后果，我们将不承担任何法律及连带责任
        4.请您务必审慎阅读、充分理解各条款内容，特别是免除或者限制责任的条款，并选择接受或不接受
        5.除非您已阅读并接受本协议所有条款，否则您无权下载、安装或使用本工具
        6.您的下载、安装、使用等行为即视为您已阅读并同意上述协议的约束
        """)
