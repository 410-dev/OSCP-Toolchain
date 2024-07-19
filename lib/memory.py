import json
import os


class Memory:
    data = {}

    @staticmethod
    def get(key):
        try:
            return Memory.data[key]
        except KeyError:
            return None

    @staticmethod
    def set(key, value):
        Memory.data[key] = value

        if key != "config" and Memory.get("config").get("MemoryPersistence.enabled"):
            Memory.save()

        return Memory.data[key]

    @staticmethod
    def save():
        jsonSerializablesOnly = {}
        def isJsonable(x):
            try:
                json.dumps(x)
                return True
            except:
                return False

        for key in Memory.data:
            if key == "config":
                continue
            if isJsonable(Memory.data[key]):
                jsonSerializablesOnly[key] = Memory.data[key]

        with open("cache/memory.json", "w") as file:
            file.write(json.dumps(jsonSerializablesOnly, indent=4))

    @staticmethod
    def load():
        if os.path.isfile("cache/memory.json"):
            try:
                with open("cache/memory.json", "r") as file:
                    loaded = json.load(file)
                    if loaded:
                        Memory.data.update(loaded)
                    print("Memory loaded from memory.json")
            except:
                print("Failed to load memory.json")
