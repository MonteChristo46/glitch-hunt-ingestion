from asyncpg import Pool

class BaseHandler:
    def __init__(self, pool: Pool):
        self.pool = pool
