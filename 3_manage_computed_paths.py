from multiverse import Multiverse, Path, OXC, search_paths
import networkx as nx

# Before running:
# On Linux:
#   export MVS_USERNAME="amar"
#   export MVS_PASSWORD="amar00"
# On Windows:
#   set MVS_USERNAME=amar
#   set MVS_PASSWORD=amar00


# Initialize and authenticate
mvs = Multiverse(server_ip="localhost")
if not mvs.token:
    exit(1)

# Create a new network and upload topology or select network if it already exist
qnet = mvs.create_network(name="qnet-example-1", json_file_path="example_topology.json")
if not qnet:
    exit(1)

# Select existing network
#qnet = mvs.select_network("qnet-example-1")
#if not qnet:
#    exit(1)


G = qnet.get_topology()
print("Network topology:")
for u, v, keys in G.edges(keys=True):
    print(f"Edge from {u} to {v} with key {keys}")


curr_paths = qnet.get_paths()
print("Existing paths:")
for path in curr_paths:
    path.print()


print("----- Automated path selection ------")

# path computation 
start_node = 'SOURCE.2'   # port number is optional
end_node = 'DETECTOR.2'

print(f"\nPath search: {start_node} -> {end_node}")

paths_result = search_paths(G, start_node, end_node, curr_paths)

# Print the results
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


# Create then delete a path from a computed path
path_to_create = Path.from_computed_path(paths_result[1])     # make sure the index is correct
path_to_create.print()

path_w_id = qnet.create_path(path_to_create)
if not path_w_id:
    exit(1)
path_w_id.print()

if not qnet.delete_path(path_w_id, force=True):
    exit(1)


# delete the network
if not mvs.delete_network(qnet):
    exit(1)