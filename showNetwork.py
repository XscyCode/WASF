from xml.dom.minicompat import NodeList
import networkx as nx
import matplotlib.pyplot as plt
import configure

G = nx.Graph()

pos = {0: (0, 0), 1: (0, 2), 2: (0, 4), 3: (0, 6), 4: (0, 8),
 5: (0, 10),6: (0, 12),7: (0, 14),8: (0, 16),9:(0, 18),
 19:(2, 0),18: (2, 2), 17: (2, 4), 16: (2, 6), 15: (2, 8),
 14: (2, 10),13: (2, 12),12: (2, 14),11: (2, 16),10:(2, 18),
 20: (4, 0), 21: (4, 2), 22: (4, 4), 23: (4, 6), 24:(4, 8),
 25: (4, 10),26: (4, 12),27: (4, 14),28: (4, 16),29:(4, 18),
 39: (6, 0), 38: (6, 2), 37: (6, 4), 36: (6, 6), 35:(6, 8),
 34: (6, 10),33: (6, 12),32: (6, 14),31: (6, 16),30:(6, 18),
 40: (8, 0), 41: (8, 2), 42: (8, 4), 43: (8, 6), 44:(8, 8),
 45: (8, 10),46: (8, 12),47: (8, 14),48: (8, 16),49:(8, 18)}
edges = []

f = open('structure.txt')
lines = f.readlines()
startLine = 0
for i in range(len(lines)):
    if lines[i].find('************') != -1:
        startLine = i
print(startLine)
n2 = []
n4 = []
n6 = []
n8 = []
n5 = []
for i in range(startLine, len(lines), 1):
    if lines[i].find('edge') != -1:
        params = lines[i].split(':')
        G.add_edge(int(params[2]), int(params[1]), weight = float(params[3]))
        n5.append(int(params[1]))
    if lines[i].find('selfWeight') != -1:       
        params = lines[i].split(':')
        G.add_node(int(params[1]))
        if float(params[2]) == 0.2:
            n2.append(int(params[1]))
        if float(params[2]) == 0.4:
            n4.append(int(params[1]))
        if float(params[2]) == 0.6:
            n6.append(int(params[1]))
        if float(params[2]) == 0.8:
            n8.append(int(params[1]))

e2 = [(u, v) for (u, v, d) in G.edges(data=True) if d['weight'] == 0.2]
e4 = [(u, v) for (u, v, d) in G.edges(data=True) if d['weight'] == 0.4]
e6 = [(u, v) for (u, v, d) in G.edges(data=True) if d['weight'] == 0.6]
e8 = [(u, v) for (u, v, d) in G.edges(data=True) if d['weight'] == 0.8]


# pos = nx.spring_layout(G)


nx.draw_networkx_nodes(G, pos, node_size=700)
nx.draw_networkx_nodes(G, pos, nodelist = n5, node_color = 'g', node_size=700)
# nx.draw_networkx_nodes(G, pos, nodelist = n4, node_color = 'g', node_size=700)
# nx.draw_networkx_nodes(G, pos, nodelist = n6, node_color = 'r', node_size=700)
# nx.draw_networkx_nodes(G, pos, nodelist = n8, node_color = 'black', node_size=700)


for edge in G.edges:
   plt.annotate("",xy=pos[edge[0]], xycoords='data',
                xytext=pos[edge[1]], textcoords='data',
                arrowprops=dict(arrowstyle="->", color="r",
                                shrinkA=5, shrinkB=5,lw = 4,
                                patchA=None, patchB=None,
                                connectionstyle="arc3,rad=-0.3",
                                ),
                )
# # edges
# # nx.draw_networkx_edges(G, pos, edgelist=e2, width=6, edge_color='blue')
# # nx.draw_networkx_edges(G, pos, edgelist=e4, width=6, edge_color='g')
# # nx.draw_networkx_edges(G, pos, edgelist=e6, width=6, edge_color='r')
# # nx.draw_networkx_edges(G, pos, edgelist=e8, width=6, edge_color='black')

# labels
nx.draw_networkx_labels(G, pos, font_size=20, font_family='sans-serif')

plt.axis('off')
plt.show()