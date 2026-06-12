from rich.console import Console

console = Console()


def log_info(message: str) -> None:
    console.print(f"[bold cyan][INFO][/bold cyan] {message}")


def log_success(message: str) -> None:
    console.print(f"[bold green][SUCCESS][/bold green] {message}")


def log_warning(message: str) -> None:
    console.print(f"[bold yellow][WARNING][/bold yellow] {message}")


def log_error(message: str) -> None:
    console.print(f"[bold red][ERROR][/bold red] {message}")


def log_debug(message: str) -> None:
    console.print(f"[dim][DEBUG][/dim] {message}")