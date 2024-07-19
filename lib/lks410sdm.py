import json
import importlib

class Data:

    class Types:
        separator = ":"
        String    = "String"
        Integer8  = "Int8"    # byte in Java
        Integer16 = "Int16"   # short in Java
        Integer   = "Int32"   # int in Java
        Integer32 = "Int32"
        Integer64 = "Int64"   # long in java
        Float32   = "Float32" # float in Java
        Float64   = "Float64" # double in Java
        Float     = "Float64"
        Boolean   = "Boolean" # boolean in Java
        List      = "List"
        Object    = "Object"  # Json object in Java
        Undefined = "UndefinedType"    # Undefined type, same as "Auto"
        NoStandard= f"{Object}{separator}NoStandard"
        Auto      = "Auto"    # Auto-detect type
        Null      = "Null"    # Null value (None in Python)

        all = [String, Integer8, Integer16, Integer, Integer32, Integer64, Float32, Float64, Float, Boolean, List, Object, NoStandard, Auto, Null]
        allInPythonType = [str, int, float, bool, list, dict, None]
        allExportable = [String, Integer8, Integer16, Integer, Integer32, Integer64, Float32, Float64, Float, Boolean, List, Object]
        primitive = [String, Integer8, Integer16, Integer, Integer32, Integer64, Float32, Float64, Float, Boolean]
        dictionary = [Object, NoStandard]
        complex = [List, Object, NoStandard]

    class Strings:
        Separators = ";;;"
        StandardVersion = "1.0"
        StandardHeader = f"LKS410 Standard Data Map"
        Standard = f"{StandardHeader}{Separators}{StandardVersion}{Separators}https://github.com/410-dev/lks410-sdm/tree/main/docs"
        TypeTemporaryString = "__TYPE__"
        NoStandardObjPython = "@python="
        NoStandardObjJava   = "@java="

    class ReservedNames:
        Standard = "standard"
        DataRoot = "DataRoot"
        ExtraProperties = "ExtraProperties"
        TypeField = "type"

    def __init__(self, parseString: str = None, checkValidity: bool = True, parseFile: str = None):
        self.checkValidity = checkValidity
        self.dictForm = {
            Data.ReservedNames.Standard: Data.Strings.Standard,
            Data.ReservedNames.DataRoot: {},
            Data.ReservedNames.ExtraProperties: {}
        }

        if parseString is not None and parseFile is not None:
            raise ValueError("Both parseString and parseFile cannot be used at the same time.")

        if parseString is not None:
            self.parseFromString(parseString)
        elif parseFile is not None:
            self.parseFromFile(parseFile)

    def getFast(self, name: str):
        grandparent, parent, key, index = self.traverse(name, create_missing=False, allow_type_modifier=True)
        if parent is None:
            return None

        if index == -1:
            return parent.get(key)
        else:
            return parent[key][index] if index < len(parent[key]) else None

    def getExtraProperties(self) -> dict:
        return self.dictForm[Data.ReservedNames.ExtraProperties]

    def getRoot(self) -> dict:
        return self.dictForm[Data.ReservedNames.DataRoot]

    def set(self, name: str, value, setAs: str = Types.Auto, allowTypeModifier: bool = False) -> bool:
        grandparent, parent, key, index = self.traverse(name, create_missing=True, allow_type_modifier=allowTypeModifier)
        if parent is None:
            return False

        if index == -1:
            if type(value) in Data.Types.allInPythonType:
                parent[key] = value
            else:
                parent[key] = value.__dict__
        else:
            if type(value) in Data.Types.allInPythonType:
                parent[key][index] = value
            else:
                parent[key][index] = value.__dict__

        def classname(obj):
            cls = type(obj)
            module = cls.__module__
            name = cls.__qualname__
            if module is not None and module != "__builtin__":
                name = module + "." + name
            return name

        if setAs == Data.Types.Auto:
            if type(value) not in Data.Types.allInPythonType:
                if f"{key}.{Data.ReservedNames.TypeField}" in parent and parent[f"{key}.{Data.ReservedNames.TypeField}"] is not None:
                    setAs = parent[f"{key}.{Data.ReservedNames.TypeField}"]
                else:
                    cn = classname(value)
                    setAs = f"{Data.Types.NoStandard}{Data.Types.separator}{Data.Strings.NoStandardObjPython}{cn}"
                parent[f"{key}.{Data.ReservedNames.TypeField}"] = setAs
        else:
            parent[f"{key}.{Data.ReservedNames.TypeField}"] = setAs

        return True

    def setType(self, of: str, setAs: str):
        self.set(name=f"{of}.{Data.ReservedNames.TypeField}", value=setAs, allowTypeModifier=True)

    def has(self, name: str) -> bool:
        return self.getFast(name) is not None

    def info(self, name: str) -> tuple:
        return self.traverse(name, create_missing=False, allow_type_modifier=True)

    @staticmethod
    def autoType(o) -> str:
        if isinstance(o, dict):
            return Data.Types.Object
        elif isinstance(o, list):
            return f"{Data.Types.List}{Data.Types.separator}{Data.Types.Auto}"
        elif isinstance(o, bool):
            return Data.Types.Boolean
        elif isinstance(o, str):
            return Data.Types.String
        elif isinstance(o, int):
            return Data.Types.Integer
        elif isinstance(o, float):
            return Data.Types.Float
        elif o is None:
            return Data.Types.Null
        else:
            return Data.Types.Undefined

    def typeOf(self, name: str, infodat: tuple = None, useAutoTypeOnly: bool = False) -> str:
        if infodat == None:
            infodat = self.info(name)

        if infodat is None:
            return Data.Types.Undefined
        grandparent, parent, key, index = infodat
        if parent is None:
            return Data.Types.Undefined

        if index == -1:
            if f"{key}.{Data.ReservedNames.TypeField}" in parent:
                if useAutoTypeOnly:
                    typeName = Data.autoType(parent[key])
                else:
                    typeName = parent[f"{key}.{Data.ReservedNames.TypeField}"]
            else:
                typeName = Data.autoType(parent[key])
        else:
            if f"{key}.{Data.ReservedNames.TypeField}" in grandparent:
                typeName = grandparent[f"{key}.{Data.ReservedNames.TypeField}"]
                if typeName.startswith(f"{Data.Types.List}{Data.Types.separator}"):
                    typeName = typeName[len(f"{Data.Types.List}{Data.Types.separator}"):]
                    if typeName == Data.Types.Auto:
                        typeName = Data.autoType(parent[key][index])
                else:
                    typeName = Data.Types.Undefined
            else:
                # Auto type
                typeName = Data.autoType(parent[key][index])

        if typeName.startswith(Data.Types.NoStandard):
            typeClass: list = typeName.split(Data.Types.separator)[2:]
            found = False
            for typeClassName in typeClass:
                if typeClassName.startswith(Data.Strings.NoStandardObjPython):
                    typeName = typeClassName.split("=")[1]
                    found = True
                    break

            if not found:
                typeName = Data.Types.Undefined

            typeName = f"{Data.Types.NoStandard}{Data.Types.separator}{typeName}"

        return typeName

    def typeMatches(self, name: str, typeName: str, useAutoTypeOnly: bool = False, strictInSize: bool = False) -> bool:
        expectedType = self.typeOf(name, useAutoTypeOnly=useAutoTypeOnly)

        if not strictInSize:
            numbers = "1234567890"
            for number in numbers:
                expectedType = expectedType.replace(number, "")

        expectedType = expectedType.split(Data.Types.separator)[0]

        return typeName.startswith(expectedType)

    def remove(self, name: str) -> bool:
        grandparent, parent, key, index = self.traverse(name, create_missing=False, allow_type_modifier=True)
        if parent is None:
            return False

        if index == -1:
            if key in parent:
                del parent[key]
                return True
        else:
            if key in parent and index < len(parent[key]):
                parent[key][index] = None
                return True

        return False

    def parseFromString(self, stringData: str):
        jsonData = json.loads(stringData)
        if Data.ReservedNames.Standard not in jsonData:
            raise ValueError("Standard field not found in the data")
        stdString = jsonData[Data.ReservedNames.Standard]
        stdStringHeader = stdString.split(Data.Strings.Separators)[0]
        stdStringVersion = stdString.split(Data.Strings.Separators)[1]
        if stdStringHeader != Data.Strings.StandardHeader:
            raise ValueError("Standard header mismatch.")
        if stdStringVersion != Data.Strings.StandardVersion:
            print(f"Warning: Standard version mismatch. Expected {Data.Strings.StandardVersion}, got {stdStringVersion}")
        originalData = self.dictForm.copy()
        self.dictForm = jsonData
        invalidFields: list = self.checkFieldNameValidity()
        if len(invalidFields) > 0:
            self.dictForm = originalData
            raise ValueError("Field names are not valid: " + ", ".join(invalidFields))

    def parseFromFile(self, filePath: str):
        with open(filePath, "r") as file:
            self.parseFromString(file.read())

    def compileString(self, linebreak: int = 4, checkFieldNameValidity: bool = True) -> str:
        if checkFieldNameValidity:
            results: list = self.checkFieldNameValidity()
            if len(results) > 0:
                raise ValueError("Field names are not valid: " + ", ".join(results))
        if linebreak < 0:
            return json.dumps(self.dictForm)
        return json.dumps(self.dictForm, indent=linebreak)

    def checkFieldNameValidity(self) -> list:
        fieldNames = Data.getKeyNamesRecursive(self.dictForm[Data.ReservedNames.DataRoot], "")
        invalidFieldNames = []
        reservedFieldNames = [Data.ReservedNames.Standard, Data.ReservedNames.DataRoot,
                              Data.ReservedNames.ExtraProperties, Data.ReservedNames.TypeField]
        for fieldName in fieldNames:
            if fieldName.split(".")[-1] in reservedFieldNames:
                invalidFieldNames.append(fieldName)
        return invalidFieldNames

    @staticmethod
    def getKeyNamesRecursive(obj: dict, currentScope: str) -> list:
        keyNames = []
        for key in obj:
            if key != Data.ReservedNames.TypeField and key.endswith(f".{Data.ReservedNames.TypeField}"):
                key = key.replace(f".{Data.ReservedNames.TypeField}", Data.Strings.TypeTemporaryString)
            keyNames.append(f"{currentScope}.{key}")
            if key not in obj:
                continue
            elif isinstance(obj[key], dict):
                keyNames += Data.getKeyNamesRecursive(obj[key], f"{currentScope}.{key}")
            elif isinstance(obj[key], list):
                for i in range(len(obj[key])):
                    if isinstance(obj[key][i], dict):
                        keyNames += Data.getKeyNamesRecursive(obj[key][i], f"{currentScope}.{key}[{i}]")
        for i in range(len(keyNames)):
            if keyNames[i][0] == ".":
                keyNames[i] = keyNames[i][1:]
        return keyNames

    def traverse(self, name: str, create_missing: bool = False, allow_type_modifier: bool = False):
        # Disallowed characters:
        disallowed_characters_for_key = ["{", "}", "(", ")", ":"]
        if not allow_type_modifier:
            disallowed_characters_for_key.append(f".{Data.ReservedNames.TypeField}")
        elif f".{Data.ReservedNames.TypeField}" in name:
            name = name.replace(f".{Data.ReservedNames.TypeField}", Data.Strings.TypeTemporaryString)

        for disallowed_character in disallowed_characters_for_key:
            if disallowed_character in name:
                return None, None, None, None

        # Nodes
        nodes_route = name.split(".")
        nodes_route_length = len(nodes_route)

        current_node = self.dictForm[Data.ReservedNames.DataRoot]
        parent_nodes = [current_node]
        final_key = nodes_route[-1]

        for i in range(nodes_route_length):
            current_node_name = nodes_route[i]
            list_access_idx = -1
            if "[" in current_node_name and "]" in current_node_name:
                list_access_idx = int(current_node_name.split("[")[1].split("]")[0])
                current_node_name = current_node_name.split("[")[0]

            if i == nodes_route_length - 1:
                if Data.Strings.TypeTemporaryString in current_node_name:
                    current_node_name = current_node_name.replace(Data.Strings.TypeTemporaryString,
                                                                  f".{Data.ReservedNames.TypeField}")

                if list_access_idx == -1:
                    return parent_nodes[-2] if len(parent_nodes) > 1 else None, parent_nodes[-1], current_node_name, -1
                else:
                    if create_missing and (current_node_name not in current_node or len(
                            current_node[current_node_name]) <= list_access_idx):
                        if current_node_name not in current_node:
                            current_node[current_node_name] = []
                        while len(current_node[current_node_name]) <= list_access_idx:
                            current_node[current_node_name].append(None)
                    return parent_nodes[-1], current_node, current_node_name, list_access_idx
            else:
                if create_missing and current_node_name not in current_node:
                    if list_access_idx == -1:
                        current_node[current_node_name] = {}
                    else:
                        current_node[current_node_name] = []
                        while len(current_node[current_node_name]) <= list_access_idx:
                            current_node[current_node_name].append(None)

                if current_node_name not in current_node:
                    return None, None, None, None

                if list_access_idx == -1:
                    current_node = current_node[current_node_name]
                else:
                    if list_access_idx >= len(current_node[current_node_name]):
                        return None, None, None, None
                    if current_node[current_node_name][list_access_idx] is None:
                        if create_missing:
                            current_node[current_node_name][list_access_idx] = {}
                        else:
                            return None, None, None, None
                    current_node = current_node[current_node_name][list_access_idx]
                parent_nodes.append(current_node)

        return None, None, None, None  # This line should never be reached, but it's here for completeness

    # Exporting as typed object
    def get(self, name: str, usingType: type = None, copyDictTo: object=None):
        infodat = self.traverse(name, create_missing=False, allow_type_modifier=True)
        grandparent, parent, key, index = infodat

        # Not found
        if parent is None:
            return None

        # Not list, key available in parent
        if index == -1 and key in parent:
            if usingType is None:
                typeName = self.typeOf(key, infodat)
                if typeName.startswith(Data.Types.NoStandard):
                    typeName = typeName[len(Data.Types.NoStandard) + len(Data.Types.separator):]
                    modulePath = typeName.split(".")[:-1]
                    objectName = typeName.split(".")[-1]
                    module = importlib.import_module(".".join(modulePath))
                    if copyDictTo is None:
                        return getattr(module, objectName)(**parent[key])
                    else:
                        copyDictTo.__dict__.update(parent[key])
                        return copyDictTo

                elif typeName in Data.Types.allExportable:
                    return parent[key]
                else:
                    return parent[key]
            else:
                return usingType(**parent[key])

        # It's a list
        else:
            if key in parent and index < len(parent[key]):
                if usingType is None:
                    typeName = self.typeOf(f"{key}[{index}]", infodat)
                    if typeName.startswith(Data.Types.NoStandard):
                        typeName = typeName[len(Data.Types.NoStandard) + len(Data.Types.separator):]
                        modulePath = typeName.split(".")[:-1]
                        objectName = typeName.split(".")[-1]
                        module = importlib.import_module(".".join(modulePath))
                        if copyDictTo is None:
                            return getattr(module, objectName)(**parent[key][index])
                        else:
                            copyDictTo.__dict__.update(parent[key][index])
                            return copyDictTo

                    elif typeName in Data.Types.allExportable:
                        return parent[key][index]
                    else:
                        return parent[key][index]
                else:
                    return usingType(**parent[key][index])

        return None

    def typeCheck(self, writeTypeData: bool = False, strictTypeChecks: bool = False, strictInSize: bool = False, verbose: bool = True, handleNamingConvention: str = "warning", markTypeEnforcementCompletedOnWritingTypeData: bool = True) -> bool:
        names = Data.getKeyNamesRecursive(self.dictForm[Data.ReservedNames.DataRoot], "")
        allPass = True
        for name in names:
            if name.endswith(Data.Strings.TypeTemporaryString):
                continue

            typeData = self.typeOf(name)
            if writeTypeData:
                self.setType(name, typeData)

            if handleNamingConvention == "warning" or handleNamingConvention == "error":
                typeMaster = typeData.split(Data.Types.separator)[0]
                currentName = name.split(".")[-1]
                hasUnderscore = "_" in currentName
                isComplexName = currentName[0].isupper()
                if hasUnderscore:
                    if handleNamingConvention == "error":
                        allPass = False
                        print(f"Error: Field name {currentName} contains underscore '_' character which is not in field naming convention.")
                    elif verbose:
                        print(f"Warning: Field name {currentName} contains underscore '_' character which is not in field naming convention.")
                if typeMaster in Data.Types.complex:
                    if not isComplexName:
                        if handleNamingConvention == "error":
                            allPass = False
                            print(f"Error: Field name {currentName} is not in complex field naming convention. Use uppercase starting letter instead.")
                        elif verbose:
                            print(f"Warning: Field name {currentName} is not in complex field naming convention. Use uppercase starting letter instead.")
                else:
                    if isComplexName:
                        if handleNamingConvention == "error":
                            allPass = False
                            print(f"Error: Field name {currentName} is in complex field naming convention. Use lowercase starting letter instead.")
                        elif verbose:
                            print(f"Warning: Field name {currentName} is in complex field naming convention. Use lowercase starting letter instead.")

            if strictTypeChecks:
                if not self.typeMatches(name, typeData, strictTypeChecks, strictInSize):
                    allPass = False
                    if verbose:
                        print(f"Potential type check error: Type mismatch for {name}. Expected {self.typeOf(name, useAutoTypeOnly=True)}, got {self.typeOf(name)}")

        if allPass and markTypeEnforcementCompletedOnWritingTypeData:
            self.dictForm[Data.ReservedNames.ExtraProperties]["typeEnforcement"] = True

        return allPass

    def sortKeysByName(self, reverse: bool = False):
        def sortKeys(obj: dict):
            return dict(sorted(obj.items(), key=lambda x: x[0], reverse=reverse))

        self.dictForm[Data.ReservedNames.DataRoot] = sortKeys(self.dictForm[Data.ReservedNames.DataRoot])

    def append(self, name: str, value):
        grandparent, parent, key, index = self.traverse(name, create_missing=False, allow_type_modifier=False)
        if parent is None:
            return False
        if index == -1:
            if isinstance(parent[key], list):
                if isinstance(value, list):
                    parent[key] = parent[key] + value
                else:
                    parent[key].append(value)
            else:
                return False
        else:
            if isinstance(parent[key], list):
                if isinstance(value, list):
                    parent[key][index] = parent[key][index] + value
                else:
                    parent[key][index].append(value)
            else:
                return False

        return True

    def toCallableData(self):
        return CallableData(self.getRoot())

    def fromCallableData(self, callableDS):
        self.dictForm[Data.ReservedNames.DataRoot] = callableDS.getAsDict()

    def __str__(self):
        return self.compileString()


