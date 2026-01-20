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
    "Excel edge list (From, To, optional Type/Tags) → interactive network + node measures + inspector. "
    "This version colors ONLY the focus node and 'bridge' nodes (boundary connectors)."
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

    df = df[(df["From"] != "") & (df["To"] != "")]
    return df


def load_from_repo_path_or_upload() -> pd.DataFrame:
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
# Sidebar filters / display controls
# ----------------------------
st.sidebar.header("Filters")

type_options = sorted([t for t in df["Type"].dropna().astype(str).unique() if t.strip() != ""])
selected_types = st.sidebar.multiselect("Type", options=type_options, default=type_options)

tag_text = st.sidebar.text_input("Filter Tags contains (substring)", value="")

max_edges = st.sidebar.slider(
    "Max edges to render (performance)", min_value=200, max_value=20000, value=5000, step=200
)

directed = st.sidebar.toggle("Directed graph", value=True)

st.sidebar.header("Edge label & color")
label_mode = st.sidebar.radio(
    "Edge label style",
    options=["None", "Short (first 3 letters)", "Full Type"],
    index=1,
)
color_edges_by_type = st.sidebar.toggle("Color edges by Type", value=True)

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
default_focus = 0 if len(all_nodes) > 0 else None

focus_node = st.selectbox("Focus node", options=all_nodes, index=default_focus if default_focus is not None else 0)

use_ego = st.toggle("Show only neighborhood around focus", value=True)
ego_hops = st.slider("Neighborhood hops", 1, 4, 2)

H = G
if use_ego and focus_node:
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
# Bridge nodes (boundary connectors)
# Definition used here:
#   Nodes inside the visible graph H that have at least one neighbor outside H in the FULL graph G (undirected view).
# These are good "possible connections to next level" from the current view.
# ----------------------------
G_und = G.to_undirected()
H_und = H.to_undirected()

bridge_nodes = set()
if H_und.number_of_nodes() > 0:
    H_nodes = set(H_und.nodes())
    for n in H_nodes:
        if not G_und.has_node(n):
            continue
        for nbr in G_und.neighbors(n):
            if nbr not in H_nodes:
                bridge_nodes.add(n)
                break

# Make sure focus isn't also treated as bridge color (focus wins)
if focus_node in bridge_nodes:
    bridge_nodes.remove(focus_node)

# ----------------------------
# Measures (Global vs Visible Degree) + Connected Partners list
# ----------------------------
st.subheader("Node Details (Inspector)")

global_degree = dict(G_und.degree())
visible_degree = dict(H_und.degree())

d1, d2, d3, d4 = st.columns(4)
d1.metric("Global Degree", int(global_degree.get(focus_node, 0)))
d2.metric("Visible Degree", int(visible_degree.get(focus_node, 0)))
d3.metric("Bridge Nodes (count)", int(len(bridge_nodes)))
d4.metric("Visible Nodes", int(H_und.number_of_nodes()))

st.markdown("**Connected Partners (Global neighbors of focus)**")
global_neighbors = sorted(list(G_und.neighbors(focus_node))) if G_und.has_node(focus_node) else []
st.write(", ".join(global_neighbors) if global_neighbors else "No connections found for this node (in the current dataset).")

st.markdown("**Bridge Nodes (boundary connectors in current view)**")
st.write(", ".join(sorted(list(bridge_nodes))) if bridge_nodes else "No bridge/boundary nodes detected for this view.")

st.divider()

# ----------------------------
# Node Measures table (computed on visible graph H)
# ----------------------------
def compute_measures(graph_for_analysis: nx.Graph) -> pd.DataFrame:
    U = graph_for_analysis.to_undirected()

    if U.number_of_nodes() == 0:
        return pd.DataFrame(columns=["Name", "Degree", "Betweenness", "Closeness"])

    deg = dict(U.degree())
    if U.number_of_edges() > 0:
        bet = nx.betweenness_centrality(U, normalized=True)
        clo = nx.closeness_centrality(U)
    else:
        bet = {n: 0.0 for n in U.nodes()}
        clo = {n: 0.0 for n in U.nodes()}

    out = pd.DataFrame({
        "Name": list(U.nodes()),
        "Degree": [deg.get(n, 0) for n in U.nodes()],
        "Betweenness": [bet.get(n, 0.0) for n in U.nodes()],
        "Closeness": [clo.get(n, 0.0) for n in U.nodes()],
    })

    out["Betweenness"] = out["Betweenness"].round(3)
    out["Closeness"] = out["Closeness"].round(3)
    out = out.sort_values(by=["Degree", "Betweenness", "Name"], ascending=[False, False, True]).reset_index(drop=True)
    return out


