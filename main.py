# -*- coding: utf-8 -*-
"""
@ Author: b3nguang
@ Date: 2025-02-18 12:04:37
"""

import sys
from typing import List

from ollama import Client
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table


class OllamaShell:
    def __init__(self, host: str = "http://112.117.14.179:11434/"):
        self.client = Client(host=host)
        self.console = Console()
        self.commands = {
            "list": (self.list_models, "📃 列出可用模型"),
            "pull": (self.pull_model, "📥 拉取模型"),
            "show": (self.show_model, "🔍 显示模型详情"),
            "chat": (self.chat_with_model, "💬 与模型对话"),
            "ps": (self.show_processes, "⚡️ 显示运行中的模型"),
            "help": (self.show_help, "❓ 显示帮助信息"),
            "exit": (self.exit_shell, "🚪 退出程序"),
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
                    size_str = (
                        f"{size / (1024 * 1024 * 1024):.1f}GB" if size else "Unknown"
                    )

                    # 格式化时间
                    modified_str = (
                        modified.strftime("%Y-%m-%d %H:%M") if modified else "Unknown"
                    )

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
                    self.console.print(
                        f"[yellow]⚠️ 警告: 处理模型信息时出错: {str(e)}[/yellow]"
                    )
                    continue

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]错误: {str(e)}[/red]")

    def pull_model(self, *args: List[str]) -> None:
        """拉取指定的模型"""
        if not args:
            self.console.print("[red]错误: 请指定模型名称[/red]")
            return

        model_name = args[0]
        self.console.print(f"\n[bold]📥 开始拉取模型: {model_name}[/bold]")

        try:
            with Progress(
                TextColumn("[bold blue]{task.description}"), transient=False
            ) as progress:
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

        except Exception as e:
            self.console.print(f"[red]错误: {str(e)}[/red]")

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

        except Exception as e:
            self.console.print(f"[red]错误: {str(e)}[/red]")

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

            if not response or not hasattr(response, 'models') or not response.models:
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
                    expires_str
                )

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]❌ 错误: {str(e)}[/red]")

    def chat_with_model(self, *args: List[str]) -> None:
        """与模型进行对话"""
        if not args:
            self.console.print("[red]错误: 请指定模型名称[/red]")
            return

        model_name = args[0]
        self.console.print(f"\n[bold]💬 开始与 {model_name} 对话[/bold]")
        self.console.print("[dim]🚪 输入 'exit' 结束对话[/dim]")

        while True:
            try:
                message = Prompt.ask("\n[bold green]你[/bold green]")
                if message.lower() == "exit":
                    break

                self.console.print("\n[bold blue]AI[/bold blue]")
                with Progress(
                    SpinnerColumn(), TextColumn("[bold blue]思考中..."), transient=True
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
                    self.console.print(content, end="", highlight=False)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]对话已取消[/yellow]")
                break
            except Exception as e:
                self.console.print(f"\n[red]错误: {str(e)}[/red]")
                break

    def show_help(self, *args: List[str]) -> None:
        """显示帮助信息"""
        table = Table(
            title="✨ 命令列表", show_header=True, header_style="bold magenta"
        )
        table.add_column("📝 命令", style="cyan")
        table.add_column("📄 说明", style="green")
        table.add_column("📖 用法", style="yellow")

        commands_help = [
            ("list", "📃 列出所有可用的模型", "list"),
            ("pull", "📥 拉取指定的模型", "pull <model_name>"),
            ("show", "🔍 显示模型详细信息", "show <model_name>"),
            ("chat", "💬 与模型进行对话", "chat <model_name>"),
            ("ps", "⚡️ 显示运行中的模型", "ps"),
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

    def run(self) -> None:
        """运行交互式shell"""
        self.console.print(
            Panel.fit(
                "👋 欢迎使用 Ollama Shell！输入 'help' 查看可用命令 ✨",
                title="🤖 Ollama Shell",
                border_style="green",
            )
        )

        while True:
            try:
                command = Prompt.ask("\n[bold cyan]🤖 ollama[/bold cyan]")
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
            except Exception as e:
                self.console.print(f"[red]❌ 错误: {str(e)}[/red]")


def main():
    shell = OllamaShell()
    shell.run()


if __name__ == "__main__":
    main()
