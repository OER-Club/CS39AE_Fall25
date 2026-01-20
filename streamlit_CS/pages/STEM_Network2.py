import os
import io
import pandas as pd
import networkx as nx
import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components


# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="Excel → Network Graph", layout="wide")
st.title("📌 Spreadsheet → Network Graph")
st.caption("Reads an Excel edge list (From, To, Type, Tags) and visualizes it as an interactive network.")


# ----------------------------
# Data loading
# ----------------------------
@st.cache_data(show_spinner=False)
def load_edges_from_excel_bytes(xlsx_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(xlsx_bytes))
    # Expected columns: From, To, Type, Tags
    needed = {"From", "To"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Found: {list(df.columns)}")

    # Clean up
    df = df.copy()
    df["From"] = df["From"].astype(str).str.strip()
    df["To"] = df["To"].astype(str).str.strip()

    # Optional columns
    if "Type" not in df.columns:
        df["Type"] = ""
    if "Tags" not in df.columns:
        df["Tags"] = ""

    # Drop empty endpoints
    df = df[(df["From"] != "") & (df["To"] != "")]
    return df


def load_from_repo_path_or_upload() -> pd.DataFrame:
    """
    Priority:
      1) Uploaded file in UI
      2) Repo file at data/From_To.xlsx
    """
    uploaded = st.sidebar.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])
    if uploaded is not None:
        return load_edges_from_excel_bytes(uploaded.read())

    repo_path = os.path.join("data", "From_To.xlsx")
    if os.path.exists(repo_path):
        with open(repo_path, "rb") as f:
            return load_edges_from_excel_bytes(f.read())

    st.sidebar.warning("Upload an .xlsx file or add it to repo at data/From_To.xlsx")
    st.stop()


df = load_from_repo_path_or_upload()

# ----------------------------
# Sidebar filters
# ----------------------------
st.sidebar.header("Filters")

type_options = sorted([t for t in df["Type"].dropna().astype(str).unique() if t.strip() != ""])
selected_types = st.sidebar.multiselect("Type", options=type_options, default=type_options)

tag_text = st.sidebar.text_input("Filter Tags contains (substring)", value="")

max_edges = st.sidebar.slider("Max edges to render (performance)", min_value=200, max_value=20000, value=5000, step=200)

directed = st.sidebar.toggle("Directed graph", value=True)
physics = st.sidebar.toggle("Physics layout (force-directed)", value=True)

# Apply filters
filtered = df.copy()
if selected_types:
    filtered = filtered[filtered["Type"].astype(str).isin(selected_types)]
if tag_text.strip():
    filtered = filtered[filtered["Tags"].astype(str).str.contains(tag_text.strip(), case=False, na=False)]

if len(filtered) > max_edges:
    st.sidebar.info(f"Showing first {max_edges:,} edges out of {len(filtered):,} (increase slider to render more).")
    filtered = filtered.head(max_edges)

# ----------------------------
# Build graph
# ----------------------------
@st.cache_data(show_spinner=False)
def build_graph(edges_df: pd.DataFrame, directed: bool) -> nx.Graph:
    G = nx.DiGraph() if directed else nx.Graph()

    for _, r in edges_df.iterrows():
        frm = str(r["From"]).strip()
        to = str(r["To"]).strip()
        rel_type = str(r.get("Type", "")).strip()
        tags = str(r.get("Tags", "")).strip()

        # Add nodes
        if not G.has_node(frm):
            G.add_node(frm)
        if not G.has_node(to):
            G.add_node(to)

        # Add edge with attributes
        G.add_edge(frm, to, Type=rel_type, Tags=tags)

    return G


G = build_graph(filtered, directed=directed)

# Compute stats
num_nodes = G.number_of_nodes()
num_edges = G.number_of_edges()

col1, col2, col3 = st.columns(3)
col1.metric("Nodes", f"{num_nodes:,}")
col2.metric("Edges", f"{num_edges:,}")
col3.metric("Filtered rows", f"{len(filtered):,}")

st.divider()

# ----------------------------
# Search / focus
# ----------------------------
all_nodes = sorted(list(G.nodes()))
focus_node = st.selectbox("Focus node (optional)", options=["(none)"] + all_nodes, index=0)

# Optionally create a neighborhood subgraph for clarity
use_ego = st.toggle("Show only neighborhood around focus (if selected)", value=False)
ego_hops = st.slider("Neighborhood hops", 1, 4, 2)

H = G
if focus_node != "(none)" and use_ego:
    if directed:
        # combine in/out neighborhood
        nbrs = set([focus_node])
        frontier = set([focus_node])
        for _ in range(ego_hops):
            new_frontier = set()
            for n in frontier:
                new_frontier |= set(G.predecessors(n))
                new_frontier |= set(G.successors(n))
            nbrs |= new_frontier
            frontier = new_frontier
        H = G.subgraph(nbrs).copy()
    else:
        H = nx.ego_graph(G, focus_node, radius=ego_hops)

st.caption(f"Rendering graph with **{H.number_of_nodes():,} nodes** and **{H.number_of_edges():,} edges**.")