st.subheader("Node Measures (Visible Graph)")
measures_df = compute_measures(H)
st.dataframe(measures_df, use_container_width=True)

st.subheader("Degree Analysis (Visible Graph)")
if len(measures_df) > 0:
    max_deg = int(measures_df["Degree"].max())
    top_nodes = measures_df[measures_df["Degree"] == max_deg]["Name"].tolist()
    st.write(f"Most connected (highest visible degree): {', '.join(top_nodes)} with **{max_deg}** connections.")
else:
    st.write("No nodes to analyze.")

st.divider()

# ----------------------------
# PyVis rendering (expanded, no physics)
# Color rules:
#   - Focus node: Gold
#   - Bridge nodes: Red-ish
#   - All others: Light gray/blue
# Edge labels:
#   - None, Short (first 3 letters), or Full
# Edge colors by Type (optional)
# ----------------------------
def shorten_label(t: str) -> str:
    t = (t or "").strip()
    if not t:
        return ""
    return t[:3].upper()


def build_type_color_map(types: list[str]) -> dict[str, str]:
    palette = [
        "#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd", "#d62728",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
    ]
    out = {}
    for i, t in enumerate(sorted(set([x.strip() for x in types if x.strip()]))):
        out[t] = palette[i % len(palette)]
    return out


type_color_map = build_type_color_map(filtered["Type"].astype(str).tolist()) if color_edges_by_type else {}


def nx_to_pyvis_html(graph: nx.Graph) -> str:
    net = Network(
        height="950px",   # more expanded view
        width="100%",
        bgcolor="#FFFFFF",
        font_color="#222222",
        directed=isinstance(graph, nx.DiGraph),
    )

    # No physics (stable)
    net.toggle_physics(False)

    # Expanded / readable settings (no motion)
    net.set_options("""
    var options = {
      "layout": {
        "improvedLayout": true
      },
      "nodes": {
        "shape": "dot",
        "scaling": { "min": 10, "max": 55 },
        "font": { "size": 16 }
      },
      "edges": {
        "smooth": false,
        "arrows": {
          "to": {"enabled": true, "scaleFactor": 0.65}
        },
        "font": { "size": 11, "align": "middle" }
      },
      "physics": { "enabled": false }
    }
    """)

    degrees = dict(graph.degree())
    max_deg = max(degrees.values()) if degrees else 1

    # Node colors: only focus + bridge nodes
    for n in graph.nodes():
        deg = degrees.get(n, 0)
        size = 12 + (40 * (deg / max_deg)) if max_deg else 12

        # default color
        color = "#DCE7F2"  # light blue-gray

        if n == focus_node:
            color = "#FFB000"  # focus
        elif n in bridge_nodes:
            color = "#E45756"  # bridge/boundary connector

        title = f"<b>{n}</b><br>Visible degree: {deg}"
        net.add_node(n, label=str(n), title=title, size=size, color=color)

    # Edges
    for u, v, attrs in graph.edges(data=True):
        etype = str(attrs.get("Type", "")).strip()
        tags = str(attrs.get("Tags", "")).strip()

        if label_mode == "None":
            label = ""
        elif label_mode == "Full Type":
            label = etype
        else:
            label = shorten_label(etype)

        edge_title = "<br>".join([x for x in [
            f"<b>From:</b> {u}",
            f"<b>To:</b> {v}",
            f"<b>Type:</b> {etype}" if etype else "",
            f"<b>Tags:</b> {tags}" if tags else "",
        ] if x])

        edge_kwargs = dict(title=edge_title)
        if label:
            edge_kwargs["label"] = label

        if color_edges_by_type and etype in type_color_map:
            edge_kwargs["color"] = type_color_map[etype]

        net.add_edge(u, v, **edge_kwargs)

    return net.generate_html()


st.subheader("Network Graph")
html = nx_to_pyvis_html(H)
components.html(html, height=980, scrolling=True)

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
