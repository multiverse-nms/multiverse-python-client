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

# Delete all paths
for path in curr_paths:
    if not qnet.delete_path(path, force=True):
        exit(1)


print("----- Manual path selection ------")

# Manually create a path
# Option 1: From dict
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
path1 = Path.from_dict(path_dict)

path_w_id = qnet.create_path(path1)
if not path_w_id:
    exit(1)
# path_w_id.print()
if not qnet.delete_path(path1, force=True):
    exit(1)


# Option 2: Create the Path and OXC objects
path2 = Path(name="TRAIL_1", label="SOURCE.1_TO_DETECTOR.1")
oxc1 = OXC(label="NIST_SOURCE.1_TO_UMD", switch="NIST", inPort="1", outPort="9")
oxc2 = OXC(label="UMD_TO_DETECTOR.1", switch="UMD", inPort="1", outPort="11")
path2.add_oxc(oxc1)
path2.add_oxc(oxc2)

path_w_id = qnet.create_path(path2)
if not path_w_id:
    exit(1)
# path_w_id.print()
if not qnet.delete_path(path2, force=True):
    exit(1)



# delete the network
if not mvs.delete_network(qnet):
    exit(1)