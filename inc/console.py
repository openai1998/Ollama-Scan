# -*- coding: utf-8 -*-
"""
@ Author: b3nguang
@ Date: 2025-02-12 01:30:26
"""

import sys

from inc import exemption, fofa, hunter, ollamacheck, output, run, zoom


# 控制台-参数处理和程序调用
def Ollama_Scan_console(args, proxies, header_new):
    if args.url:
        exemption.Disclaimer()
        urlnew = ollamacheck.check(args.url, proxies, header_new)
        run.url(urlnew, proxies, header_new)
    if args.urlfile:
        exemption.Disclaimer()
        run.file(args.urlfile, proxies, header_new)
    if args.zoomeye:
        zoom.ZoomDowload(args.zoomeye, proxies)
    if args.fofa:
        fofa.FofaDowload(args.fofa, proxies)
    if args.hunter:
        hunter.HunterDowload(args.hunter, proxies)
    else:
        output.usage()
        sys.exit()
