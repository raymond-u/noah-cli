from ..core.config import ConfigManager
from ..core.console import Console
from ..core.file import DataManager
from ..core.network import NetworkClient

_console = Console()
_network_client = NetworkClient(_console)
_config_manager = ConfigManager(_console)
_data_manager = DataManager(_console, _network_client)


def console() -> Console:
    """Return a shared console."""
    return _console


def network_client() -> NetworkClient:
    """Return a shared network client."""
    return _network_client


def config_manager() -> ConfigManager:
    """Return a shared config manager."""
    return _config_manager


def data_manager() -> DataManager:
    """Return a shared data manager."""
    return _data_manager
