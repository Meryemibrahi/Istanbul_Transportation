--schema


DROP MATERIALIZED VIEW IF EXISTS route_shapes;

CREATE MATERIALIZED VIEW route_shapes AS
SELECT DISTINCT
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    t.shape_id,
    sg.geom
FROM routes r
JOIN trips t ON r.route_id = t.route_id
JOIN shape_geoms sg ON t.shape_id = sg.shape_id;

CREATE INDEX IF NOT EXISTS route_shapes_geom_gix ON route_shapes USING GIST (geom);



DROP MATERIALIZED VIEW IF EXISTS route_trip_counts;

CREATE MATERIALIZED VIEW route_trip_counts AS
SELECT
    rs.route_id,
    rs.route_short_name,
    rs.route_long_name,
    COUNT(DISTINCT t.trip_id) AS trip_count,
    rs.geom
FROM route_shapes rs
JOIN trips t
  ON rs.route_id = t.route_id
 AND rs.shape_id = t.shape_id
GROUP BY rs.route_id, rs.route_short_name, rs.route_long_name, rs.shape_id, rs.geom;

-----


--Full network output
--Input needed: none
--Output returned: route_id, route_short_name, route_long_name, geojson
--Used for: displaying the full transit network on the map

SELECT
    route_id,
    route_short_name,
    route_long_name,
    ST_AsGeoJSON(geom) AS geojson
FROM route_shapes;


--One selected route + stops
--Input needed: route_id
--Output returned:stop_id, stop_name, stop_sequence, stop_geojson
--Used for: displaying one selected route’s stops in order

WITH one_trip AS (
    SELECT trip_id, shape_id
    FROM trips
    WHERE route_id = '28195'
    LIMIT 1
)
SELECT
    s.stop_id,
    s.stop_name,
    st.stop_sequence,
    ST_AsGeoJSON(s.geom) AS stop_geojson
FROM one_trip ot
JOIN stop_times st ON ot.trip_id = st.trip_id
JOIN stops s ON st.stop_id = s.stop_id
ORDER BY st.stop_sequence;


--Top routes by trip count
--Input needed: none
--Output returned: route_id, route_short_name, route_long_name, trip_count
--Used for: showing the busiest or most scheduled routes

SELECT
    r.route_id,
    r.route_short_name,
    r.route_long_name,
    COUNT(t.trip_id) AS trip_count
FROM routes r
JOIN trips t ON r.route_id = t.route_id
GROUP BY r.route_id, r.route_short_name, r.route_long_name
ORDER BY trip_count DESC
LIMIT 20;


--Busiest stops in morning hours
--Input needed: start time, end time
--Output returned: stop_id, stop_name, morning_arrivals, geojson
--Used for: 

SELECT
    s.stop_id,
    s.stop_name,
    COUNT(*) AS morning_arrivals,
    ST_AsGeoJSON(s.geom) AS geojson
FROM stop_times st
JOIN stops s ON st.stop_id = s.stop_id
WHERE st.arrival_time >= '07:00:00'
  AND st.arrival_time < '09:00:00'
GROUP BY s.stop_id, s.stop_name, s.geom
ORDER BY morning_arrivals DESC
LIMIT 20;


SELECT COUNT(*) FROM stop_vertices;
SELECT COUNT(*) FROM transit_edges_raw;
SELECT COUNT(*) FROM transit_edges;


SELECT *
FROM transit_edges
LIMIT 10;

SELECT vertex_id, stop_id, stop_name
FROM stop_vertices
WHERE stop_name ILIKE '%METRO%'
LIMIT 20;


--Dijkstra shortest path stop list
--Input needed: start_vertex_id, end_vertex_id
--Output returned: seq, node, stop_id, stop_name, edge, cost, agg_cost
--Used for: showing the ordered list of stops in the shortest path result

WITH path AS (
    SELECT *
    FROM pgr_dijkstra(
        'SELECT id, source, target, cost FROM transit_edges',
        565,
        564,
        directed := true
    )
)
SELECT
    p.seq,
    p.node,
    sv.stop_id,
    sv.stop_name,
    p.edge,
    p.cost,
    p.agg_cost
