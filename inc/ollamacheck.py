# -*- coding: utf-8 -*-
"""
@ Author: b3nguang
@ Date: 2025-02-12 01:30:26
"""

import json
import sys

import requests
import requests.packages.urllib3
from termcolor import cprint

requests.packages.urllib3.disable_warnings()
outtime = 10


def Ollama_Check(url, proxies, header_new):
    cprint("[.] 正在进行Ollama的指纹识别", "cyan")
    check_status = 0
    test_url = str(url)
    r = requests.get(test_url, verify=False, timeout=outtime, headers=header_new, proxies=proxies)
    print(r.text)
    try:
        if ("Ollama" in r.text) and ("running" in r.text):
            ver_url = str(url) + "api/version"
            ver_r = requests.get(ver_url, verify=False, timeout=outtime, headers=header_new, proxies=proxies)
            containers = ver_r.json()
            ver = containers["version"]
            cprint("[+] 站点指纹符合Ollama特征，版本号为" + ver, "red")
            check_status = 1
        while check_status == 0:
            cprint("[-] 站点指纹不符合Ollama特征，可能不是Ollama框架", "yellow")
            break
    except KeyboardInterrupt:
        print("Ctrl + C 手动终止了进程")
        sys.exit()
    except Exception as e:
        print("[-] 发生错误，已记入日志error.log\n")
        f2 = open("error.log", "a")
        f2.write(str(e) + "\n")
        f2.close()


def check(url, proxies, header_new):
    header_new = json.loads(header_new)
    if "://" not in url:
        url = str("http://") + str(url)
    if str(url[-1]) != "/":
        url = url + "/"
    try:
        requests.packages.urllib3.disable_warnings()
        r = requests.get(url, verify=False, timeout=outtime, headers=header_new, proxies=proxies)
        if r.status_code == 503:
            sys.exit()
        else:
            Ollama_Check(url, proxies, header_new)
            return url
    except KeyboardInterrupt:
        print("Ctrl + C 手动终止了进程")
        sys.exit()
    except Exception as e:
        cprint("[-] URL为 " + url + " 的目标积极拒绝请求，予以跳过！已记入日志error.log", "magenta")
        f2 = open("error.log", "a")
        f2.write(str(e) + "\n")
        f2.close()
        sys.exit()
