class OXC:
    def __init__(self, label, switch, inPort, outPort):
        """
        Initialize an OXC object.

        :param label: Label for the OXC
        :param switch: Name of the switch
        :param inPort: Ingress port
        :param outPort: Egress port
        """
        self._label = label
        self._switch = switch
        self._inPort = inPort
        self._outPort = outPort

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

    # Getter and Setter for switch
    @property
    def switch(self):
        return self._switch

    @switch.setter
    def switch(self, value):
        if isinstance(value, str) and value.strip():
            self._switch = value
        else:
            raise ValueError("Switch must be a non-empty string.")

    # Getter and Setter for inPort
    @property
    def inPort(self):
        return self._inPort

    @inPort.setter
    def inPort(self, value):
        if isinstance(value, str) and value.strip():
            self._inPort = value
        else:
            raise ValueError("inPort must be a non-empty string.")

    # Getter and Setter for outPort
    @property
    def outPort(self):
        return self._outPort

    @outPort.setter
    def outPort(self, value):
        if isinstance(value, str) and value.strip():
            self._outPort = value
        else:
            raise ValueError("outPort must be a non-empty string.")

    def to_dict(self):
        """
        Convert the OXC object to a dictionary representation.

        :return: Dictionary representation of the OXC object
        """
        return {
            "label": self._label,
            "switch": self._switch,
            "inPort": self._inPort,
            "outPort": self._outPort
        }