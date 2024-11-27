from multiverse import Multiverse, Path, OXC, search_paths
import networkx as nx
import json

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
    print(f"  Edge from {u} to {v} with key {keys}")

curr_paths = qnet.get_paths()
print("Existing paths:")
for path in curr_paths:
    path.print()

print("Download network content in JSON:")
json_content = qnet.download_json()
if json_content:
    print(json.dumps(json_content))

exit(0)

# delete the network
if not mvs.delete_network(qnet):
    exit(1)

exit(0)