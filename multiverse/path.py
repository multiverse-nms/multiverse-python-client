import json

from .oxc import OXC


class Path:
    def __init__(self, name, label):
        """
        Initialize a Path object.

        :param name: Name of the path
        :param label: Label for the path
        """
        self._id = 0
        self._name = name
        self._label = label
        self._oxcs = []


    # Getter and Setter for id
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if isinstance(value, int):
            self._id = value
        else:
            raise ValueError("ID must be an integer.")

    # Getter and Setter for name
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if isinstance(value, str) and value.strip():
            self._name = value
        else:
            raise ValueError("Name must be a non-empty string.")
    
    # Getter and Setter for label
    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        if isinstance(value, str) and value.strip():
            self._label = value
        else:
            raise ValueError("Label must be a non-empty string.")

    # Getter and Setter for oxcs
    @property
    def oxcs(self):
        return self._oxcs

    @oxcs.setter
    def oxcs(self, value):
        if all(isinstance(v, OXC) for v in value):
            self._oxcs = value
        else:
            raise ValueError("All items must be instances of the OXC class.")

    
    def add_oxc(self, oxc):
        """
        Add an OXC to the path.

        :param oxc: OXC object to be added
        """
        if isinstance(oxc, OXC):
            self._oxcs.append(oxc)
        else:
            raise ValueError("Invalid OXC. Please provide an instance of the OXC class.")

    def to_dict(self):
        """
        Convert the Path object to a JSON representation.

        :return: JSON string representation of the Path object
        """
        path_dict = {
            "name": self._name,
            "label": self._label,
            "oxcs": [oxc.to_dict() for oxc in self._oxcs]
        }
        if self._id:
            path_dict['id'] = self._id
        return path_dict

    def print(self):
        if self._id:
            print(f"  ID: {self._id}")
        print(f"  Name: {self._name}")
        print(f"  Label: {self._label}")
        print(f"  OXCs:")
        for oxc in self._oxcs:
            print(f"    Label: {oxc.label}, Switch: {oxc.switch}, InPort: {oxc.inPort}, OutPort: {oxc.outPort}")

    @classmethod
    def from_dict(cls, data):
        """
        Create a Path object from a dictionary.

        :param data: Dictionary containing path data
        :return: Path object
        """
        path = cls(name=data["name"], label=data["label"])
        if "id" in data:
            path.id = data["id"]
        for oxc_data in data.get("oxcs", []):
            oxc = OXC(label=oxc_data["label"], switch=oxc_data["switch"], inPort=oxc_data["inPort"], outPort=oxc_data["outPort"])
            path.add_oxc(oxc)
        return path


    @classmethod
    def from_computed_path(cls, computed_path, name=None, label=None):
        """
        Creates a path dictionary suitable for instantiating a Path object from a computed path.

        Parameters:
        - computed_path (dict): The computed path dictionary containing path information.
        - name (str, optional): The name of the path. If not provided, it will be generated.
        - label (str, optional): The label of the path. If not provided, it will be generated.

        Returns:
        - dict: A dictionary suitable for creating a Path object using Path.from_dict().
        """
        # Extract the path and cross-connects from the computed path
        path_nodes = computed_path['path']
        cross_connects = computed_path.get('cross_connects', [])

        # Generate default name, label, and description if not provided
        if not name:
            name = f"TRAIL_{path_nodes[0]}_TO_{path_nodes[-1]}"
        if not label:
            label = f"{path_nodes[0]} to {path_nodes[-1]}"

        # Construct the oxcs list
        oxcs = []
        for idx, cc in enumerate(cross_connects):
            switch = cc['switch']
            inPort = cc['inPort'].split(".")[1]
            outPort = cc['outPort'].split(".")[1]
            # Generate a label for each cross-connect
            cc_label = f"{switch}_OXC_{inPort}_to_{outPort}"
            oxc = {
                "label": cc_label,
                "switch": switch,
                "inPort": inPort,
                "outPort": outPort
            }
            oxcs.append(oxc)

        # Create the path dictionary
        path_dict = {
            "name": name,
            "label": label,
            "description": "",
            "oxcs": oxcs
        }

        return Path.from_dict(path_dict)