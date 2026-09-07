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
#
# `[*0..8]` (not `[*..8]`, which defaults to a minimum of 1 hop) so a target
# that is itself internet_facing resolves to its own trivial zero-hop path
# instead of being invisible to this query. `ORDER BY length(path)` matters
# once more than one node is internet_facing: without it, a multi-hop path
# through some other entry point can be returned in place of the shorter,
# more direct (and more dangerous) exposure -- picking the shortest is what
# makes this deterministic rather than dependent on Neo4j's arbitrary
# result ordering.
FIND_EXPOSURE_PATH = """
MATCH (entry:Asset {internet_facing: true})
MATCH path = shortestPath((entry)-[*0..8]->(target:Asset {id: $target_id}))
RETURN path
ORDER BY length(path) ASC
LIMIT 1
"""

FIND_DEPENDENTS = """
MATCH (target:Asset {id: $target_id})<-[:DEPENDS_ON*1..4]-(dependent:Asset)
RETURN DISTINCT dependent.id AS id
"""

# The most recently ingested CTI report, persisted in Neo4j (not process
# memory) so it survives an API restart -- a redeploy should never make the
# frontend forget which report is currently active.
UPSERT_LATEST_CTI = """
MERGE (c:CtiState {id: "latest"})
SET c.cve_id = $cve_id, c.target_software = $target_software,
    c.affected_versions = $affected_versions, c.attack_vector = $attack_vector,
    c.source_report = $source_report
"""

FETCH_LATEST_CTI = """
MATCH (c:CtiState {id: "latest"})
RETURN c
"""
