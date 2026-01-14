class graph:
    '''Using https://www.tutorialspoint.com/python_data_structure/python_graphs.htm we represent a graph as a dictionary and 
    transform model_graph.my_edge_list into such a dictionary
    '''

    def __init__(self,gdict=None,*,glist=None):
        '''We construct by either supplying the dictionary or a list of edges'''
        if gdict is None and glist is None:
            self.gdict = {}
            self.rgdict = {}
        elif gdict is not None:
            self.gdict = {}
            self.rgdict = {}
            for key,v in gdict.items():
                for n in v:
                    edge = (key,n)
                    self.AddEdge(edge)
        elif glist is not None:
            self.gdict = {}
            self.rgdict = {}
            for edge in glist:
                self.AddEdge((edge[0],edge[1]))
        
    def edges(self):
        return self.findedges()
    
    def getVertices(self):
        return set(self.gdict.keys())
    
    def addVertex(self, vrtx):
        '''Add the vertex as a key'''
        if not vrtx in self.gdict:
            self.gdict[vrtx] = []
            self.rgdict[vrtx] = []
            
    def AddEdge(self, edge):
        '''Add the new edge. If vrtx2 is not represented already as 
        a vertex in gdict is is also added there. This is to assure
        that applications that need all vertices to be in gdict will
        work'''
        (vrtx1, vrtx2) = edge
        self.addVertex(vrtx2)
        self.addVertex(vrtx1)
        
        if vrtx1 in self.gdict:
            self.gdict[vrtx1].append(vrtx2)
        else:
            self.gdict[vrtx1] = [vrtx2]      
            
        if vrtx2 in self.rgdict:
            self.rgdict[vrtx2].append(vrtx1)
        else:
            self.rgdict[vrtx2] = [vrtx1]   
            
    def findedges(self):
        '''List the edge names'''
        edgename = []
        for vrtx in self.gdict:
            for nxtvrtx in self.gdict[vrtx]:
                if (nxtvrtx, vrtx) not in edgename:
                    edgename.append((vrtx, nxtvrtx))
        return edgename
    
    def findRootVertices(self):            
        vertices = []
        for vrtx in self.rgdict:
            if not self.rgdict[vrtx]:
                vertices.append(vrtx)          
                    
        return list(vertices)
    
    def findLeafVertices(self):
        vertices = []
        for vrtx in self.gdict:
            if not self.gdict[vrtx]:
                vertices.append(vrtx)
                
        return vertices

    def traverse_graph(self):
        '''Do a depth first traversal, producing an enumeration of the nodes. The graph is not a tree
        so we have to keep track of visited nodes.
        '''
        self.visited = {}
        for vrtx in self.gdict:
            self.visited[vrtx] = False
            
        root_vertices = self.findRootVertices() 
        if len(root_vertices) == 1:
            root_vertex = root_vertices[0]
            self.node_enumeration = []
            self.depth_first_traversal(root_vertex)
            return self.node_enumeration
        else:
            return
        
    def depth_first_traversal(self,vrtx):
        self.node_enumeration.append(vrtx)
        if vrtx in self.gdict:
            for nxtvrtx in self.gdict[vrtx]:
                if nxtvrtx in self.visited and not self.visited[nxtvrtx]:
                    self.visited[nxtvrtx] = True
                    self.depth_first_traversal(nxtvrtx)
                 
    def depth_first_traversal2(self,vrtx):
        print(vrtx)
        if vrtx in self.gdict:
            for nxtvrtx in self.gdict[vrtx]:
                if nxtvrtx in self.visited and not self.visited[nxtvrtx]:
                    self.visited[nxtvrtx] = True
                    self.depth_first_traversal2(nxtvrtx)
                
    def topologicalSortUtil(self,vrtx):
        '''A recursive function used by longestPath. See below
        link for details
        https:www.geeksforgeeks.org/topological-sorting/
        '''
        self.visited[vrtx] = True

        # Recur for all the vertices adjacent to this vertex
        for i in self.gdict[vrtx]:
            if (not self.visited[i]):
                self.topologicalSortUtil(i)

        # Push current vertex to stack which stores topological
        # sort
        self.Stack.append(vrtx)
        
    def longestDistances(self,vrtx):
        '''The function to find longest distances from a given vertex.
        It uses recursive topologicalSortUtil() to get topological
        sorting.
        '''
        self.Stack= []
        self.visited = {i:False for i in self.getVertices()}
        self.dist = {i:-10**9 for i in self.getVertices()}

        # Call the recursive helper function to store Topological
        # Sort starting from all vertices one by one
        for i in self.getVertices():
            if (self.visited[i] == False):
                self.topologicalSortUtil(i)

        # Initialize distances to all vertices as infinite and
        # distance to source as 0
        self.dist[vrtx] = 0

        # Process vertices in topological order
        while (len(self.Stack) > 0):

            # Get the next vertex from topological order
            u = self.Stack[-1]
            del self.Stack[-1]

            # Update distances of all adjacent vertices
            if (self.dist[u] != 10**9):
                for i in self.gdict[u]:
                    if (self.dist[i] < self.dist[u] + 1):
                        self.dist[i] = self.dist[u] + 1
                        
    def longestPath(self,vrtx):
        '''longestPath(...) only found the path lengths, here we supply
        the actual path, presumes that we have run longestDistances(...) before'''
        self.v_list = [vrtx]
        while (len(self.rgdict[vrtx]) > 0 and vrtx != -1):
            (l,v) = (-10**9, -1)
            for i in self.rgdict[vrtx]:
                if l < self.dist[i]:
                    (l,v) = (self.dist[i],i)
            vrtx = v
            self.v_list.append(vrtx)

        self.v_list.reverse()
        
    def prune_nodes(self,visible_nodes: set) -> None:
        '''Prune the non-visible nodes by removing
        all references to it in the relevant neighbour lists
        and finally removing the node itself from the Dictionary'''
        invisible_nodes = self.getVertices().difference(visible_nodes)
        invisible_nodes_left = set(invisible_nodes)
        
        for node in invisible_nodes:
            if (len(self.rgdict[node]) == 1):
                parent = self.rgdict[node][0]
                self.gdict[parent].remove(node)
                self.gdict[parent] = self.gdict[parent] + self.gdict[node]
                for child in self.gdict[node]:
                    self.rgdict[child].remove(node)
                    self.rgdict[child].append(parent)

                del self.gdict[node]
                del self.rgdict[node]
                invisible_nodes_left.remove(node)
        
        for node in invisible_nodes_left:        
            if (len(self.gdict[node]) == 1):
                child = self.gdict[node][0]
                self.rgdict[child].remove(node)
                self.rgdict[child] = self.rgdict[child] + self.rgdict[node]
                for parent in self.rgdict[node]:
                    self.gdict[parent].remove(node)
                    self.gdict[parent].append(child)

                del self.gdict[node]
                del self.rgdict[node]
        
    def find_skip_connections(self) -> list:
        '''Now, we would like to find all skip connections, which are paths that start and end on the main path. 
        Each skip connection has a start and end node and can contain internal visible nodes, which 
        are not drawn due to presenting a readable graph. For now we assume that the skip connection paths 
        are "simple", that is, each is a "line" graph, with no diverging branches inside 
        (each node has exactly one child and one parent).

        So the algorithm for finding skip connections is to:

        1. Traverse the main path
        2. For each node with more than one child node, traverse its path until we get to the main path again.
        3. Record the (startnode, endnode) pairs
        '''
        skip_connections = []
        main_path = self.v_list
        main_path_set = set(main_path)
        for index, node in enumerate(main_path):
            if (len(self.gdict[node]) > 1):
                child_nodes = list(self.gdict[node])
                begin_node = node
                for child in self.gdict[node]:
                    if child != main_path[index + 1]:
                        if child in main_path_set:
                            skip_connections.append((begin_node,child))
                        else:
                            print("traverse the path starting at child")
                                
        return skip_connections
        
