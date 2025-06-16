"""Command Pattern Implementation.

This module provides classes for implementing the Command pattern.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class Command(ABC):
    """Abstract base class for commands.

    This class defines the interface for commands.
    Different commands can be implemented by subclassing this class.
    """

    @abstractmethod
    def execute(self) -> Any:
        """Execute the command.

        Returns:
            The result of the command execution.
        """
        pass


class AnalyzePlaylistCommand(Command):
    """Command for analyzing a playlist.

    This class implements the Command pattern for analyzing a playlist.

    Attributes:
        analyzer_service: The playlist analyzer service to use.
        playlist_url: The URL of the playlist to analyze.
    """

    def __init__(self, analyzer_service, playlist_url: str):
        """Initialize the AnalyzePlaylistCommand.

        Args:
            analyzer_service: The playlist analyzer service to use.
            playlist_url: The URL of the playlist to analyze.
        """
        self.analyzer_service = analyzer_service
        self.playlist_url = playlist_url

    def execute(self) -> Dict[str, Any]:
        """Execute the command.

        Returns:
            A dictionary containing the analysis results.
        """
        return self.analyzer_service.analyze_playlist(self.playlist_url)


class CommandInvoker:
    """Invoker for commands.

    This class is responsible for executing commands.
    It keeps a history of executed commands.

    Attributes:
        history: A list of executed commands.
    """

    def __init__(self):
        """Initialize the CommandInvoker."""
        self.history = []

    def execute_command(self, command: Command) -> Any:
        """Execute a command.

        Args:
            command: The command to execute.

        Returns:
            The result of the command execution.
        """
        self.history.append(command)
        return command.execute()
