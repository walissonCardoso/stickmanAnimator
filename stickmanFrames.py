import cv2
import copy
import numpy as np

# Node is a 2D-position in the screen
class Node:
    # Constructor
    def __init__(self, x = 0, y = 0):
        self.setPos(x, y)
        self.isSelected = False
    
    # Reset position of the node
    def setPos(self, x, y):
        self.x, self.y = int(x), int(y)
    
    # Euclidian Distance to other node
    def distanceTo(self, other):
        squared = (self.x - other.x) ** 2 + (self.y - other.y) ** 2
        return np.sqrt(squared)

# Frame is a collection of nodes connected by edges
class Frame:
    def __init__(self):
        self.nodes = []
        self.edges = []
    
    def __len__(self):
        return len(self.nodes)
    
    # Just append one node at the end
    def insertNode(self, x, y):
        self.nodes.append(Node(x, y))
    
    # If we remove a node, we have to delete this node and update edge list
    def removeNode(self, nodeIndex):
        # if index is invalid, return
        if nodeIndex < 0 or nodeIndex >= len(self.nodes):
            return
        # if not, delete
        del self.nodes[nodeIndex]
        
        # Check edges
        for i in range(len(self.edges)-1, -1, -1):
            # If edge contain node, delete
            edge = self.edges[i]
            if edge[0] == nodeIndex or edge[1] == nodeIndex:
                del self.edges[i]
            else:
                # If not, reduce bigger indexes (one edge was deleted)
                if edge[0] > nodeIndex:
                    edge[0] -= 1
                if edge[1] > nodeIndex:
                    edge[1] -= 1
    
    # Edge is a connection between two nodes.
    def insertEdge(self, index1, index2, edgeType = 'line'):
        if index1 < 0 or index1 >= len(self.nodes) or\
            index2 < 0 or index2 >= len(self.nodes):
                return
        self.edges.append([index1, index2, edgeType])
    
    # Returns a copy of a node addressed by index
    def getNode(self, index):
        if index < 0 or index >= len(self.nodes):
            return None
        return copy.deepcopy(self.nodes[index])
    
    # Selection threshold is the minimum distance of a click so the node is
    # selected
    def selectNode(self, x, y, selectionThreshold = 24):
        ref = Node(x, y)
        minDist = np.inf
        selectedIndex = None
        
        # Go over all nodes
        for i in range(len(self.nodes)):
            # Unselect all nodes
            self.nodes[i].isSelected = False
            # check distance
            distance = ref.distanceTo(self.nodes[i])
            # See if this is the smallest distance found so far
            if distance < minDist:
                minDist = distance
                selectedIndex = i
        
        # If minimum distance is smaller than threshold, and there's any node,
        # select it
        if minDist <= selectionThreshold and selectedIndex is not None:
            self.nodes[selectedIndex].isSelected = True

    
    # Edit the position of the selected node
    def editSelectedPosition(self, x, y):
        # Go over all nodes
        for node in self.nodes:
            # If node is selected, edit and return
            if node.isSelected:
                node.setPos(x, y)
                break