st.subheader("Node Measures")

# For measures + communities, use an undirected version (more standard for friendship/community grouping)
H_undirected = H.to_undirected()

# --- Centralities ---
# Degree (simple count of neighbors)
deg_dict = dict(H_undirected.degree())

# Betweenness centrality
between_dict = nx.betweenness_centrality(H_undirected, normalized=True)

# Closeness centrality
close_dict = nx.closeness_centrality(H_undirected)

# --- Community detection (Greedy modularity) ---
# Returns a list of sets of nodes (communities)
communities = list(greedy_modularity_communities(H_undirected))

# Map node -> community id
community_map = {}
for i, comm in enumerate(communities):
    for node in comm:
        community_map[node] = i

# --- Build measures table ---
measures_df = pd.DataFrame({
    "Name": list(H_undirected.nodes()),
    "Degree": [deg_dict.get(n, 0) for n in H_undirected.nodes()],
    "Betweenness Centrality": [between_dict.get(n, 0.0) for n in H_undirected.nodes()],
    "Closeness Centrality": [close_dict.get(n, 0.0) for n in H_undirected.nodes()],
    "Community": [community_map.get(n, -1) for n in H_undirected.nodes()],
})

# Make it look like your screenshot (rounded values)
measures_df["Betweenness Centrality"] = measures_df["Betweenness Centrality"].round(3)
measures_df["Closeness Centrality"] = measures_df["Closeness Centrality"].round(3)

# Sort for readability
measures_df = measures_df.sort_values(by=["Community", "Degree", "Name"], ascending=[True, False, True]).reset_index(drop=True)

st.dataframe(measures_df, use_container_width=True)

# ----------------------------
# Degree Analysis (like screenshot)
# ----------------------------
st.subheader("Degree Analysis")

if len(measures_df) > 0:
    max_deg = measures_df["Degree"].max()
    top_nodes = measures_df[measures_df["Degree"] == max_deg]["Name"].tolist()
    if max_deg == 1:
        friends_word = "friend"
    else:
        friends_word = "friends"

    st.write(
        f"Most connected (highest degree): "
        f"{', '.join(top_nodes)} with **{int(max_deg)}** {friends_word}."
    )
else:
    st.write("No nodes to analyze.")

# ----------------------------
# Communities Listing (like screenshot)
# ----------------------------
st.subheader("Communities (Friendship Groups)")

if len(communities) == 0:
    st.write("No communities detected.")
else:
    for i, comm in enumerate(communities, start=1):
        members = sorted(list(comm))
        st.markdown(f"**Group {i}:** {', '.join(members)}")


# ----------------------------
# Render with PyVis
# ----------------------------
def nx_to_pyvis_html(graph: nx.Graph, physics: bool, focus: str | None = None) -> str:
    net = Network(height="700px", width="100%", bgcolor="#FFFFFF", font_color="#222222", directed=isinstance(graph, nx.DiGraph))

    # Physics controls
    net.toggle_physics(physics)

    # Add nodes (size by degree)
    degrees = dict(graph.degree())
    max_deg = max(degrees.values()) if degrees else 1

    for n in graph.nodes():
        deg = degrees.get(n, 0)
        size = 10 + (30 * (deg / max_deg)) if max_deg else 10

        title = f"<b>{n}</b><br>Degree: {deg}"
        node_kwargs = dict(label=str(n), title=title, size=size)

        if focus and n == focus:
            node_kwargs["color"] = "#FFB000"  # highlight focus node

        net.add_node(n, **node_kwargs)

    # Add edges
    for u, v, attrs in graph.edges(data=True):
        etype = attrs.get("Type", "")
        tags = attrs.get("Tags", "")

        edge_title = "<br>".join([x for x in [
            f"<b>From:</b> {u}",
            f"<b>To:</b> {v}",
            f"<b>Type:</b> {etype}" if etype else "",
            f"<b>Tags:</b> {tags}" if tags else ""
        ] if x])

        # Show type as label (optional)
        label = str(etype) if str(etype).strip() else ""

        net.add_edge(u, v, title=edge_title, label=label)

    # Extra UI
    net.show_buttons(filter_=["physics"])

    return net.generate_html()


html = nx_to_pyvis_html(H, physics=physics, focus=None if focus_node == "(none)" else focus_node)
components.html(html, height=750, scrolling=True)

st.divider()

# ----------------------------
# Show data table
# ----------------------------
with st.expander("Show filtered edge table"):
    st.dataframe(filtered, use_container_width=True)

# ----------------------------
# Export options
# ----------------------------
st.subheader("Export")
colA, colB = st.columns(2)

with colA:
    # Export filtered edges as CSV
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered edges (CSV)",
        data=csv_bytes,
        file_name="filtered_edges.csv",
        mime="text/csv",
    )

with colB:
    # Export graph as GraphML (useful for Gephi)
    graphml_bytes = io.BytesIO()
    nx.write_graphml(H, graphml_bytes)
    st.download_button(
        "Download graph (GraphML)",
        data=graphml_bytes.getvalue(),
        file_name="network.graphml",
        mime="application/xml",
    )
