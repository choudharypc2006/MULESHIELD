import networkx as nx
import random

def build_graph(cache: dict) -> nx.Graph:
    """
    Builds a synthetic transaction graph using NetworkX.
    Injects obvious fan-in/fan-out clusters centered around High-risk accounts.
    Returns the generated graph.
    """
    G = nx.Graph()
    
    # Add all accounts as nodes
    for acc_id in cache:
        G.add_node(acc_id)
        
    high_risk_ids = [acc_id for acc_id, data in cache.items() if data['risk_band'] == 'High']
    other_ids = [acc_id for acc_id, data in cache.items() if data['risk_band'] != 'High']
    
    if not high_risk_ids:
        # Fallback if no High risk accounts exist
        high_risk_ids = list(cache.keys())[:5]
        other_ids = list(cache.keys())[5:]
    
    # 1. Guarantee connections for EVERY High-risk account
    if high_risk_ids and other_ids:
        # Create a small pool of shared "hubs" (e.g. 15 accounts) that high-risk accounts will connect to.
        # This naturally creates dense mule-ring clusters.
        shared_pool_size = min(15, len(other_ids))
        shared_pool = random.sample(other_ids, shared_pool_size)
        
        for hr_id in high_risk_ids:
            # Each high-risk account connects to 3-6 accounts from the shared pool
            num_edges = random.randint(3, min(6, shared_pool_size))
            targets = random.sample(shared_pool, num_edges)
            for target in targets:
                G.add_edge(hr_id, target, weight=round(random.uniform(0.1, 1.0), 2))
                
    # 2. Add some random background noise (sparse) ONLY among Low-risk accounts
    # so we don't dilute the High-risk clusters
    low_risk_ids = [acc_id for acc_id, data in cache.items() if data['risk_band'] == 'Low']
    if len(low_risk_ids) > 1:
        for _ in range(1000):
            u, v = random.sample(low_risk_ids, 2)
            if not G.has_edge(u, v):
                G.add_edge(u, v, weight=round(random.uniform(0.1, 0.3), 2))
            
    return G

def compute_network_risk_signal(G: nx.Graph, cache: dict):
    """
    Computes a network_risk_signal per account: proximity (shortest path length)
    to the nearest High-risk account.
    """
    high_risk_nodes = set([n for n, d in cache.items() if d['risk_band'] == 'High'])
    
    # Initialize distances
    distances = {n: float('inf') for n in G.nodes()}
    
    import collections
    
    # BFS from all high_risk_nodes
    queue = collections.deque([(n, 0) for n in high_risk_nodes])
    visited = set(high_risk_nodes)
    
    for n in high_risk_nodes:
        distances[n] = 0
        
    # Standard BFS
    while queue:
        current, dist = queue.popleft()
        for neighbor in G.neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                distances[neighbor] = dist + 1
                queue.append((neighbor, dist + 1))
                
    # Assign signal to cache.
    for acc_id in cache:
        dist = distances.get(acc_id, float('inf'))
        if dist == float('inf'):
            signal = 0
        else:
            signal = round(100 / (dist + 1), 1)
        cache[acc_id]['network_risk_signal'] = signal