class StickmanFrames:
    def __init__(self, imgWidth = 800, imgHeight = 600):
        # Garbage frame receives all thrash from index error
        self.garbageFrame = Frame()
        self.frames = []
        self.newByCopy = True
        
        # Size of the screen
        self.imgWidth  = imgWidth
        self.imgHeight = imgHeight
    
    # number of frames
    def __len__(self):
        return len(self.frames)
    
    # Insert a node on a frame
    def insertNode(self, frameIndex, x, y):
        # If frame number is bigger than number of frames, make list grow to fit
        if frameIndex >= len(self.frames):
            for i in range(frameIndex - len(self.frames) + 1):
                self.frames.append(Frame())
        
        # Insert node on frame and return number of nodes in this frame
        self.frames[frameIndex].insertNode(x, y)
        return len(self.frames[frameIndex])-1
    
    # Edit position of node in nodeIndex and in frame frameNumber
    def editNode(self, frameIndex, nodeIndex, x, y):
        self.getFrame(frameIndex).nodes[nodeIndex].setPos(x, y)
        
    def removeNode(self, frameIndex, nodeIndex):
        self.getFrame(frameIndex).removeNode(nodeIndex)
    
    # Insert edge connecting nodes of indexes id1 and id2
    def insertEdge(self, frameIndex, id1, id2, edgeType = 'line'):
        self.getFrame(frameIndex).insertEdge(id1, id2, edgeType)
    
    # Substitute a frame for an empty frame
    def clearFrame(self, frameIndex):
        if frameIndex >= len(self.frames):
            return
        self.frames[frameIndex] = Frame()
    
    # Select node. The selected node is identified by isSelected == True
    def selectNode(self, frameIndex, x, y):
        self.getFrame(frameIndex).selectNode(x, y)
    
    # Unselect all nodes os this frame
    def unselectNodes(self, frameIndex):
        for node in self.getFrame(frameIndex).nodes:
            node.isSelected = False
    
    # Return index of the selected node in this frame
    def selectedNode(self, frameIndex):
        for i, node in enumerate(self.getFrame(frameIndex).nodes):
            if node.isSelected:
                return i
        return None
    
    # Draw our graph above an image
    def drawFigure(self, frameIndex, background, lineThickness = 10,
                 lineColor = (0, 255, 0), nodeColor = (0, 255, 0),
                 selectedColor = (255, 0, 0), drawNodes = True):
        
        # Get frame
        frame = self.getFrame(frameIndex)
        
        # For all edges in the frame
        for id1, id2, edgeType in frame.edges:
            # Get nodes 
            node1 = frame.getNode(id1)
            node2 = frame.getNode(id2)
            
            # Draw a line of a circle. Depending on line type
            if edgeType == 'line':
                cv2.line(background, (node1.x, node1.y), (node2.x, node2.y),
                         lineColor, thickness = lineThickness)
            elif edgeType == 'circle':
                center = ((node1.x + node2.x) // 2, (node1.y + node2.y) // 2)
                radius = int(np.sqrt((node1.x-node2.x)**2 + (node1.y-node2.y)**2) / 2)
                cv2.circle(background, center, radius, lineColor, -1)
        
        # If draw nodes is True, print nodes as smaller circles
        if drawNodes:
            for node in frame.nodes:
                # Color changes if node is selected
                color = selectedColor if node.isSelected else nodeColor
                cv2.circle(background, (node.x, node.y), radius = lineThickness,
                           color = color, thickness = -1)
    
    # This function is used internally. If a invalid index is requested, garbage
    # frame is returned
    def getFrame(self, frameIndex):
        if frameIndex < len(self.frames):
            return self.frames[frameIndex]
        else:
            return self.garbageFrame
    
    # Search the last non empty frame to clone
    def repeatByCopy(self, frameIndex):
        # If there are no frames, return
        if len(self.frames) == 0:
            return
        # If frame is not empty, return
        if len(self.getFrame(frameIndex)) > 0:
            return
        
        source = None
        # We gonna search backwards for a non empty frame and stop
        limit = min(frameIndex, len(self.frames))
        for i in range(limit-1, -1, -1):
            if len(self.frames[i]) > 0:
                source = i 
                break
        
        # Append new frame by copy
        if source is not None:
            for node in self.frames[source].nodes:
                self.insertNode(frameIndex, node.x, node.y)
            for edge in self.frames[source].edges:
                self.insertEdge(frameIndex, edge[0], edge[1], edge[2])
    
    # Interpolate is a function to fill all gaps in animation with intermediate
    # steps. The filling is linear
    def interpolate(self):
        emptyIntervals = []
        begin, end = 0, 0
        for i in range(len(self.frames)):
            # Found a non-empty frame
            if len(self.frames[i]) > 0:
                end = i
            
            # Here if we passed for a series of empty frames, end-begin > 1, so
            # we save the interval
            if begin is not None and end is not None and end - begin > 1:
                emptyIntervals.append([begin, end])
                
            # Register begin for one more non-empty thing
            begin = end
        
        # For all empty intervals found...
        for interval in emptyIntervals:
            # We will interpolate only the common nodes
            nNodes = min(len(self.getFrame(interval[0])),
                         len(self.getFrame(interval[1])))
            
            # Let's copy all nodes in the frames on the interval
            for i in range(nNodes):
                # Get the extreme nodes
                node1 = self.getFrame(interval[0]).getNode(i)
                node2 = self.getFrame(interval[1]).getNode(i)
                
                # Calculate the difference between their position
                diffX = node2.x - node1.x
                diffY = node2.y - node1.y
                step = 1 / (interval[1]-interval[0])
                
                # Fill with new nodes in intermediate positions
                for j in range(1, interval[1]-interval[0]):
                    frameIndex = interval[0]+j
                    x = node1.x + diffX * step * j
                    y = node1.y + diffY * step * j
                    self.insertNode(frameIndex, x, y)
            
            # Now copy edges from the node in the beggining of the interval
            for edge in self.getFrame(interval[0]).edges:
                for j in range(1, interval[1]-interval[0]):
                    frameIndex = interval[0]+j
                    
                    # Let's ignore edges that contain nodes we did not include
                    if edge[0] < len(self.getFrame(frameIndex)) and\
                       edge[1] < len(self.getFrame(frameIndex)):
                        self.insertEdge(frameIndex, edge[0], edge[1], edge[2])
                
    
    # Export animation as a series of .png images
    def exportAnimation(self, folderPath, lineThickness = 10, lineColor = (1, 1, 1)):
        # Background is fully transparent
        backGround = np.zeros([self.imgHeight, self.imgWidth, 4], dtype=np.uint8)
        # Avoid confusion with background
        if lineColor == (0,0,0):
            lineColor = (1,1,1)
        
        # For all frames
        exportedImages = 0
        for i, frame in enumerate(self.frames):
            # If frame is empty, do not save
            if len(frame.nodes) == 0:
                continue
            
            # Copy default background
            image = np.copy(backGround)
            # Draw above it.
            self.drawFigure(i, image, drawNodes=False, lineThickness=lineThickness, lineColor=lineColor)
            # Figure color is almost full black, but it is not. So we can
            # differentiate from background and apply transparency only on the
            # right places.
            mask = image[:, :, :3].sum(axis=2) > 0
            image[mask, 3] = 255
            
            # Save figure
            fileName = folderPath + '/' + str(exportedImages) + '.png'
            cv2.imwrite(fileName, image)
            exportedImages += 1
    
    # Print frames, nodes, and edges info
    def describe(self, start = 0, end = -1):
        for i, frame in enumerate(self.frames):
            print('Frame', i, '. Nodes:', len(frame.nodes))
            for j, edge in enumerate(frame.edges):
                print('   Edge', j, '. (', edge[0], ', ', edge[1], ')', '-->', edge[2])
            

# Test this file by executing it.
# Some frames whould be generated in this folder
if __name__ == '__main__':
    st = StickmanFrames()
    
    nodes = (((100, 100), (300, 200), (600, 300), (500,  50)),
             ((400, 350), (450, 410), (420, 150), (700, 120)))
    
    for i, frameIndex in enumerate([0, 3]):
        for node in nodes[i]:
            st.insertNode(frameIndex, node[0], node[1])
        
        st.insertEdge(frameIndex, 0, 1, 'circle')
        st.insertEdge(frameIndex, 1, 2, 'line')
        st.insertEdge(frameIndex, 1, 3, 'line')
    
    st.repeatByCopy(6)
    st.removeNode(3, 0)
    st.describe()
    
    print('')
    
    st.interpolate()
    st.describe()
    
    #folderPath = '.'
    #st.exportAnimation(folderPath)