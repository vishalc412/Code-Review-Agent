"""Base class for agents."""

from abc import ABC, abstractmethod
from core.config import Settings, get_settings
from core.logger import get_logger
from platforms.base import BasePlatform
from platforms.factory import create_platform
from llm.base import BaseLLMClient
from llm.factory import create_llm_client


class BaseAgent(ABC):
    """Abstract base class for agents."""

    def __init__(self, settings: Settings = None):
        """
        Initialize base agent.

        Args:
            settings: Optional settings, defaults to global settings
        """
        self.settings = settings or get_settings()
        self.logger = get_logger(self.__class__.__name__)
        self.platform: BasePlatform = create_platform(self.settings)
        self.llm_client: BaseLLMClient = create_llm_client(self.settings)

    @abstractmethod
    def run(self, **kwargs):
        """
        Run the agent.

        Args:
            **kwargs: Agent-specific parameters
        """
        pass
