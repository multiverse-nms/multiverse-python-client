# multiverse/utils.py

import networkx as nx
import matplotlib.pyplot as plt

def compute_all_paths(graph, start_name, end_name, start_port=None, end_port=None):
    """
    Computes all possible simple paths between two nodes, including edge keys,
    considering optional source and destination ports.

    Parameters:
    - graph: The NetworkX graph.
    - start_name: The name of the starting node.
    - end_name: The name of the ending node.
    - start_port: Optional, the source port name (e.g., 'SOURCE.1').
    - end_port: Optional, the destination port name (e.g., 'DETECTOR.1').

    Returns:
    list: A list of paths, each path is a list of edges (from_node, to_node, edge_key).
    """
    all_simple_paths = []
    
    def dfs(current_node, end_node, path, visited_nodes):
        if current_node == end_node:
            # If an end_port is specified, check if the last edge uses that port
            if end_port:
                if not path:
                    return  # No edges in path, can't check end port
                last_edge = path[-1]
                edge_data = graph[last_edge[0]][last_edge[1]][last_edge[2]]
                dest_port = edge_data['dest_port']
                if dest_port != end_port:
                    return  # Skip paths that don't end with the specified destination port
            all_simple_paths.append(list(path))
            return
        for neighbor in graph.successors(current_node):
            for key, edge_data in graph[current_node][neighbor].items():
                if neighbor not in visited_nodes:
                    # If at the starting node, check for start_port constraint
                    if current_node == start_name and start_port:
                        src_port = edge_data['src_port']
                        if src_port != start_port:
                            continue  # Skip edges that don't use the specified start port
                    # Proceed to neighbor
                    path.append((current_node, neighbor, key))
                    visited_nodes.add(neighbor)
                    dfs(neighbor, end_node, path, visited_nodes)
                    path.pop()
                    visited_nodes.remove(neighbor)
    
    # Initialize path as empty, visited_nodes contains start_name
    dfs(start_name, end_name, [], set([start_name]))
    
    return all_simple_paths


def extract_cross_connects(graph, path_edges):
    """
    Extracts the sequence of cross-connects (OXCs) from a given path of edges.

    Parameters:
    graph (networkx.MultiDiGraph): The NetworkX graph.
    path_edges (list): A list of edges (from_node, to_node, edge_key).

    Returns:
    list: A list of cross-connects, each cross-connect is a dict with 'switch', 'inPort', 'outPort'.
    """
    cross_connects = []
    
    for i in range(1, len(path_edges)):
        prev_edge = path_edges[i - 1]
        curr_edge = path_edges[i]
        
        # The switch where the cross-connect occurs
        switch = prev_edge[1]  # The 'to_node' of the previous edge
        
        # Edge data
        edge_in = graph[prev_edge[0]][prev_edge[1]][prev_edge[2]]
        edge_out = graph[curr_edge[0]][curr_edge[1]][curr_edge[2]]
        
        # Extract port numbers
        in_port = edge_in['dest_port']
        out_port = edge_out['src_port']
        
        cross_connect = {
            'switch': switch,
            'inPort': in_port,
            'outPort': out_port
        }
        cross_connects.append(cross_connect)
    
    return cross_connects


def search_paths(graph, start_name, end_name, paths_data):
    """
    Finds all possible paths between two nodes, considering optional source and destination ports.
    """
    # Get port number if specified
    start_port = None
    start_split = start_name.split(".")
    if len(start_split) == 2:
        start_port = start_name
        start_name = start_split[0]

    end_port = None
    end_split = end_name.split(".")
    if len(end_split) == 2:
        end_port = end_name
        end_name = end_split[0]

    # Compute all possible simple paths with edges, considering port constraints
    all_paths_with_edges = compute_all_paths(graph, start_name, end_name, start_port, end_port)

    # Prepare a list of established cross-connect sequences and a mapping of used ports to path names
    established_cross_connects = []
    used_ports = {}  # mapping from (switch, port) to set of path names
    for path in paths_data:
        # For each cross-connect, store a tuple (switch, inPort, outPort)
        cross_connects_seq = [(oxc.switch, oxc.inPort, oxc.outPort) for oxc in path.oxcs]
        established_cross_connects.append(cross_connects_seq)
        # Collect used ports and map them to the path name
        for oxc in path.oxcs:
            # For inPort
            port_key_rx = (oxc.switch, oxc.inPort)
            if port_key_rx not in used_ports:
                used_ports[port_key_rx] = set()
            used_ports[port_key_rx].add(path.name)
            # For outPort
            port_key_tx = (oxc.switch, oxc.outPort)
            if port_key_tx not in used_ports:
                used_ports[port_key_tx] = set()
            used_ports[port_key_tx].add(path.name)
    
    # The rest of the function remains the same, using the updated paths
    paths_result = []

    for path_edges in all_paths_with_edges:
        # Extract node names from the edges
        path_nodes = [start_name] + [edge[1] for edge in path_edges]

        # Extract cross-connects for this path
        cross_connects = extract_cross_connects(graph, path_edges)
        # Convert cross-connects to a sequence of tuples for comparison
        cross_connects_seq = [(cc['switch'], cc['inPort'], cc['outPort']) for cc in cross_connects]

        # Check if this cross-connect sequence matches any established path
        is_established = cross_connects_seq in established_cross_connects

        conflicting_paths = set()

        if is_established:
            is_possible = True  # Already established
        else:
            # For each cross-connect, check if its ports are available (not in used_ports)
            is_possible = True
            for cc in cross_connects:
                in_port = cc['inPort']
                out_port = cc['outPort']
                switch = cc['switch']
                port_key_rx = (switch, in_port)
                port_key_tx = (switch, out_port)
                conflicts = False
                if port_key_rx in used_ports:
                    conflicts = True
                    conflicting_paths.update(used_ports[port_key_rx])
                if port_key_tx in used_ports:
                    conflicts = True
                    conflicting_paths.update(used_ports[port_key_tx])
                if conflicts:
                    is_possible = False
            # Note: We do not break the loop to collect all conflicting paths

        # Build the path with port information
        path_with_ports = []
        # For the start node, get the outgoing port
        if path_edges:
            first_edge = path_edges[0]
            edge_data = graph[first_edge[0]][first_edge[1]][first_edge[2]]
            src_port_num = edge_data['src_port'].split('.')[-1]
            path_with_ports.append(f"{start_name} (out:{src_port_num})")
        else:
            path_with_ports.append(start_name)
        # For intermediate nodes
        for i in range(len(cross_connects)):
            cc = cross_connects[i]
            switch = cc['switch']
            in_port = cc['inPort']
            out_port = cc['outPort']
            path_with_ports.append(f"{switch} (in:{in_port}, out:{out_port})")
        # For the end node, get the incoming port
        if path_edges:
            last_edge = path_edges[-1]
            edge_data = graph[last_edge[0]][last_edge[1]][last_edge[2]]
            dest_port_num = edge_data['dest_port'].split('.')[-1]
            path_with_ports.append(f"{end_name} (in:{dest_port_num})")
        else:
            path_with_ports.append(end_name)

        # Append the path information
        path_info = {
            'path': path_nodes,
            'path_with_ports': path_with_ports,
            'cross_connects': cross_connects,
            'is_established': is_established,
            'is_possible': is_possible
        }
        if not is_possible and conflicting_paths:
            path_info['conflicting_paths'] = list(conflicting_paths)
        paths_result.append(path_info)

    return paths_result


