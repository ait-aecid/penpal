from vncdotool.api import ThreadedVNCClientProxy as VncClient


class SessionStore:
    def __init__(self):
        self.store: dict[str, VncClient] = {}

    def __getstate__(self):
        """
        store contains the clients of the vnc connections.
        """
        state = self.__dict__.copy()
        state['store'] = None
        return state

    def has_session(self, session_name: str) -> bool:
        if session_name in self.store:
            return True
        else:
            return False

    def get_client_by_session(self, session_name: str) -> VncClient:
        if session_name in self.store:
            return self.store[session_name]
        else:
            raise KeyError('Session not found in Sessionstore')

    def set_session(self, session_name: str, client: VncClient):
        self.store[session_name] = client
