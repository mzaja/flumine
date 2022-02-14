import logging
from enum import Enum

from ..exceptions import ClientError

logger = logging.getLogger(__name__)


class ExchangeType(Enum):
    BETFAIR = "Betfair"
    SIMULATED = "Simulated"
    BETCONNECT = "BetConnect"


class Clients:
    """
    Data structure for flumine clients
    """

    def __init__(self) -> None:
        self._clients = []
        self._exchange_clients = {exchange: {} for exchange in ExchangeType}

    def add_client(self, client):
        if client in self._clients:
            raise ClientError("Client already present")
        if client.EXCHANGE not in self._exchange_clients:
            raise ClientError("Unknown exchange type")
        self._clients.append(client)
        self._exchange_clients[client.EXCHANGE][client.username] = client
        logger.info("Client added", extra=client.info)
        return client

    def get_client(self, exchange_type: ExchangeType, username: str):
        try:
            return self._exchange_clients[exchange_type][username]
        except KeyError:
            return

    def login(self) -> None:
        for client in self._clients:
            client.login()
            logger.info("Client login", extra=client.info)

    def keep_alive(self) -> None:
        for client in self._clients:
            client.keep_alive()
            logger.info("Client keep alive", extra=client.info)

    def logout(self) -> None:
        for client in self._clients:
            client.logout()
            logger.info("Client logout", extra=client.info)

    def update_account_details(self) -> None:
        for client in self._clients:
            client.update_account_details()
            logger.info("Client update account details", extra=client.info)

    @property
    def simulated(self) -> bool:
        # return True if simulated client present
        for client in self._clients:
            if client.EXCHANGE == ExchangeType.SIMULATED or client.paper_trade:
                return True
        return False

    @property
    def info(self) -> dict:
        return {
            k: {k_i: v_i.info for k_i, v_i in v.items()}
            for k, v in self._exchange_clients.items()
        }

    def __iter__(self):
        return iter(self._clients)

    def __len__(self) -> int:
        return len(self._clients)