FROM path p
LEFT JOIN stop_vertices sv
    ON p.node = sv.vertex_id
ORDER BY p.seq;


--Dijkstra shortest path geometry
--Input needed: start_vertex_id, end_vertex_id
--Output returned: seq, from_stop_id, to_stop_id, cost, edge_geojson
--Used for: displaying the shortest path on the map as connected route segments

WITH path AS (
    SELECT *
    FROM pgr_dijkstra(
        'SELECT id, source, target, cost FROM transit_edges',
        565,
        564,
        directed := true
    )
)
SELECT
    p.seq,
    e.from_stop_id,
    e.to_stop_id,
    e.cost,
    ST_AsGeoJSON(e.geom) AS edge_geojson
FROM path p
JOIN transit_edges e
    ON p.edge = e.id
ORDER BY p.seq;

--A* shortest path stop list
--Input needed: start_vertex_id, end_vertex_id
--Output returned: seq, node, stop_id, stop_name, edge, cost, agg_cost
--Used for: showing the ordered list of stops in the shortest path result using the A* algorithm

WITH path AS (
    SELECT *
    FROM pgr_astar(
        'SELECT id, source, target, cost, x1, y1, x2, y2 FROM transit_edges',
        565,
        564,
        directed := true
    )
)
SELECT
    p.seq,
    p.node,
    sv.stop_id,
    sv.stop_name,
    p.edge,
    p.cost,
    p.agg_cost
FROM path p
LEFT JOIN stop_vertices sv
    ON p.node = sv.vertex_id
ORDER BY p.seq;


--A* shortest path geometry
--Input needed: start_vertex_id, end_vertex_id
--Output returned: seq, from_stop_id, to_stop_id, cost, edge_geojson
--Used for: displaying the A* shortest path on the map as connected route segments

WITH path AS (           
    SELECT *
    FROM pgr_astar(
        'SELECT id, source, target, cost, x1, y1, x2, y2 FROM transit_edges',
        565,
        564,
        directed := true
    )
)
SELECT
    p.seq,
    e.from_stop_id,
    e.to_stop_id,
    e.cost,
    ST_AsGeoJSON(e.geom) AS edge_geojson
FROM path p
JOIN transit_edges e
    ON p.edge = e.id
ORDER BY p.seq;




WITH path AS (
    SELECT *
    FROM pgr_dijkstra(
        'SELECT id, source, target, cost FROM transit_edges',
        565,
        564,
        directed := true
    )
)
SELECT
    COUNT(*) AS step_count,
    MAX(agg_cost) AS total_cost
FROM path;

WITH path AS (
    SELECT *
    FROM pgr_astar(
        'SELECT id, source, target, cost, x1, y1, x2, y2 FROM transit_edges',
        565,
        564,
        directed := true
    )
)
SELECT
    COUNT(*) AS step_count,
    MAX(agg_cost) AS total_cost
FROM path;





--TSP selected stops
--Initial input needed: selected vertex_id list
--Output returned: vertex_id, stop_id, stop_name
--Used for: defining which stops will be included in the multi-stop optimization

CREATE TABLE tsp_selected_stops AS
SELECT *
FROM stop_vertices
WHERE vertex_id IN (564, 565, 596, 1325);

/* Check which stops were selected */
SELECT
    vertex_id,
    stop_id,
    stop_name
FROM tsp_selected_stops
ORDER BY vertex_id;



--TSP cost matrix
--Depends on: selected stop list
--Output returned: start_vid, end_vid, agg_cost
--Used for: computing pairwise travel cost between selected stops
CREATE TABLE tsp_cost_matrix AS
SELECT *
FROM pgr_dijkstraCostMatrix(
    'SELECT id, source, target, cost, cost AS reverse_cost FROM transit_edges',
    (SELECT array_agg(vertex_id) FROM tsp_selected_stops),
    directed := false
);

/* Check the generated pairwise costs */
SELECT *
FROM tsp_cost_matrix
ORDER BY start_vid, end_vid;



