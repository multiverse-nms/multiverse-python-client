# multiverse/multiverse.py

import requests
import json
import os

from .network import Network

class Multiverse:
    def __init__(self, server_ip="localhost"):
        username = os.getenv("MVS_USERNAME")
        password = os.getenv("MVS_PASSWORD")

        if not username or not password:
            raise ValueError("Username or password is not set in environment variables: MVS_USERNAME and MVS_PASSWORD")

        self._token = None
        self._BASE_URL = f"http://{server_ip}:8787/api/topology"
        self._AUTH_URL = f"http://{server_ip}:8888/realms/multiverse/protocol/openid-connect/token"
        self.session = requests.Session()
        self.login(username, password)

    @property
    def token(self):
        return self._token

    def login(self, username, password):
        """Authenticate with the backend and store the access token."""
        print(f"Logging in as {username}")
        url = self._AUTH_URL
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": "multiverse-access",
            "username": username,
            "password": password,
            "grant_type": "password"
        }
        response = self.session.post(url, headers=headers, data=data)
        if response.status_code == 200:
            self._token = response.json()['access_token']
            self.session.headers.update({'Authorization': f'Bearer {self._token}'})
            print("Logged in successfully.")
        else:
            print(f"Login failed: {response.text}")

    def create_network(self, name, json_file_path):
        """Create a network with topology from a JSON file."""
        url = f"{self._BASE_URL}/upload"
        headers = {'Content-Type': 'application/json'}
        with open(json_file_path, 'r') as file:
            topology = json.load(file)
            topology['name'] = name
        response = self.session.post(url, headers=headers, data=json.dumps(topology))
        if response.status_code == 201:
            network_id = response.json()['id']
            print(f"Network '{name}' created with ID: {network_id}")
            return Network(self, network_id, name)
        else:
            print(f"Failed to upload network: {response.status_code} {response.text}")
            if response.status_code == 409:
                print(f"Network '{name}' already exists.")
                return self.select_network(name)        
            return None

    def select_network(self, name):
        """Select a network by name and return a Network object."""
        networks = self.get_networks()
        if networks:
            for network in networks:
                if network['name'] == name:
                    return Network(self, network['id'], name)
        print(f"Network '{name}' not found.")
        return None

    def get_networks(self):
        """Fetch all networks."""
        url = f"{self._BASE_URL}/subnet"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get networks: {response.text}")
            return None

    def delete_network(self, network):
        """Delete a network."""
        if not network.id:
            print("Network ID is required to delete a network.")
            return False
        url = f"{self._BASE_URL}/subnet/{network.id}"
        response = self.session.delete(url)
        if response.status_code == 200 or response.status_code == 204:
            print(f"Network {network.name} deleted.")
            return True
        else:
            print(f"Failed to delete network: {response.text}")
            return False
