import networkx as nx
from typing import List, Dict, Any, Tuple

class RailwayNetworkAnalyzer:
    def __init__(self):
        self.network = nx.Graph()
        self._initialize_delhi_corridor()
        
    def _initialize_delhi_corridor(self):
        """Build Delhi division key corridors network"""
        corridor_nodes = [
            ("NDLS", {"name": "New Delhi Central", "type": "TERMINAL", "lat": 28.643, "lng": 77.219}),
            ("DLI", {"name": "Old Delhi Junction", "type": "JUNCTION", "lat": 28.661, "lng": 77.228}),
            ("NZM", {"name": "Hazrat Nizamuddin", "type": "TERMINAL", "lat": 28.588, "lng": 77.253}),
            ("TKD", {"name": "Tuglakabad Freight Hub", "type": "YARD", "lat": 28.502, "lng": 77.291}),
            ("PWL", {"name": "Palwal Junction", "type": "JUNCTION", "lat": 28.148, "lng": 77.332}),
            ("GZB", {"name": "Ghaziabad Junction", "type": "JUNCTION", "lat": 28.669, "lng": 77.438}),
            ("ALJN", {"name": "Aligarh Junction", "type": "JUNCTION", "lat": 27.897, "lng": 78.088}),
            ("AGC", {"name": "Agra Cantt", "type": "JUNCTION", "lat": 27.159, "lng": 78.007}),
            ("PNP", {"name": "Panipat Junction", "type": "JUNCTION", "lat": 29.390, "lng": 76.963}),
            ("UMB", {"name": "Ambala Cantt", "type": "JUNCTION", "lat": 30.361, "lng": 76.840}),
        ]
        
        for node, attrs in corridor_nodes:
            self.network.add_node(node, **attrs)
            
        corridor_edges = [
            ("NDLS", "GZB", {"section_code": "NDLS-GZB", "distance_km": 25.4, "tracks": 4, "max_speed": 130, "density": "VERY_HIGH"}),
            ("NDLS", "NZM", {"section_code": "NDLS-NZM", "distance_km": 7.2, "tracks": 2, "max_speed": 110, "density": "HIGH"}),
            ("NZM", "TKD", {"section_code": "NZM-TKD", "distance_km": 14.8, "tracks": 4, "max_speed": 130, "density": "VERY_HIGH"}),
            ("TKD", "PWL", {"section_code": "TKD-PWL", "distance_km": 38.6, "tracks": 4, "max_speed": 160, "density": "VERY_HIGH"}),
            ("GZB", "ALJN", {"section_code": "GZB-ALJN", "distance_km": 106.1, "tracks": 2, "max_speed": 130, "density": "HIGH"}),
            ("PWL", "AGC", {"section_code": "PWL-AGC", "distance_km": 134.5, "tracks": 3, "max_speed": 160, "density": "HIGH"}),
            ("NDLS", "PNP", {"section_code": "NDLS-PNP", "distance_km": 88.9, "tracks": 2, "max_speed": 130, "density": "HIGH"}),
            ("PNP", "UMB", {"section_code": "PNP-UMB", "distance_km": 109.3, "tracks": 2, "max_speed": 130, "density": "HIGH"}),
            ("DLI", "GZB", {"section_code": "DLI-GZB", "distance_km": 20.1, "tracks": 2, "max_speed": 100, "density": "MEDIUM"}),
        ]
        
        for u, v, attrs in corridor_edges:
            self.network.add_edge(u, v, **attrs)

    def analyze_dependency_chain(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build DAG of tasks and find execution order, cycle detection, critical path"""
        dag = nx.DiGraph()
        task_lookup = {}
        for t in tasks:
            tid = str(t.get("id") or t.get("request_id"))
            task_lookup[tid] = t
            dag.add_node(tid, duration=float(t.get("estimated_duration", 2.0)), title=t.get("task_title", ""))
            
        for t in tasks:
            tid = str(t.get("id") or t.get("request_id"))
            deps = t.get("task_dependencies") or []
            if isinstance(deps, list):
                for dep in deps:
                    s_dep = str(dep)
                    if s_dep in task_lookup:
                        dag.add_edge(s_dep, tid)

        is_dag = nx.is_directed_acyclic_graph(dag)
        cycles = []
        if not is_dag:
            cycles = list(nx.simple_cycles(dag))
            return {
                "valid": False,
                "error": "Cyclic dependencies detected in maintenance requests",
                "cycles": cycles
            }
            
        topological_order = list(nx.topological_sort(dag))
        
        # Calculate critical path
        critical_path = []
        try:
            critical_path = nx.dag_longest_path(dag, weight="duration")
        except Exception:
            critical_path = topological_order
            
        return {
            "valid": True,
            "is_acyclic": True,
            "topological_order": topological_order,
            "critical_path": critical_path,
            "total_nodes": dag.number_of_nodes(),
            "total_dependencies": dag.number_of_edges()
        }

    def find_rerouting_alternatives(self, origin: str, destination: str, blocked_section: str) -> List[Dict[str, Any]]:
        """If a section is completely blocked, find alternative detour routes in network"""
        subgraph = self.network.copy()
        
        # Remove blocked edge
        for u, v, data in list(subgraph.edges(data=True)):
            if data.get("section_code") == blocked_section:
                subgraph.remove_edge(u, v)
                break
                
        try:
            paths = list(nx.all_simple_paths(subgraph, source=origin, target=destination, cutoff=5))
            results = []
            for path in paths[:3]:
                dist = sum(
                    subgraph.get_edge_data(path[i], path[i+1])["distance_km"]
                    for i in range(len(path)-1)
                )
                results.append({
                    "path": " -> ".join(path),
                    "stops": path,
                    "distance_km": round(dist, 1),
                    "detour_penalty_minutes": round(dist * 0.8, 0)
                })
            return results
        except Exception:
            return []

    def get_network_topology(self) -> Dict[str, Any]:
        """Return nodes and edges formatted for visual topology graph in React UI"""
        nodes = []
        for n, d in self.network.nodes(data=True):
            nodes.append({
                "id": n,
                "label": d.get("name", n),
                "type": d.get("type", "STATION"),
                "lat": d.get("lat"),
                "lng": d.get("lng")
            })
            
        edges = []
        for u, v, d in self.network.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "section_code": d.get("section_code"),
                "distance_km": d.get("distance_km"),
                "tracks": d.get("tracks"),
                "density": d.get("density")
            })
            
        return {"nodes": nodes, "edges": edges}

railway_network = RailwayNetworkAnalyzer()
