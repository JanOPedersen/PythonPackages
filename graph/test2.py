adj = { 
    0 : [1,2],
    1 : [3,2],
    2 : [4,5,3],
    3 : [5,4],
    4 : [5],
    5 : []
}

g = graph(adj)
s = 4
print("Following are longest distances from source vertex ",s)
g.longestPath(s)

# Print calculated longest distances
for i in sorted(g.getVertices()):
    print("i: ", str(i) + ", dist: " + str(g.dist[i]) + "\n")
