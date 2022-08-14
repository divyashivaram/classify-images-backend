import redis


REDIS_HOST = 'localhost'
REDIS_PORT = 6379


class Redis():
    def __init__(self):
        self.redis_instance = redis.Redis(host=REDIS_HOST,
                                          port=REDIS_PORT, db=0)

    def write(self, key, val):
        return self.redis_instance.set(key, val)

    def read(self, key):
        return self.redis_instance.get(key)

    def peek(self, key):
        return self.redis_instance.exists(key)
