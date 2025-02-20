# -*- coding: utf-8 -*-
"""
@ Author: b3nguang
@ Date: 2025-02-18 12:04:37
"""

import argparse
import re
import sys
from typing import List, Tuple
import logging
import subprocess

from ollama import Client
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.style import Style
from rich.table import Table
from httpx import Timeout, HTTPError, ReadTimeout


class OllamaShell:
    def __init__(self, host: str = None):
        if not host:
            raise ValueError("必须提供 Ollama 服务器地址")
        if not host.startswith(("http://", "https://")):
            raise ValueError("服务器地址必须以 http:// 或 https:// 开头")
        
        # 保存 host 地址
        self.host = host
        
        # 根据协议决定是否验证证书
        self.verify_ssl = not (host.startswith("https://") and ":" in host.split("://")[1].split("/")[0])
        
        self.client = Client(
            host=host,
            timeout=Timeout(30.0),
            verify=self.verify_ssl
        )
        self.console = Console()
        self.commands = {
            "list": (self.list_models, "📃 列出可用模型"),
            "pull": (self.pull_model, "📥 拉取模型"),
            "show": (self.show_model, "🔍 显示模型详情"),
            "chat": (self.chat_with_model, "💬 与模型对话"),
            "ps": (self.show_processes, "⚡️ 显示运行中的模型"),
            "help": (self.show_help, "❓ 显示帮助信息"),
            "exit": (self.exit_shell, "🚪 退出程序"),
            "rm": (self.delete_model, "🗑️ 删除指定模型"),
            "version": (self.show_version, "📌 显示版本信息"),
        }

    def list_models(self, *args: List[str]) -> None:
        """列出所有可用的模型"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]获取模型列表..."),
                transient=True,
            ) as progress:
                progress.add_task("fetch")
                models = self.client.list()
                # self.console.print(
                #     f"[dim]DEBUG: type={type(models)}, value={models}[/dim]"
                # )
            table = Table(
                title="📃 可用模型列表",
                show_header=True,
                header_style="bold magenta",
                show_lines=True,
            )
            table.add_column("🤖 模型名称", style="cyan")
            table.add_column("💾 大小", justify="right", style="green")
            table.add_column("📅 修改时间", justify="right", style="yellow")
            table.add_column("📋 格式", style="magenta")
            table.add_column("🧩 参数量", style="blue")
            table.add_column("🏷️ 量化等级", style="red")

            if not models:
                self.console.print("[red]❗️ 未找到模型[/red]")
                return

            # 处理模型列表
            if hasattr(models, "models"):
                model_list = models.models
            elif isinstance(models, list):
                model_list = models
            else:
                self.console.print(f"[yellow]⚠️ 返回值格式异常: {models}[/yellow]")
                return

            for model in model_list:
                try:
                    # 获取基本信息
                    name = model.model
                    size = model.size
                    modified = model.modified_at
                    details = model.details

                    # 格式化大小
                    size_str = f"{size / (1024 * 1024 * 1024):.1f}GB" if size else "Unknown"

                    # 格式化时间
                    modified_str = modified.strftime("%Y-%m-%d %H:%M") if modified else "Unknown"

                    # 获取详细信息
                    format_str = details.format if details else "Unknown"
                    param_size = details.parameter_size if details else "Unknown"
                    quant_level = details.quantization_level if details else "Unknown"

                    # 添加到表格
                    table.add_row(
                        name,
                        size_str,
                        modified_str,
                        format_str,
                        str(param_size),
                        str(quant_level),
                    )

                except Exception as e:
                    self.console.print(f"[yellow]⚠️ 警告: 处理模型信息时出错: {str(e)}[/yellow]")
                    continue

            self.console.print(table)

        except ConnectionError:
            self.console.print("[red]连接服务器失败[/red]")
        except TimeoutError:
            self.console.print("[red]请求超时[/red]")
        except HTTPError as e:
            self.console.print(f"[red]HTTP 错误: {e.response.status_code}[/red]")
        except Exception as e:
            self.console.print("[red]发生未知错误[/red]")
            logging.error(f"Unexpected error: {str(e)}")

    def pull_model(self, *args: List[str]) -> None:
        """拉取指定的模型"""
        if not args:
            self.console.print("[red]错误: 请指定模型名称[/red]")
            return

        model_name = args[0]
        # 修改模型名称验证，允许更多字符
        if not re.match(r'^[a-zA-Z0-9_\-\./:]+$', model_name):
            self.console.print("[red]错误: 模型名称包含非法字符[/red]")
            return

        self.console.print(f"\n[bold]📥 开始拉取模型: {model_name}[/bold]")

        try:
            with Progress(TextColumn("[bold blue]{task.description}"), transient=False) as progress:
                task = progress.add_task("拉取中...", total=None)
                for info in self.client.pull(model_name, stream=True):
                    if "status" in info:
                        progress.update(task, description=f"状态: {info['status']}")
                    if "completed" in info:
                        progress.update(
                            task,
                            description=f"进度: {info['completed']}/{info['total']} layers",
                        )
            self.console.print("[green]✅ 模型拉取完成！[/green]")

        except ConnectionError:
            self.console.print("[red]连接服务器失败[/red]")
        except TimeoutError:
            self.console.print("[red]请求超时[/red]")
        except HTTPError as e:
            self.console.print(f"[red]HTTP 错误: {e.response.status_code}[/red]")
        except Exception as e:
            self.console.print("[red]发生未知错误[/red]")
            logging.error(f"Unexpected error: {str(e)}")

    def show_model(self, *args: List[str]) -> None:
        """显示模型详细信息"""
        if not args:
            self.console.print("[red]错误: 请指定模型名称[/red]")
            return

        model_name = args[0]
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn(f"[bold blue]获取模型 {model_name} 的信息..."),
                transient=True,
            ) as progress:
                progress.add_task("fetch")
                info = self.client.show(model_name)
                # self.console.print(f"[dim]DEBUG: type={type(info)}, value={info}[/dim]")
            # 构建基本信息
            basic_info = (
                f"\n[bold cyan]模型名称:[/bold cyan] {model_name}\n"
                + f"[bold yellow]修改时间:[/bold yellow] {info.modified_at.strftime('%Y-%m-%d %H:%M')}\n"
                + f"[bold magenta]格式:[/bold magenta] {info.details.format}\n"
                + f"[bold blue]参数量:[/bold blue] {info.details.parameter_size}\n"
                + f"[bold red]量化等级:[/bold red] {info.details.quantization_level}\n"
            )

            # 添加模型信息
            if hasattr(info, "modelinfo") and info.modelinfo:
                model_info_str = "\n[bold white]模型信息:[/bold white]\n"
                for key, value in info.modelinfo.items():
                    model_info_str += f"  {key}: {value}\n"
                basic_info += model_info_str

            # 添加许可证信息
            if hasattr(info, "license") and info.license:
                basic_info += f"\n[bold white]许可证:[/bold white]\n{info.license}\n"

            panel = Panel.fit(
                basic_info,
                title=f"模型详情 - {model_name}",
                border_style="blue",
            )
            self.console.print(panel)

        except ConnectionError:
            self.console.print("[red]连接服务器失败[/red]")
        except TimeoutError:
            self.console.print("[red]请求超时[/red]")
        except HTTPError as e:
            self.console.print(f"[red]HTTP 错误: {e.response.status_code}[/red]")
        except Exception as e:
            self.console.print("[red]发生未知错误[/red]")
            logging.error(f"Unexpected error: {str(e)}")

    def show_processes(self, *args: List[str]) -> None:
        """显示运行中的模型进程"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]获取运行中的模型..."),
                transient=True,
            ) as progress:
                progress.add_task("fetch")
                response = self.client.ps()

            if not response or not hasattr(response, "models") or not response.models:
                self.console.print("[yellow]⚠️ 没有正在运行的模型[/yellow]")
                return

            table = Table(
                title="⚡️ 运行中的模型",
                show_header=True,
                header_style="bold magenta",
                show_lines=True,
            )
            table.add_column("🤖 模型名称", style="cyan")
            table.add_column("💾 模型大小", style="green")
            table.add_column("📂 格式", style="yellow")
            table.add_column("🧩 参数量", style="blue")
            table.add_column("🏷️ 量化等级", style="red")
            table.add_column("⏳ 过期时间", style="magenta")

            for model in response.models:
                # 格式化大小（转换为GB）
                size_gb = model.size / (1024 * 1024 * 1024)
                size_str = f"{size_gb:.1f}GB"

                # 格式化过期时间
                expires_str = model.expires_at.strftime("%Y-%m-%d %H:%M:%S") if model.expires_at else "Unknown"

                table.add_row(
                    model.name,
                    size_str,
                    model.details.format if model.details else "Unknown",
                    model.details.parameter_size if model.details else "Unknown",
                    model.details.quantization_level if model.details else "Unknown",
                    expires_str,
                )

            self.console.print(table)

        except ConnectionError:
            self.console.print("[red]连接服务器失败[/red]")
        except TimeoutError:
            self.console.print("[red]请求超时[/red]")
        except HTTPError as e:
            self.console.print(f"[red]HTTP 错误: {e.response.status_code}[/red]")
        except Exception as e:
            self.console.print("[red]发生未知错误[/red]")
            logging.error(f"Unexpected error: {str(e)}")

    def chat_with_model(self, *args: List[str]) -> None:
        """与模型进行对话"""
        if not args:
            self.console.print("[red]错误: 请指定模型名称[/red]")
            return

        model_name = args[0]
        self.console.print(f"\n[bold]💬 开始与 {model_name} 对话[/bold]")
        self.console.print("[dim]🚪 输入 'exit' 结束对话[/dim]")

        # 创建对话会话
        chat_session = PromptSession()

        while True:
            try:
                # 获取用户输入
                message = chat_session.prompt("\n👤 你> ")
                if message.lower() == "exit":
                    break

                self.console.print("\n[bold blue]🤖 AI[/bold blue]")
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]🤔 思考中..."),
                    transient=True,
                ) as progress:
                    progress.add_task("think")
                    stream = self.client.chat(
                        model=model_name,
                        messages=[{"role": "user", "content": message}],
                        stream=True,
                    )

                response = ""
                for chunk in stream:
                    content = chunk["message"]["content"]
                    response += content

                # 处理思考标签
                think_pattern = r"<think>(.*?)</think>"
                parts = re.split(think_pattern, response, flags=re.DOTALL)

                for i, part in enumerate(parts):
                    if i % 2 == 1:  # 思考内容
                        think_panel = Panel(Markdown(part.strip()), title="思考过程", style=Style(color="grey70", italic=True), border_style="grey50")
                        self.console.print(think_panel)
                        self.console.print()  # 添加空行
                    else:  # 普通内容
                        if part.strip():
                            md = Markdown(part.strip())
                            self.console.print(md)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]⛔️ 对话已取消[/yellow]")
                break
            except EOFError:
                self.console.print("\n[yellow]👋 再见！[/yellow]")
                break
            except ConnectionError:
                self.console.print("[red]连接服务器失败[/red]")
                break
            except (TimeoutError, ReadTimeout):
                self.console.print("[red]请求超时，请检查网络连接或服务器状态[/red]")
                break
            except HTTPError as e:
                self.console.print(f"[red]HTTP 错误: {e.response.status_code}[/red]")
                break
            except Exception as e:
                self.console.print(f"[red]发生未知错误: {str(e)}[/red]")
                logging.error(f"Unexpected error: {str(e)}")
                break

    def show_help(self, *args: List[str]) -> None:
        """显示帮助信息"""
        table = Table(title="✨ 命令列表", show_header=True, header_style="bold magenta")
        table.add_column("📝 命令", style="cyan")
        table.add_column("📄 说明", style="green")
        table.add_column("用法", style="yellow", justify="left")

        commands_help = [
            ("list", "📃 列出所有可用的模型", "list"),
            ("pull", "📥 拉取指定的模型", "pull <namespace/model_name>"),
            ("show", "🔍 显示模型详细信息", "show <model_name>"),
            ("chat", "💬 与模型进行对话", "chat <model_name>"),
            ("ps", "⚡️ 显示运行中的模型", "ps"),
            ("rm", "🚮 删除指定模型", "rm <model_name>"),
            ("version", "📌 显示版本信息", "version"),
            ("help", "❓ 显示帮助信息", "help"),
            ("exit", "🚪 退出程序", "exit"),
        ]

        for cmd, desc, usage in commands_help:
            table.add_row(cmd, desc, usage)

        self.console.print(table)

    def exit_shell(self, *args: List[str]) -> None:
        """退出程序"""
        self.console.print("[yellow]👋 再见！✨[/yellow]")
        sys.exit(0)

    def get_model_list(self) -> List[str]:
        """获取模型列表"""
        try:
            models = self.client.list()
            if hasattr(models, "models"):
                return [model.model for model in models.models]
            elif isinstance(models, list):
                return [model.model for model in models]
            return []
        except Exception:
            return []

    def get_command_completer(self) -> WordCompleter:
        """创建命令补全器"""
        # 获取所有命令
        commands = list(self.commands.keys())
        # 获取所有模型
        models = self.get_model_list()
        # 创建补全器
        word_list = commands + [f"{cmd} {model}" for cmd in ["chat", "show", "pull"] for model in models]
        return WordCompleter(word_list, ignore_case=True)

    def run(self) -> None:
        """运行交互式shell"""
        self.console.print(
            Panel.fit(
                "👋 欢迎使用 Ollama Shell！输入 'help' 查看可用命令 ✨",
                title="🤖 Ollama Shell",
                border_style="green",
            )
        )

        # 创建命令行会话
        session = PromptSession()

        while True:
            try:
                # 获取最新的补全器
                completer = self.get_command_completer()
                # 显示提示符并等待输入
                command = session.prompt(
                    "\n🤖 ollama> ",
                    completer=completer,
                    complete_while_typing=True,
                )

                args = command.strip().split()
                if not args:
                    continue

                cmd, *cmd_args = args
                if cmd in self.commands:
                    func, _ = self.commands[cmd]
                    func(*cmd_args)
                else:
                    self.console.print(f"[red]❌ 未知命令: {cmd}[/red]")
                    self.console.print("[yellow]❓ 输入 'help' 查看可用命令[/yellow]")

            except KeyboardInterrupt:
                self.console.print("\n[yellow]⛔️ 操作已取消[/yellow]")
                continue
            except EOFError:
                self.console.print("\n[yellow]👋 再见！✨[/yellow]")
                break
            except ConnectionError:
                self.console.print("[red]连接服务器失败[/red]")
            except TimeoutError:
                self.console.print("[red]请求超时[/red]")
            except HTTPError as e:
                self.console.print(f"[red]HTTP 错误: {e.response.status_code}[/red]")
            except Exception as e:
                self.console.print("[red]发生未知错误[/red]")
                logging.error(f"Unexpected error: {str(e)}")
                break

    def delete_model(self, *args: List[str]) -> None:
        """删除指定的模型"""
        if not args:
            self.console.print("[red]错误: 请指定要删除的模型名称[/red]")
            return

        model_name = args[0]
        # 修改模型名称验证，允许更多字符
        if not re.match(r'^[a-zA-Z0-9_\-\./:]+$', model_name):
            self.console.print("[red]错误: 模型名称包含非法字符[/red]")
            return

        try:
            # 确认删除
            self.console.print(f"\n[yellow]⚠️ 确定要删除模型 {model_name} 吗？这个操作不可恢复！[/yellow]")
            self.console.print("[dim]输入 'yes' 确认删除，其他输入取消[/dim]")
            
            # 创建确认会话
            confirm_session = PromptSession()
            confirm = confirm_session.prompt("\n确认> ")
            
            if confirm.lower() != 'yes':
                self.console.print("[yellow]已取消删除操作[/yellow]")
                return

            with Progress(
                SpinnerColumn(),
                TextColumn(f"[bold red]正在删除模型 {model_name}..."),
                transient=True,
            ) as progress:
                progress.add_task("delete")
                self.client.delete(model_name)
            
            self.console.print(f"[green]✅ 模型 {model_name} 已成功删除！[/green]")

        except ConnectionError:
            self.console.print("[red]连接服务器失败[/red]")
        except TimeoutError:
            self.console.print("[red]请求超时[/red]")
        except HTTPError as e:
            self.console.print(f"[red]HTTP 错误: {e.response.status_code}[/red]")
        except Exception as e:
            self.console.print("[red]发生未知错误[/red]")
            logging.error(f"Unexpected error: {str(e)}")

    def show_version(self, *args: List[str]) -> None:
        """显示 Ollama 版本信息"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]获取版本信息..."),
                transient=True,
            ) as progress:
                progress.add_task("fetch")
                # 使用保存的 verify_ssl 设置
                import httpx
                response = httpx.get(
                    f"{self.host}/api/version",
                    verify=self.verify_ssl
                )
                response.raise_for_status()
                data = response.json()
                
            if not data or 'version' not in data:
                self.console.print("[yellow]⚠️ 无法获取版本信息[/yellow]")
                return

            version = data['version']
            # 创建面板显示版本信息
            panel = Panel.fit(
                f"[bold cyan]Ollama 版本:[/bold cyan] {version}",
                title="📌 版本信息",
                border_style="green"
            )
            self.console.print(panel)

        except ConnectionError:
            self.console.print("[red]连接服务器失败[/red]")
        except TimeoutError:
            self.console.print("[red]请求超时[/red]")
        except HTTPError as e:
            self.console.print(f"[red]HTTP 错误: {e.response.status_code}[/red]")
        except Exception as e:
            self.console.print("[red]获取版本信息时发生错误[/red]")
            logging.error(f"Version info error: {str(e)}")


def main():
    # 创建命令行解析器
    parser = argparse.ArgumentParser(description="Ollama Shell - 一个功能强大的 Ollama 命令行工具")
    parser.add_argument(
        "-H",
        "--host",
        default="http://localhost:11434",
        help="Ollama 服务器地址，默认为 http://localhost:11434",
    )

    # 解析命令行参数
    args = parser.parse_args()

    # 创建 shell 实例
    shell = OllamaShell(host=args.host)
    shell.run()


if __name__ == "__main__":
    main()
