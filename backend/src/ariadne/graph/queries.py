"""Cypher query bodies used by GraphClient. Kept separate from the driver
wiring so the traversal logic can be read/reviewed without the client noise.
"""

UPSERT_NODE = """
MERGE (n:Asset {id: $id})
SET n.kind = $kind, n.label = $label, n.compromised = $compromised, n.internet_facing = $internet_facing
"""

UPSERT_EDGE = """
MATCH (a:Asset {id: $source}), (b:Asset {id: $target})
MERGE (a)-[r:%s]->(b)
"""

FETCH_TOPOLOGY = """
MATCH (n:Asset)
OPTIONAL MATCH (n)-[r]->(m:Asset)
RETURN n, r, m
"""

# Reachability: is there any path from a node flagged `internet_facing`
# down to the target? Bounded depth keeps this tractable on dense graphs.
FIND_EXPOSURE_PATH = """
MATCH (entry:Asset {internet_facing: true})
MATCH path = shortestPath((entry)-[*..8]->(target:Asset {id: $target_id}))
RETURN path
LIMIT 1
"""

FIND_DEPENDENTS = """
MATCH (target:Asset {id: $target_id})<-[:DEPENDS_ON*1..4]-(dependent:Asset)
RETURN DISTINCT dependent.id AS id
"""