class CallableData:
    def __init__(self, data: dict = None):
        self._data = data if data is not None else {}
        self._create_structure(self._data)

    def _create_structure(self, data, prefix=''):
        for key, value in data.items():
            if key.endswith('.type'):
                continue
            full_key = f"{prefix}{key}" if prefix else key
            if isinstance(value, dict):
                setattr(self, full_key, self._create_nested_property(full_key, value))
            elif isinstance(value, list):
                setattr(self, full_key, self._create_list_property(full_key, value))
            else:
                setattr(self, full_key, self._create_property(full_key))

    def _create_nested_property(self, key, value):
        nested = CallableData(value)
        def nested_getter():
            return nested
        return nested_getter

    def _create_list_property(self, key, value):
        def list_getter_setter(*args):
            if len(args) == 0:
                return ListWrapper([self._wrap_value(item, f"{key}[{i}]") for i, item in enumerate(self._data[key])])
            else:
                new_value = args[0]
                type_key = f"{key}.type"
                if type_key in self._data:
                    self._check_list_type(new_value, self._data[type_key])
                self._data[key] = new_value
                return None
        return list_getter_setter

    def _wrap_value(self, value, path):
        if isinstance(value, dict):
            return CallableData(value)
        elif isinstance(value, list):
            return ListWrapper([self._wrap_value(item, f"{path}[{i}]") for i, item in enumerate(value)])
        else:
            return self._create_primitive_property(path, value)

    def _create_primitive_property(self, path, value):
        def getter_setter(*args):
            if len(args) == 0:
                return value
            else:
                new_value = args[0]
                keys = path.replace(']', '').replace('[', '.').split('.')
                target = self._data
                for key in keys[:-1]:
                    if key.isdigit():
                        index = int(key)
                        while len(target) <= index:
                            target.append({})
                        target = target[index]
                    else:
                        target = target.setdefault(key, {})
                if keys[-1].isdigit():
                    index = int(keys[-1])
                    while len(target) <= index:
                        target.append({})
                    target[index] = new_value
                else:
                    target[keys[-1]] = new_value
                return None
        return getter_setter

    def _check_list_type(self, value, type_string):
        if not isinstance(value, list):
            raise TypeError(f"Expected List, got {type(value).__name__}")
        if type_string.startswith("List:"):
            item_type = self._get_type(type_string.split(":")[1])
            if item_type:
                for item in value:
                    if not isinstance(item, item_type) and item_type != object:
                        raise TypeError(f"List item: Expected {item_type.__name__}, got {type(item).__name__}")

    def _create_property(self, key):
        def getter_setter(*args):
            if len(args) == 0:
                return self._data.get(key)
            else:
                new_value = args[0]
                type_key = f"{key}.type"
                if type_key in self._data:
                    expected_type = self._get_type(self._data[type_key])
                    if expected_type and not isinstance(new_value, expected_type) and expected_type != object:
                        raise TypeError(f"Expected {expected_type.__name__}, got {type(new_value).__name__}")
                self._data[key] = new_value
                return None
        return getter_setter

    def _get_type(self, type_string):
        type_map = {
            'String': str,
            'Integer': int,
            'Float': float,
            'Boolean': bool,
            'Object': dict,
            'Array': list,
            'Auto': object  # 'Auto' will match any type
        }
        return type_map.get(type_string)

    def __getattr__(self, name):
        if name not in self._data:
            self._data[name] = []
        if isinstance(self._data[name], dict):
            return self._create_nested_property(name, self._data[name])()
        elif isinstance(self._data[name], list):
            return self._create_list_property(name, self._data[name])
        return self._create_property(name)

    def __call__(self):
        return self

    def getAsDict(self):
        def convert(item):
            if isinstance(item, CallableData):
                return item.getAsDict()
            elif isinstance(item, ListWrapper):
                return [convert(i) for i in item]
            elif isinstance(item, list):
                return [convert(i) for i in item]
            elif isinstance(item, dict):
                return {k: convert(v) for k, v in item.items()}
            else:
                return item
        return convert(self._data)

class ListWrapper(list):
    def __getitem__(self, key):
        while len(self) <= key:
            self.append(CallableData({}))
        return super().__getitem__(key)

    def __call__(self):
        return self