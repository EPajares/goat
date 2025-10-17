from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from types import TracebackType
from typing import (
    Any,
    Callable,
    ContextManager,
    Iterator,
    ParamSpec,
    Protocol,
    Self,
    TypeVar,
)

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


@dataclass
class ProgressState:
    """Universal progress state for any operation."""

    current: float = 0.0
    total: float = 100.0
    message: str = ""
    current_item: str | None = None
    metadata: dict[str, Any] | None = None


class ProgressReporter(Protocol):
    """Protocol for progress reporting - can be Rich, simple callbacks, or silent."""

    def update(self: Self, state: ProgressState) -> None: ...
    def start_stage(self: Self, name: str, total: float = 100.0) -> None: ...
    def end_stage(self: Self) -> None: ...


class RichProgressManager:
    """Rich-based progress manager for beautiful CLI progress."""

    def __init__(
        self: Self, console: Console | None = None, enabled: bool = True
    ) -> None:
        self.enabled: bool = enabled
        self.console: Console = console or Console()
        self.progress: Progress | None = None
        self.current_task: TaskID | None = None
        self._stack: list[tuple[str, TaskID]] = []

    def update(self: Self, state: ProgressState) -> None:
        if not self.enabled or not self.progress:
            return

        if self.current_task:
            self.progress.update(
                self.current_task,
                completed=state.current,
                total=state.total,
                description=state.message,
            )

    def start_stage(self: Self, name: str, total: float = 100.0) -> None:
        if not self.enabled:
            return

        if not self.progress:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=self.console,
                transient=False,
            )
            self.progress.__enter__()

        task_id: TaskID = self.progress.add_task(name, total=total)
        self._stack.append((name, task_id))
        self.current_task = task_id

    def end_stage(self: Self) -> None:
        if not self.enabled or not self.progress or not self._stack:
            return

        name, task_id = self._stack.pop()
        self.progress.update(task_id, completed=100, refresh=True)

        if self._stack:
            self.current_task = self._stack[-1][1]
        else:
            self.current_task = None
            self.progress.__exit__(None, None, None)
            self.progress = None


class CallbackProgressReporter:
    """Simple callback-based progress reporter."""

    def __init__(
        self: Self, callback: Callable[[ProgressState], None] | None = None
    ) -> None:
        self.callback: Callable[[ProgressState], None] | None = callback
        self.current_stage: str = ""

    def update(self: Self, state: ProgressState) -> None:
        if self.callback:
            self.callback(state)

    def start_stage(self: Self, name: str, total: float = 100.0) -> None:
        self.current_stage = name
        if self.callback:
            self.callback(ProgressState(message=f"Starting {name}"))

    def end_stage(self: Self) -> None:
        if self.callback:
            self.callback(
                ProgressState(message=f"Completed {self.current_stage}", current=100)
            )


class SilentProgressReporter:
    """No-op progress reporter for when progress is disabled."""

    def update(self: Self, state: ProgressState) -> None:
        pass

    def start_stage(self: Self, name: str, total: float = 100.0) -> None:
        pass

    def end_stage(self: Self) -> None:
        pass


# Factory function
def create_progress_reporter(
    style: str = "auto",
    callback: Callable[[ProgressState], None] | None = None,
    console: Console | None = None,
) -> ProgressReporter:
    """
    Create appropriate progress reporter.

    Args:
        style: "rich", "callback", "silent", or "auto"
        callback: Callback function for callback style
        console: Rich console instance
    """
    if style == "rich" or (style == "auto" and callback is None):
        return RichProgressManager(console=console)
    elif style == "callback" and callback:
        return CallbackProgressReporter(callback)
    else:
        return SilentProgressReporter()


# Context manager for easy progress tracking
@contextmanager
def track_operation(
    name: str, reporter: ProgressReporter | None = None, total: float = 100.0
) -> Iterator[ProgressReporter]:
    """Context manager for tracking operations with progress."""
    if not reporter:
        reporter = SilentProgressReporter()

    reporter.start_stage(name, total)

    try:
        yield reporter
        reporter.update(ProgressState(current=total, message=f"Completed {name}"))
    except Exception as e:
        reporter.update(ProgressState(message=f"Failed {name}: {str(e)}"))
        raise
    finally:
        reporter.end_stage()


# Type variable for generic function decorator


P = ParamSpec("P")
T = TypeVar("T")


# Decorator for functions
def with_progress(
    operation_name: str, weight: float = 1.0
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to add progress tracking to any function."""

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Extract progress_reporter from kwargs if present
            reporter: ProgressReporter | None = kwargs.pop("progress_reporter", None)
            if not reporter:
                return func(*args, **kwargs)

            with track_operation(operation_name, reporter, 100 * weight):
                return func(*args, **kwargs)

        return wrapper

    return decorator


class ProgressContextManager:
    """Context manager that provides progress reporting capabilities."""

    def __init__(self: Self, reporter: ProgressReporter) -> None:
        self.reporter: ProgressReporter = reporter

    def __enter__(self: Self) -> Self:
        return self

    def __exit__(
        self: Self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return None

    def update(
        self: Self,
        current: float,
        message: str,
        current_item: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Convenience method to update progress."""
        self.reporter.update(
            ProgressState(
                current=current,
                message=message,
                current_item=current_item,
                metadata=metadata,
            )
        )


# Convenience function for common progress patterns
def create_progress_context(
    name: str,
    style: str = "auto",
    callback: Callable[[ProgressState], None] | None = None,
    console: Console | None = None,
) -> ContextManager[ProgressContextManager]:
    """Create a progress context manager for easy usage."""

    @contextmanager
    def context_manager() -> Iterator[ProgressContextManager]:
        reporter = create_progress_reporter(style, callback, console)
        with track_operation(name, reporter) as progress_reporter:
            yield ProgressContextManager(progress_reporter)

    return context_manager()
