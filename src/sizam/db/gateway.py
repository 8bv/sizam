

class DBGateway:
    def __init__(self, session):
        self._session = session

    def add_all(self, values):
        self._session.add_all(values)