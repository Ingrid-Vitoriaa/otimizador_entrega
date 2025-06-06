from collections import deque
class Edge:
    def __init__(self, to, rev, capacity):
        self.to = to    #Nó destino
        self.rev = rev  # índice da aresta reversa
        self.capacity = capacity #Capacidade residual
        self.original_capacity = capacity

class MaxFlow:
    def __init__(self, n):
        self.size = n
        self.graph = [[] for _ in range(n)]  # Lista de adjacências
    
    def add_edge(self, fr, to, cap):
        forward = Edge(to, len(self.graph[to]), cap) #Aresta foward
        backward = Edge(fr, len(self.graph[fr]), 0) #Aresta residual
        self.graph[fr].append(forward)
        self.graph[to].append(backward)
    
    def bfs_level(self, s, t, level):
        """Busca em largura para encontrar caminhos aumentantes"""
        q = deque()
        level[:] = [-1]*self.size
        level[s] = 0
        q.append(s)
        
        while q:
            v = q.popleft()
            for edge in self.graph[v]:
                if edge.capacity > 0 and level[edge.to] < 0:
                    level[edge.to] = level[v] + 1
                    q.append(edge.to)
    
    def dfs_flow(self, v, t, upTo, iter_, level):
        if v == t:
            return upTo
        for i in range(iter_[v], len(self.graph[v])):
            edge = self.graph[v][i]
            if edge.capacity > 0 and level[v] < level[edge.to]:
                d = self.dfs_flow(edge.to, t, min(upTo, edge.capacity), iter_, level)
                if d > 0:
                    edge.capacity -= d
                    self.graph[edge.to][edge.rev].capacity += d
                    return d
            iter_[v] += 1
        return 0
    
    def max_flow(self, s, t):
        """Implementação completa do Edmonds-Karp"""
        flow = 0
        level = [-1]*self.size
        while True:
            self.bfs_level(s, t, level)
            if level[t] < 0:
                return flow
            iter_ = [0]*self.size
            while True:
                f = self.dfs_flow(s, t, float('inf'), iter_, level)
                if f == 0:
                    break
                flow += f
            level = [-1]*self.size

class ExtendedMaxFlow(MaxFlow):
    def __init__(self, n):
        super().__init__(n + 2)  # +2 para super fonte e super destino
        self.super_source = n #Fonte universal
        self.super_sink = n + 1 #Sorvedouro universal
    
    def add_multi_sources(self, sources, caps):
        for s, cap in zip(sources, caps):
            self.add_edge(self.super_source, s, cap)
    
    def add_multi_sinks(self, sinks, caps):
        for t, cap in zip(sinks, caps):
            self.add_edge(t, self.super_sink, cap)
    
    def multi_max_flow(self):
        return super().max_flow(self.super_source, self.super_sink)