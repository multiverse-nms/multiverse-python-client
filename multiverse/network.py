# _multiverse/network.py

import json

from .path import Path
import networkx as nx


def topology_to_graph(topology_dict):
    """
    Converts an optical network topology dictionary to a NetworkX MultiDiGraph,
    allowing multiple links between nodes.
    """
    G = nx.MultiDiGraph()
    
    # Add nodes to the graph using node names as identifiers
    for node in topology_dict['nodes']:
        node_name = node.get('name', '')
        G.add_node(node_name, type=node.get('type', ''))

    # Create a mapping from port IDs to port names for quick lookup
    node_id_to_name = {}
    port_id_to_name = {}
    for node in topology_dict['nodes']:
        node_id_to_name[node['id']] = node.get('name', '')
        for port in node.get('vltps', []):
            port_id_to_name[port['id']] = port.get('name', '')
    
    # Add edges to the graph, accounting for multiple edges
    for link in topology_dict.get('links', []):
        # Get source and destination node names based on their IDs
        src_node_name = node_id_to_name.get(link['srcVnodeId'], None)
        dest_node_name = node_id_to_name.get(link['destVnodeId'], None)
    
        # Get port names
        src_port_name = port_id_to_name.get(link['srcVltpId'], '')
        dest_port_name = port_id_to_name.get(link['destVltpId'], '')
    
        # Add edge with attributes
        G.add_edge(
            src_node_name,
            dest_node_name,
            key=int(link['id']),  # Use link ID as the edge key
            name=link.get('name', ''),
            src_port=src_port_name,
            dest_port=dest_port_name,
            #**link
        )
    
    return G


class Network:
    def __init__(self, multiverse, network_id, name):
        self._multiverse = multiverse
        self._network_id = network_id
        self._name = name
        self._node_map = None
        self._port_map = None

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._network_id

    def get_topology(self):
        """Fetch the topology for the network."""
        url = f"{self._multiverse._BASE_URL}/subnet/{self._network_id}/topology"
        response = self._multiverse.session.get(url)
        if response.status_code == 200:
            topology = response.json()
            self._update_maps(topology)
            return topology_to_graph(topology)
        else:
            print(f"Failed to get topology: {response.text}")
            self._reset_maps()
            return None

    def _update_maps(self, topology):
        """Create mappings from port IDs to names."""
        self._node_map = {}
        self._port_map = {}
        for node in topology['nodes']:
            self._node_map[node['id']] = node['name']
            for port in node['vltps']:
                self._port_map[port['id']] = port['name']

    def _reset_maps(self):
        self._node_map = None
        self._port_map = None

    def get_paths(self):
        """Fetch all paths (trails) for the network, including their cross-connects."""
        if self._node_map is None or self._port_map is None:
            t = self.get_topology()
        url = f"{self._multiverse._BASE_URL}/subnet/{self._network_id}/trails"
        response = self._multiverse.session.get(url)
        if response.status_code == 200:
            paths_obj = []
            for path in response.json():
                vxcs = self._get_path_vxcs(path['id'])
                path['oxcs'] = vxcs
                paths_obj.append(Path.from_dict(path))
            return paths_obj
        else:
            print(f"Failed to get paths: {response.text}")
            return None

    def _get_path_vxcs(self, path_id):
        """Fetch cross-connects for a given path ID."""
        url = f"{self._multiverse._BASE_URL}/trail/{path_id}/oxcs"
        response = self._multiverse.session.get(url)
        if response.status_code == 200:
            vxcs = response.json()
            # Convert IDs to names for consistency
            for vxc in vxcs:
                switch_id = vxc['switchId']
                switch_name = self._node_map.get(switch_id)
                ingress_port_id = vxc['ingressPortId']
                egress_port_id = vxc['egressPortId']
                ingress_port = self._port_map.get(ingress_port_id)
                egress_port = self._port_map.get(egress_port_id)
                vxc['switch'] = switch_name
                vxc['inPort'] = ingress_port
                vxc['outPort'] = egress_port
            return vxcs
        else:
            print(f"Failed to get path cross-connects: {response.text}")
            return None

    def create_path(self, path):
        """Create a path with the specified data."""
        if self._node_map is None or self._port_map is None:
            t = self.get_topology()

        # Convert node and port names to IDs
        j_oxcs = []
        for oxc in path.oxcs:
            j_oxc = {}

            node_name = oxc.switch
            ingress_port_name = oxc.inPort
            egress_port_name = oxc.outPort

            # Find node ID
            node_id = None
            for nid, nname in self._node_map.items():
                if nname == node_name:
                    node_id = nid
                    break
            if not node_id:
                raise ValueError(f"Node '{node_name}' not found.")

            # Find port IDs
            ingress_port_id = None
            egress_port_id = None
            for pid, pname in self._port_map.items():
                if pname == f"{node_name}.{ingress_port_name}":
                    ingress_port_id = pid
                if pname == f"{node_name}.{egress_port_name}":
                    egress_port_id = pid
            if ingress_port_id is None or egress_port_id is None:
                raise ValueError(f"Ports '{ingress_port_name}' or '{egress_port_name}' not found on node '{node_name}'.")

            # Prepare the vxc data
            j_oxc['name'] = ""
            j_oxc['label'] = oxc.label
            j_oxc['description'] = ""
            j_oxc['switchId'] = node_id
            j_oxc['ingressPortId'] = ingress_port_id
            j_oxc['egressPortId'] = egress_port_id
            j_oxcs.append(j_oxc)

        # Prepare the payload
        payload = {
            "name": path.name,
            "label": path.label,
            "description": path.label,
            "vsubnetId": self._network_id,
            "status": "PENDING",
            "vxcs": j_oxcs
        }

        url = f"{self._multiverse._BASE_URL}/trail"
        headers = {'Content-Type': 'application/json'}
        response = self._multiverse.session.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 201:
            print(f"Path {path.name} created")
            path.id = response.json()['id']
            return path
        else:
            print(f"Failed to create path: {response.text}")
            return None

    def delete_path(self, path, force=False):
        """Delete a path."""
        if not path.id:
            print("Path ID is required to delete a path.")
            return False
        url = f"{self._multiverse._BASE_URL}/trail/{path.id}"
        response = self._multiverse.session.delete(url)
        if response.status_code == 200 or response.status_code == 204:
            if force:
                return self.delete_path(path, False)
            else:
                print(f"Path {path.name} deleted.")
                return True
        else:
            print(f"Failed to delete path: {response.text}")
            return False