--TSP optimized stop order
--Depends on: cost matrix, start_id
--Output returned: seq, node, cost, agg_cost
--Used for: finding the best visiting order
CREATE TABLE tsp_order AS
SELECT *
FROM pgr_TSP(
    $$
    SELECT * FROM tsp_cost_matrix
    $$,
    start_id := 564
);

/* Check the raw TSP order result */
SELECT *
FROM tsp_order
ORDER BY seq;



--TSP readable stop order
--Depends on: TSP optimized stop order
--Output returned: seq, vertex_id, stop_id, stop_name, cost, agg_cost
--Used for: showing the optimized stop order in a readable form with stop names
SELECT
    t.seq,
    t.node AS vertex_id,
    s.stop_id,
    s.stop_name,
    t.cost,
    t.agg_cost
FROM tsp_order t
JOIN stop_vertices s
    ON t.node = s.vertex_id
ORDER BY t.seq;




--TSP consecutive stop pairs
--Depends on: TSP optimized stop order
--Output returned: seq, start_vertex_id, end_vertex_id
--Used for: creating route legs for reconstruction
SELECT
    t1.seq,
    t1.node AS start_vertex_id,
    t2.node AS end_vertex_id
FROM tsp_order t1
JOIN tsp_order t2
    ON t2.seq = t1.seq + 1
ORDER BY t1.seq;

/* Check the generated TSP pairs */
SELECT *
FROM tsp_pairs
ORDER BY seq;




--TSP reconstructed route steps
--Depends on: TSP consecutive stop pairs
--Output returned: tsp_leg, path_seq, edge_seq, node, edge, cost, agg_cost
--Used for: rebuilding the actual shortest path for each TSP leg

CREATE TABLE tsp_route_steps AS
SELECT
    p.seq AS tsp_leg,           -- which TSP leg this belongs to
    d.seq AS path_seq,          -- order inside the Dijkstra path
    d.path_seq AS edge_seq,     -- edge order
    d.node,
    d.edge,
    d.cost,
    d.agg_cost
FROM tsp_pairs p
CROSS JOIN LATERAL pgr_dijkstra(
    'SELECT id, source, target, cost FROM transit_edges',
    p.start_vertex_id,
    p.end_vertex_id,
    directed := true
) AS d;

/* Check the reconstructed route steps */
SELECT *
FROM tsp_route_steps
ORDER BY tsp_leg, path_seq;




--TSP readable route steps
--Depends on: TSP reconstructed route steps
--Output returned: tsp_leg, path_seq, vertex_id, stop_id, stop_name, edge, cost, agg_cost
--Used for: showing the detailed stop-by-stop route for each TSP leg in a readable form
SELECT
    r.tsp_leg,
    r.path_seq,
    r.node AS vertex_id,
    sv.stop_id,
    sv.stop_name,
    r.edge,
    r.cost,
    r.agg_cost
FROM tsp_route_steps r
LEFT JOIN stop_vertices sv
    ON r.node = sv.vertex_id
ORDER BY r.tsp_leg, r.path_seq;



--TSP route geometry
--Depends on: TSP reconstructed route steps
--Output returned: tsp_leg, path_seq, from_stop_id, to_stop_id, cost, edge_geojson
--Used for: displaying the final optimized multi-stop route on the map
SELECT
    r.tsp_leg,
    r.path_seq,
    e.from_stop_id,
    e.to_stop_id,
    e.cost,
    ST_AsGeoJSON(e.geom) AS edge_geojson
FROM tsp_route_steps r
JOIN transit_edges e
    ON r.edge = e.id
ORDER BY r.tsp_leg, r.path_seq;



--SUMMARY OUTPUTS

/* Summary 1: TSP order total cost from the TSP output */
SELECT
    MAX(agg_cost) AS tsp_total_cost
FROM tsp_order;

/* Summary 2: Sum of the actual reconstructed path costs */
SELECT
    SUM(cost) AS reconstructed_total_cost
FROM tsp_route_steps
WHERE edge <> -1;


