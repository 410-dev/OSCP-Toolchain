
class Memory:
    data = {}

    @staticmethod
    def get(key):
        return Memory.data[key]

    @staticmethod
    def set(key, value):
        Memory.data[key] = value
        return Memory.data[key]

