import networkx as nx
import matplotlib.pyplot as plt

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
pos = nx.spring_layout(G)
weights = nx.get_edge_attributes(G, 'weight')
nx.draw(
    G, pos, with_labels=True, node_size=3000, node_color='skyblue',
    edge_color='gray', font_size=10, font_weight='bold'
)
nx.draw_networkx_edge_labels(G, pos, edge_labels=weights)
plt.title("Phishing Network with Weighted Edges")
plt.show()
