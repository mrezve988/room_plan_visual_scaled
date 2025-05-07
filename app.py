
import streamlit as st
import networkx as nx
import tempfile
from pyvis.network import Network
import streamlit.components.v1 as components

# Updated Ideal configuration
IDEAL_ROOMS = {
    'Living': 22,
    'Dining': 12,
    'Kitchen': 10,
    'Store': 2.5,
    'Toilet1': 2.5,
    'Bedroom1': 13,
    'Bath1': 4,
    'Bedroom2': 10,
    'Bedroom3': 10
}

IDEAL_EDGES = [
    ('Living', 'Dining'),
    ('Dining', 'Toilet1'),
    ('Dining', 'Kitchen'),
    ('Kitchen', 'Store'),
    ('Living', 'Bedroom1'),
    ('Bedroom1', 'Bath1'),
    ('Living', 'Bedroom2'),
    ('Bedroom2', 'Toilet1'),
    ('Living', 'Bedroom3'),
    ('Bedroom3', 'Toilet1')
]

def score_room_size(ideal_size, candidate_size):
    return max(0, 1 - abs(ideal_size - candidate_size) / ideal_size)

def score_adjacency(ideal_graph, candidate_graph):
    matched = sum(1 for u, v in ideal_graph.edges if candidate_graph.has_edge(u, v))
    total = len(ideal_graph.edges)
    return matched / total if total > 0 else 0

def suggest_improvements(ideal_graph, candidate_graph, ideal_sizes, candidate_sizes):
    suggestions = []
    for u, v in ideal_graph.edges:
        if not candidate_graph.has_edge(u, v):
            suggestions.append(f"Add connection between {u} and {v}.")
    for room, ideal_size in ideal_sizes.items():
        if room in candidate_sizes:
            size_diff = ideal_size - candidate_sizes[room]
            if abs(size_diff) / ideal_size > 0.2:
                if size_diff > 0:
                    suggestions.append(f"Increase size of {room} (currently {candidate_sizes[room]} m²).")
                else:
                    suggestions.append(f"Reduce size of {room} (currently {candidate_sizes[room]} m²).")
    return suggestions

def build_graph(rooms, edges):
    G = nx.Graph()
    for room in rooms:
        G.add_node(room)
    for line in edges.strip().split("\n"):
        try:
            u, v = line.strip().split(",")
            G.add_edge(u.strip(), v.strip())
        except:
            continue
    return G

def display_graph_pyvis(G, sizes_dict):
    net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="black")
    for node in G.nodes:
        size = sizes_dict.get(node, 10)
        net.add_node(node, label=node, value=size)
    for u, v in G.edges:
        net.add_edge(u, v)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    net.save_graph(tmp_file.name)
    return tmp_file.name

st.set_page_config(page_title="Room Plan Evaluator (Scaled Circles)", layout="wide")
st.title("🏠 Room Plan Evaluator: Proportional Room Size Visualization")

st.subheader("🔹 Step 1: Enter Room Sizes")
candidate_sizes = {}
for room, default_size in IDEAL_ROOMS.items():
    candidate_sizes[room] = st.number_input(f"{room} size (m²)", min_value=1.0, value=float(default_size), key=room)

st.subheader("🔹 Step 2: Define Room Adjacencies")
st.markdown("Enter one pair per line, format: `RoomA, RoomB`")
edge_input = st.text_area("Candidate Adjacency List", "Living, Dining\nDining, Kitchen\nKitchen, Store\nStore, Toilet1")

if st.button("Evaluate Plan"):
    candidate_graph = build_graph(candidate_sizes.keys(), edge_input)
    ideal_graph = nx.Graph()
    ideal_graph.add_nodes_from(IDEAL_ROOMS.keys())
    ideal_graph.add_edges_from(IDEAL_EDGES)

    size_score = sum(score_room_size(IDEAL_ROOMS[r], candidate_sizes[r]) for r in IDEAL_ROOMS) / len(IDEAL_ROOMS)
    adjacency_score = score_adjacency(ideal_graph, candidate_graph)
    final_score = 0.5 * size_score + 0.5 * adjacency_score

    st.success(f"✅ Final Plan Score: {final_score:.2f}")
    st.markdown(f"- Size Match Score: `{size_score:.2f}`")
    st.markdown(f"- Adjacency Match Score: `{adjacency_score:.2f}`")

    suggestions = suggest_improvements(ideal_graph, candidate_graph, IDEAL_ROOMS, candidate_sizes)
    if suggestions:
        st.warning("🔧 Suggestions to Improve Plan:")
        for s in suggestions:
            st.markdown(f"- {s}")
    else:
        st.success("🎯 Your plan closely matches the ideal!")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Ideal Plan Graph")
        html_ideal = display_graph_pyvis(ideal_graph, IDEAL_ROOMS)
        with open(html_ideal, 'r', encoding='utf-8') as f:
            components.html(f.read(), height=500, scrolling=True)
    with col2:
        st.markdown("### Candidate Plan Graph")
        html_candidate = display_graph_pyvis(candidate_graph, candidate_sizes)
        with open(html_candidate, 'r', encoding='utf-8') as f:
            components.html(f.read(), height=500, scrolling=True)
