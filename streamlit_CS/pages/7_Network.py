import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

st.title("Phishing Network Graph with Weighted Edges")

# Enhanced data with weights
phishing_data = [
    ("malicious1@example.com", "victim1@company.com", 5),
    ("malicious2@example.com", "victim2@company.com", 10),
    ("victim1@company.com", "victim2@company.com", 2),
    ("malicious1@example.com", "malicious2@example.com", 15),
    ("victim2@company.com", "hr@company.com", 1),
]

# Build a weighted directed graph
G = nx.DiGraph()
for sender, receiver, weight in phishing_data:
    G.add_edge(sender, receiver, weight=weight)

# Draw graph
fig, ax = plt.subplots(figsize=(10, 6))
pos = nx.spring_layout(G)
weights = nx.get_edge_attributes(G, 'weight')

nx.draw(
    G,
    pos,
    with_labels=True,
    node_size=3000,
    node_color='skyblue',
    edge_color='gray',
    font_size=10,
    font_weight='bold',
    ax=ax
)

nx.draw_networkx_edge_labels(G, pos, edge_labels=weights, ax=ax)

plt.title("Phishing Network with Weighted Edges")
plt.axis("off")

# Display in Streamlit
st.pyplot(fig)

import streamlit as st
from networkx.algorithms.community import greedy_modularity_communities

communities = greedy_modularity_communities(G)

st.subheader("Detected Communities")

for i, community in enumerate(communities, 1):
    with st.expander(f"Community {i}"):
        st.write(list(community))

st.subheader("Phishing Network with Malicious Node Highlighting")

# Compute positions BEFORE drawing
pos = nx.spring_layout(G)

# Color malicious nodes red, others green
colors = ['red' if 'malicious' in node else 'green' for node in G.nodes()]

# Draw the graph
fig, ax = plt.subplots(figsize=(10, 6))

nx.draw(
    G,
    pos,
    with_labels=True,
    node_size=3000,
    node_color=colors,
    edge_color='gray',
    font_size=10,
    font_weight='bold',
    ax=ax
)

plt.title("Phishing Network with Malicious Node Highlighting")
plt.axis("off")

# Display in Streamlit
st.pyplot(fig)
