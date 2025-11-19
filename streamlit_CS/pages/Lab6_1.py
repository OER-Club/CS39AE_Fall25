import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from networkx.algorithms.community import greedy_modularity_communities

# -----------------------------
# 1. Page config
# -----------------------------
st.set_page_config(page_title="Friendship Network Analysis", layout="wide")

st.title(" Friendship Network in a College Class")
st.write(
    """
This app visualizes a friendship network, computes basic network measures, 
detects communities, and highlights the most influential person based on a chosen centrality measure.
"""
)

# -----------------------------
# 2. Create the graph
# -----------------------------
nodes = [
    "Alice", "Bob", "Charlie", "Diana", "Eve",
    "Frank", "Grace", "Hannah", "Ian", "Jack"
]

edges = [
    ("Alice", "Bob"),
    ("Alice", "Charlie"),
    ("Bob", "Charlie"),
    ("Charlie", "Diana"),
    ("Diana", "Eve"),
    ("Bob", "Diana"),
    ("Frank", "Eve"),
    ("Eve", "Ian"),
    ("Diana", "Ian"),
    ("Ian", "Grace"),
    ("Grace", "Hannah"),
    ("Hannah", "Jack"),
    ("Grace", "Jack"),
    ("Charlie", "Frank"),
    ("Alice", "Eve"),
    ("Bob", "Jack"),
]

G = nx.Graph()
G.add_nodes_from(nodes)
G.add_edges_from(edges)

# Layout for node positions
pos = nx.spring_layout(G, seed=42)

# -----------------------------
# 3. Compute measures
# -----------------------------
degree_dict = dict(G.degree())
betweenness = nx.betweenness_centrality(G, normalized=True)
closeness = nx.closeness_centrality(G)

# Community detection
communities = list(greedy_modularity_communities(G))
community_index = {}
for i, community in enumerate(communities):
    for node in community:
        community_index[node] = i

# Put measures into a DataFrame
data = []
for node in G.nodes():
    data.append(
        {
            "Name": node,
            "Degree": degree_dict[node],
            "Betweenness Centrality": betweenness[node],
            "Closeness Centrality": closeness[node],
            "Community": community_index[node],
        }
    )

df_measures = pd.DataFrame(data).sort_values("Name").reset_index(drop=True)

# -----------------------------
# 4. Sidebar controls
# -----------------------------
st.sidebar.header("Settings")

centrality_choice = st.sidebar.radio(
    "Choose centrality measure for 'influence':",
    ("Degree", "Betweenness Centrality", "Closeness Centrality"),
)

# Determine most influential node based on choice
if centrality_choice == "Degree":
    influential_person = max(degree_dict, key=degree_dict.get)
    influence_values = degree_dict
elif centrality_choice == "Betweenness Centrality":
    influential_person = max(betweenness, key=betweenness.get)
    influence_values = betweenness
else:
    influential_person = max(closeness, key=closeness.get)
    influence_values = closeness

st.sidebar.markdown(
    f"**Most influential (by {centrality_choice}):** `{influential_person}`"
)

# -----------------------------
# 5. Color nodes by community and highlight influential person
# -----------------------------
base_colors = ["lightblue", "lightgreen", "lightpink", "lightyellow", "orange", "violet"]

node_colors = []
for node in G.nodes():
    color = base_colors[community_index[node] % len(base_colors)]
    if node == influential_person:
        color = "red"  # highlight influential person
    node_colors.append(color)

# -----------------------------
# 6. Main layout: graph + table
# -----------------------------
col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("Network Visualization")

    fig, ax = plt.subplots(figsize=(7, 6))
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=1800,
        node_color=node_colors,
        edge_color="gray",
        font_weight="bold",
        ax=ax,
    )
    ax.set_title("Friendship Network with Communities and Influential Person Highlighted")
    ax.axis("off")
    st.pyplot(fig)

    st.caption(
        f"Red node = most influential person (based on **{centrality_choice}**). "
        "Other colors indicate different friendship communities."
    )

with col2:
    st.subheader("Node Measures")

    st.dataframe(df_measures.style.format(
        {
            "Betweenness Centrality": "{:.3f}",
            "Closeness Centrality": "{:.3f}",
        }
    ))

    st.markdown("### Degree Analysis")
    max_deg = degree_dict[influential_person] if centrality_choice == "Degree" else max(degree_dict.values())
    most_connected = [n for n, d in degree_dict.items() if d == max_deg]
    st.write(f"**Most connected (highest degree):** {', '.join(most_connected)} with `{max_deg}` friends.")

    st.markdown("### Communities (Friendship Groups)")
    for i, community in enumerate(communities, start=1):
        st.write(f"**Group {i}:** {', '.join(sorted(list(community)))}")

# -----------------------------
# 7. Explanation section (optional for students)
# -----------------------------
st.markdown("---")
st.markdown("### How to Use This App (for Students)")

st.markdown(
    """
1. **Explore the graph**: Each node is a person; each line is a friendship.
2. **Change the 'influence' measure** in the sidebar to see how the highlighted person changes.
3. **Compare measures in the table**:
   - Degree = number of direct friends  
   - Betweenness = how often a person sits on shortest paths between others  
   - Closeness = how close a person is, on average, to everyone else  
4. **Communities** show friendship groups detected automatically with a community detection algorithm.
"""
)
