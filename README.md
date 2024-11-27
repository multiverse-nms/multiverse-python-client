# Multiverse Python Client Library

The Multiverse Python Client Library provides an interface to easily interact with the Multiverse network management platform via its REST API. This library allows users to create, select, and delete networks; retrieve network topology; manage optical paths; and perform path searches.

## Features

- **Network Management**: Create, select, download, and delete networks using JSON-defined topologies.
- **Topology Retrieval**: Obtain the network topology as a NetworkX `MultiDiGraph`.
- **Path Management**: Get existing optical paths with their cross-connects, manually create paths, and delete paths.
- **Path Search**: Compute all possible paths between source and destination nodes, with optional ports, and create paths from computed results.

## Dependencies

- **Python 3.6+**
- **NetworkX**: For handling network topologies. Install via pip:

  ```bash
  pip install networkx
  ```

## Installation
[TDB]

## Usage

### Authentication

Before using the library, set your Multiverse credentials as environment variables.

**On Linux/macOS:**

```bash
export MVS_USERNAME="amar"
export MVS_PASSWORD="amar00"
```

**On Windows:**

```cmd
set MVS_USERNAME=amar
set MVS_PASSWORD=amar00
```

### Initialize and Authenticate

```python
mvs = Multiverse(server_ip="localhost")
if not mvs.token:
    exit(1)
```

### Network Management

#### Create a network defined in JSON format

```python
# Create a new network and upload topology and paths from JSON
# Note: Returns the network instance if the name already exists
qnet = mvs.create_network(name="qnet-example", json_file_path="example_topology.json")
if not qnet:
    exit(1)
```

#### Alternatively, select an existing network

```python
qnet = mvs.select_network("qnet-example")
if not qnet:
    exit(1)
```

#### Delete a Network

```python
if not mvs.delete_network(qnet):
    exit(1)
```

#### Download network in JSON format

```python
# Returns topology and paths in JSON (same format as in create_network)
json_content = qnet.download_json()
if not json_content:
    exit(1)
print(json.dumps(json_content))
```

### Topology Retrieval

```python
G = qnet.get_topology()
print("Network topology:")
for u, v, keys in G.edges(keys=True):
    print(f"  Edge from {u} to {v} with key {keys}")
```

### Path Management

#### Get Existing Paths

```python
curr_paths = qnet.get_paths()
print("Existing paths:")
for path in curr_paths:
    path.print()
```

#### Delete All Paths

```python
for path in curr_paths:
    if not qnet.delete_path(path, force=True):
        exit(1)
```

#### Manually Create a Path

**Option 1: From a Dictionary**

```python
# Define path as a dictionary
path_dict = {
    "name": "TRAIL_1",
    "label": "SOURCE.1_TO_DETECTOR.1",
    "oxcs": [
        {
            "label": "NIST_SOURCE.1_TO_UMD",
            "switch": "NIST",
            "inPort": "1",
            "outPort": "9"
        },
        {
            "label": "UMD_TO_DETECTOR.1",
            "switch": "UMD",
            "inPort": "1",
            "outPort": "11"
        }
    ]
}

# Create path from dictionary
path1 = Path.from_dict(path_dict)
path_w_id = qnet.create_path(path1)
if not path_w_id:
    exit(1)

# Delete the path
if not qnet.delete_path(path1, force=True):
    exit(1)
```

**Option 2: Using Path and OXC Objects**

```python
# Create Path and OXC objects
path2 = Path(name="TRAIL_1", label="SOURCE.1_TO_DETECTOR.1")
oxc1 = OXC(label="NIST_SOURCE.1_TO_UMD", switch="NIST", inPort="1", outPort="9")
oxc2 = OXC(label="UMD_TO_DETECTOR.1", switch="UMD", inPort="1", outPort="11")
path2.add_oxc(oxc1)
path2.add_oxc(oxc2)

# Create the path
path_w_id = qnet.create_path(path2)
if not path_w_id:
    exit(1)

# Delete the path
if not qnet.delete_path(path2, force=True):
    exit(1)
```

### Path Search and Creation

```python
# Define source and destination nodes
start_node = 'SOURCE.2'   # Port number is optional
end_node = 'DETECTOR.2'

print(f"\nPath search: {start_node} -> {end_node}")

# Perform path search
paths_result = search_paths(G, start_node, end_node, curr_paths)

# Display search results
for idx, info in enumerate(paths_result, 0):
    path_str = ' -> '.join(info['path_with_ports'])
    status = 'Established' if info['is_established'] else 'Not Established'
    possible_status = 'Possible' if info['is_possible'] else 'Not Possible'
    print(f"Path {idx}: {path_str} [{status}, {possible_status}]")
    print("Cross-connects:")
    for cc in info['cross_connects']:
        print(f"  Switch: {cc['switch']}, InPort: {cc['inPort']}, OutPort: {cc['outPort']}")
    if not info['is_possible'] and 'conflicting_paths' in info:
        conflicting = ', '.join(info['conflicting_paths'])
        print(f"Conflicts with established paths: {conflicting}")
    print()

# Create a path from computed results
path_to_create = Path.from_computed_path(paths_result[1])  # Ensure the index is correct
path_to_create.print()

# Create the path
path_w_id = qnet.create_path(path_to_create)
if not path_w_id:
    exit(1)

# Delete the path
if not qnet.delete_path(path_w_id, force=True):
    exit(1)
```

## Examples

You can find complete examples for:
- [Basic Network Creation and Deletion](1_create_delete_network.py)
- [Manual Path Creation](2_manage_manual_paths.py)
- [Automated Path Search and Creation](3_manage_computed_paths.py)