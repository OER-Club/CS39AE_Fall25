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
st.set_page_config(page_title="STEM Network (Excel → Graph)", layout="wide")
st.title("🔗 STEM Network")
st.caption(
    "Reads an Excel edge list (From, To, optional Type/Tags) and visualizes it as an interactive network, "
    "with node measures, communities, and an inspector panel."
)

# ----------------------------
# Data loading
# ----------------------------
@st.cache_data(show_spinner=False)
def load_edges_from_excel_bytes(xlsx_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(xlsx_bytes))

    needed = {"From", "To"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Found: {list(df.columns)}")

    df = df.copy()
    df["From"] = df["From"].astype(str).str.strip()
    df["To"] = df["To"].astype(str).str.strip()

    if "Type" not in df.columns:
        df["Type"] = ""
    if "Tags" not in df.columns:
        df["Tags"] = ""

    df["Type"] = df["Type"].fillna("").astype(str)
    df["Tags"] = df["Tags"].fillna("").astype(str)

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

max_edges = st.sidebar.slider(
    "Max edges to render (performance)", min_value=200, max_value=20000, value=5000, step=200
)

directed = st.sidebar.toggle("Directed graph", value=True)

# Apply filters
filtered = df.copy()
if selected_types:
    filtered = filtered[filtered["Type"].astype(str).isin(selected_types)]
if tag_text.strip():
    filtered = filtered[filtered["Tags"].astype(str).str.contains(tag_text.strip(), case=False, na=False)]

if len(filtered) > max_edges:
    st.sidebar.info(f"Showing first {max_edges:,} edges out of {len(filtered):,}.")
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

        G.add_node(frm)
        G.add_node(to)
        G.add_edge(frm, to, Type=rel_type, Tags=tags)
    return G


G = build_graph(filtered, directed=directed)

# Stats
c1, c2, c3 = st.columns(3)
c1.metric("Nodes", f"{G.number_of_nodes():,}")
c2.metric("Edges", f"{G.number_of_edges():,}")
c3.metric("Filtered rows", f"{len(filtered):,}")

st.divider()

# ----------------------------
# Focus / neighborhood view
# ----------------------------
all_nodes = sorted(list(G.nodes()))
focus_node = st.selectbox("Focus node (optional)", options=["(none)"] + all_nodes, index=0)

use_ego = st.toggle("Show only neighborhood around focus (if selected)", value=False)
ego_hops = st.slider("Neighborhood hops", 1, 4, 2)

H = G
if focus_node != "(none)" and use_ego:
    if directed:
        nbrs = {focus_node}
        frontier = {focus_node}
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

# ----------------------------
# Measures + communities helpers
# ----------------------------
def compute_measures_and_communities(graph_for_analysis: nx.Graph):
    H_undirected = graph_for_analysis.to_undirected()

    if H_undirected.number_of_nodes() == 0:
        measures_df = pd.DataFrame(
            columns=["Name", "Degree", "Betweenness Centrality", "Closeness Centrality", "Community"]
        )
        return measures_df, [], {}

    deg_dict = dict(H_undirected.degree())

    if H_undirected.number_of_edges() > 0:
        between_dict = nx.betweenness_centrality(H_undirected, normalized=True)
        close_dict = nx.closeness_centrality(H_undirected)
    else:
        between_dict = {n: 0.0 for n in H_undirected.nodes()}
        close_dict = {n: 0.0 for n in H_undirected.nodes()}

    # Robust community detection with fallback (supports older NetworkX)
    if H_undirected.number_of_nodes() < 2 or H_undirected.number_of_edges() < 1:
        communities = [set(H_undirected.nodes())]
    else:
        try:
            from networkx.algorithms.community import greedy_modularity_communities
            communities = list(greedy_modularity_communities(H_undirected))
        except Exception:
            from networkx.algorithms.community import asyn_lpa_communities
            communities = list(asyn_lpa_communities(H_undirected, seed=42))

    community_map = {}
    for i, comm in enumerate(communities):
        for node in comm:
            community_map[node] = i

    measures_df = pd.DataFrame({
        "Name": list(H_undirected.nodes()),
        "Degree": [deg_dict.get(n, 0) for n in H_undirected.nodes()],
        "Betweenness Centrality": [between_dict.get(n, 0.0) for n in H_undirected.nodes()],
        "Closeness Centrality": [close_dict.get(n, 0.0) for n in H_undirected.nodes()],
        "Community": [community_map.get(n, -1) for n in H_undirected.nodes()],
    })

    measures_df["Betweenness Centrality"] = measures_df["Betweenness Centrality"].round(3)
    measures_df["Closeness Centrality"] = measures_df["Closeness Centrality"].round(3)

    measures_df = measures_df.sort_values(
        by=["Community", "Degree", "Name"], ascending=[True, False, True]
    ).reset_index(drop=True)

    return measures_df, communities, community_map


def make_community_colors(community_map: dict):
    # Soft, readable palette (repeat-safe)
    palette = [
        "#6BAED6", "#74C476", "#FD8D3C", "#9E9AC8", "#FDD0A2",
        "#A1D99B", "#FC9272", "#BDBDBD", "#9ECAE1", "#C7E9C0"
    ]
    node_color = {}
    for node, cid in community_map.items():
        node_color[node] = palette[cid % len(palette)]
    return node_color


# ----------------------------
# Node Inspector (Global vs Visible degree + neighbors)
# ----------------------------
st.subheader("Node Details (Inspector)")

G_und = G.to_undirected()
H_und = H.to_undirected()

global_degree = dict(G_und.degree())
visible_degree = dict(H_und.degree())

inspect_node = st.selectbox(
    "Pick a node to inspect (acts like click-to-view)",
    options=sorted(list(G.nodes())),
    index=0
)

d1, d2, d3 = st.columns(3)
d1.metric("Global Degree", int(global_degree.get(inspect_node, 0)))
d2.metric("Visible Degree", int(visible_degree.get(inspect_node, 0)))
d3.metric(
    "Visible Neighbors",
    int(len(list(H_und.neighbors(inspect_node))) if H_und.has_node(inspect_node) else 0)
)

st.markdown("**Connected Partners (Global neighbors)**")
global_neighbors = sorted(list(G_und.neighbors(inspect_node))) if G_und.has_node(inspect_node) else []
if not global_neighbors:
    st.write("No connections found for this node (in the current dataset).")
else:
    st.write(", ".join(global_neighbors))

st.divider()

# ----------------------------
# Measures + Communities (computed on VISIBLE graph H)
# ----------------------------
measures_df, communities, community_map = compute_measures_and_communities(H)
node_color_map = make_community_colors(community_map)

st.subheader("Node Measures")
st.dataframe(measures_df, use_container_width=True)

st.subheader("Degree Analysis")
if len(measures_df) > 0:
    max_deg = int(measures_df["Degree"].max())
    top_nodes = measures_df[measures_df["Degree"] == max_deg]["Name"].tolist()
    friends_word = "friend" if max_deg == 1 else "friends"
    st.write(f"Most connected (highest visible degree): {', '.join(top_nodes)} with **{max_deg}** {friends_word}.")
else:
    st.write("No nodes to analyze.")

st.subheader("Communities (Friendship Groups)")
if not communities:
    st.write("No communities detected.")
else:
    for i, comm in enumerate(communities, start=1):
        members = sorted(list(comm))
        st.markdown(f"**Group {i}:** {', '.join(members)}")

st.divider()

# ----------------------------
# Render with PyVis (expanded, no physics)
# ----------------------------
def nx_to_pyvis_html(graph: nx.Graph, node_color_map: dict[str, str] | None = None, focus: str | None = None) -> str:
    net = Network(
        height="900px",
        width="100%",
        bgcolor="#FFFFFF",
        font_color="#222222",
        directed=isinstance(graph, nx.DiGraph),
    )

    # No physics (stable)
    net.toggle_physics(False)

    # Expanded / readable layout options
    net.set_options("""
    var options = {
      "layout": {
        "improvedLayout": true
      },
      "nodes": {
        "shape": "dot",
        "scaling": {
          "min": 10,
          "max": 50
        },
        "font": {
          "size": 16
        }
      },
      "edges": {
        "smooth": false,
        "arrows": {
          "to": {"enabled": true, "scaleFactor": 0.7}
        },
        "font": {
          "size": 12,
          "align": "middle"
        }
      },
      "physics": {
        "enabled": false
      }
    }
    """)

    degrees = dict(graph.degree())
    max_deg = max(degrees.values()) if degrees else 1

    for n in graph.nodes():
        deg = degrees.get(n, 0)
        size = 12 + (38 * (deg / max_deg)) if max_deg else 12
        title = f"<b>{n}</b><br>Visible degree: {deg}"

        node_kwargs = dict(label=str(n), title=title, size=size)

        if node_color_map and n in node_color_map:
            node_kwargs["color"] = node_color_map[n]

        if focus and n == focus:
            node_kwargs["color"] = "#FFB000"
            node_kwargs["borderWidth"] = 4

        net.add_node(n, **node_kwargs)

    for u, v, attrs in graph.edges(data=True):
        etype = attrs.get("Type", "")
        tags = attrs.get("Tags", "")

        edge_title = "<br>".join([x for x in [
            f"<b>From:</b> {u}",
            f"<b>To:</b> {v}",
            f"<b>Type:</b> {etype}" if etype else "",
            f"<b>Tags:</b> {tags}" if tags else "",
        ] if x])

        label = str(etype) if str(etype).strip() else ""
        net.add_edge(u, v, title=edge_title, label=label)

    return net.generate_html()


html = nx_to_pyvis_html(H, node_color_map=node_color_map, focus=inspect_node)
components.html(html, height=950, scrolling=True)

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
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered edges (CSV)",
        data=csv_bytes,
        file_name="filtered_edges.csv",
        mime="text/csv",
    )

with colB:
    graphml_bytes = io.BytesIO()
    nx.write_graphml(H, graphml_bytes)
    st.download_button(
        "Download visible graph (GraphML)",
        data=graphml_bytes.getvalue(),
        file_name="network_visible.graphml",
        mime="application/xml",
    )
