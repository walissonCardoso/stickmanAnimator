import pickle
import numpy as np
import tkinter as tk

from PIL import Image
from PIL import ImageTk

from videoProcessing import VideoProcessing, imagesToVideo
from stickmanFrames import StickmanFrames
from configWindow import ConfigWindow

from tkinter.filedialog import askopenfilename as askopenfilename
from tkinter.filedialog import askopenfilenames as askopenfilenames
from tkinter.filedialog import asksaveasfilename as asksaveasfilename
from tkinter.filedialog import askdirectory as askdirectory

# Constants to control application's behaviour
global frameSize, stickyMode, videoPath, savePath, video, stickyFrames, repeatDraw, actualFrame
global configWindow, nodeColor, lineColor, selectedColor, exportColor, lineThickness, frameJump

# Some constants to use throughout the script
ADD_NODE, EDIT_NODE, MOVE_NODE, DELETE_NODE, ADD_LINE, ADD_CIRCLE = 0, 1, 2, 3, 4, 5

# Variables related to the drawing
nodeColor = (0, 255, 0)
lineColor = (0, 255, 0)
selectedColor = (255, 0, 0)
exportColor = (0, 0, 0)
lineThickness = 10
frameJump = 1

# Control variables
frameSize = (600, 800, 3)
stickyMode = ADD_NODE
repeatDraw = True
actualFrame = 0

# Initial application state
videoPath = 'initialScreen.avi'
video = VideoProcessing(videoPath)
stickmanFrames = StickmanFrames()

# savePath is None until a place has been entered
savePath = None

# Update the stickman drawing on screen
def updateDraw():
    # Copy actual frame
    image = np.copy(video.getFrame())
    stickmanFrames.drawFigure(actualFrame, image, lineThickness,
                              lineColor, nodeColor, selectedColor)
    
    # Place on the right label
    image = Image.fromarray(image)
    image = ImageTk.PhotoImage(image)
    imLabel.configure(image=image)
    imLabel.image = image

# Go to right frame on the video. If it is valid
def setFrame(frameIndex = None):
    global actualFrame
    if frameIndex < 0:
        return
    
    if frameIndex is None or frameIndex < video.nFrames:
        video.setFrame(frameIndex, frameSize)
    
    if frameIndex is not None:
        actualFrame = frameIndex
        entryText.set(str(frameIndex+1) + '/' + str(video.nFrames))
        if repeatDraw:
            stickmanFrames.repeatByCopy(frameIndex)
    updateDraw()

def configWindowClosed():
    global configWindow, nodeColor, lineColor, selectedColor, exportColor, lineThickness, frameJump
    nodeColor     = configWindow.getColor('Node')
    lineColor     = configWindow.getColor('Edge')
    selectedColor = configWindow.getColor('Selected')
    exportColor   = configWindow.getColor('Export')
    lineThickness = configWindow.getLineThickness()
    frameJump     = configWindow.getFrameJump()
    updateDraw()

def openConfigWindow():
        global configWindow, nodeColor, lineColor, selectedColor, exportColor, lineThickness, frameJump
        # Creates progress bar (immediatly appears on screen)
        configWindow = ConfigWindow(root, nodeColor, lineColor, selectedColor,
                              exportColor, lineThickness, frameJump, configWindowClosed)

# Called everytime the user clicks on ok
def entryCallback():
    frameIndex = entryText.get()
    try:
        frameIndex = int(frameIndex)-1
    except:
        return
    setFrame(frameIndex)

# Set previous frame
def previousFrame():
    setFrame(actualFrame-frameJump)

# Select next frame
def nextFrame():
    setFrame(actualFrame+frameJump)

# Reads user imput for common inputs. Those are used to control the video
# position and zooming
def keyboardInput(event):
    if len(event.char) == 0:
        return
    key = ord(event.char)
    if key == ord('-'):
        video.zoom(-10)
        setFrame()
    if key == ord('+'):
        video.zoom(+10)
        setFrame()
    if key == ord('a'):
        video.translate(x = -10)
        setFrame()
    if key == ord('d'):
        video.translate(x = +10)
        setFrame()
    if key == ord('s'):
        video.translate(y = +10)
        setFrame()
    if key == ord('w'):
        video.translate(y = -10)
        setFrame()

# Zooming on mouse wheel    
def mouseWheelEvent(event):
    amount = event.delta / 12
    video.zoom(amount)
    setFrame()

# Event for mouse click.
# Mouse is used for editting the figure
def mouseClick(event):
    global stickyMode
    
    # We only use clicks on the main label. With the exception of the frame
    # entry, where we erase the text
    if event.widget is not imLabel:
        if event.widget is entryFrame:
            entryText.set('')
        return
    
    # Get current index and see the state to interact
    frameIndex = actualFrame
    if stickyMode == ADD_NODE:
        # Add a node and update
        stickmanFrames.insertNode(frameIndex, event.x, event.y)
        updateDraw()
        
    elif stickyMode == EDIT_NODE:
        # See if any node is selected. If not, select one
        # If a node is selected, mode to mouse position
        nodeIndex = stickmanFrames.selectedNode(frameIndex)
        if nodeIndex is None:
            stickmanFrames.selectNode(frameIndex, event.x, event.y)
        else:
            stickmanFrames.editNode(frameIndex, nodeIndex, event.x, event.y)
            stickmanFrames.unselectNodes(frameIndex)
        updateDraw()
        
    elif stickyMode == MOVE_NODE:
        # Supose the user used the arrow keys to move a selected node, than we
        # are here. This select a node and sends back to edit mode. The user
        # has no knowledge of this
        stickmanFrames.selectNode(frameIndex, event.x, event.y)
        stickyMode = EDIT_NODE
        updateDraw()
        
    elif stickyMode == DELETE_NODE:
        # Select (if mouse is close) and delete any node. Also, edges are
        # update to reflect changes
        stickmanFrames.selectNode(frameIndex, event.x, event.y)
        selected = stickmanFrames.selectedNode(frameIndex)
        if selected is not None:
            stickmanFrames.removeNode(frameIndex, selected)
        updateDraw()
        
    elif stickyMode == ADD_LINE or stickyMode == ADD_CIRCLE:
        # The only difference between line and circle is the edgeType argument.
        # If a node is selected, add edge and selected newer node.
        # If no node is selected, select a node.
        edgeType = 'line' if stickyMode == ADD_LINE else 'circle'
        nodeIndex = stickmanFrames.selectedNode(frameIndex)
        if nodeIndex is None:
            stickmanFrames.selectNode(frameIndex, event.x, event.y)
        else:
            newIndex = stickmanFrames.insertNode(frameIndex, event.x, event.y)
            stickmanFrames.insertEdge(frameIndex, nodeIndex, newIndex, edgeType)
            stickmanFrames.selectNode(frameIndex, event.x, event.y)
        updateDraw()

# An special state is generated to handle node editting by keyboard
def moveNode(event):
    global stickyMode
    
    # If EDIT_MODE, set MOVE_NODE. Translate node by one unit accorfing to
    # user input
    if stickyMode == EDIT_NODE or stickyMode == MOVE_NODE:
        stickyMode = MOVE_NODE
        nodeIndex = stickmanFrames.selectedNode(actualFrame)
        if nodeIndex is None:
            return
        
        node = stickmanFrames.getFrame(actualFrame).getNode(nodeIndex)
        newX, newY = node.x, node.y
        
        if event.keysym == 'Right':
            newX += 1
        elif event.keysym == 'Left':
            newX -= 1
        elif event.keysym == 'Up':
            newY -= 1
        elif event.keysym == 'Down':
            newY += 1
        
        stickmanFrames.editNode(actualFrame, nodeIndex, newX, newY)
        updateDraw()

# Paints green the selected button and sets stickyMode according
def setStickyMode(mode):
    global stickyMode
    stickyMode = mode
    
    addNodeButton.configure(bg='white')
    editNodeButton.configure(bg='white')
    addEdgeButton.configure(bg='white')
    addCircleButton.configure(bg='white')
    deleteNodeButton.configure(bg='white')
    if stickyMode == ADD_NODE:
        addNodeButton.configure(bg='green')
    elif stickyMode == EDIT_NODE:
        editNodeButton.configure(bg='green')
    elif stickyMode == DELETE_NODE:
        deleteNodeButton.configure(bg='green')
    elif stickyMode == ADD_LINE:
        addEdgeButton.configure(bg='green')
    elif stickyMode == ADD_CIRCLE:
        addCircleButton.configure(bg='green')
    
    stickmanFrames.unselectNodes(actualFrame)
    updateDraw()

# Tells if frames should repeat draw or not.
# Changes from true to false and vice-versa everytime the button is clicked
def toggleRepeat():
    global repeatDraw
    repeatDraw = not repeatDraw
    
    if not repeatDraw:
        repeatButton.config(relief='raised')
    else:
        repeatButton.config(relief='sunken')
    stickmanFrames.newByCopy = repeatButton

def interpolate():
    stickmanFrames.interpolate()


# Opens save dialog and tries to save animation and resource location.
# Notice that if video source is moved, an error will occur
def saveDialog(event = None):
    global savePath
    if savePath == None or event is None or event.keysym == 'S':
        path = asksaveasfilename(defaultextension = '.anm',
                                 filetypes=(('Animation', '.anm'),
                                            ("All Files", "*.*")))
        if path != '':
            savePath = path
        else:
            return
    try:
        with open(savePath, 'wb') as f:
            pickle.dump([stickmanFrames, videoPath], f)
    except:
        print('Erro ao salvar arquivo')
     
# Load saved state
def loadDialog(event = None):
    global stickmanFrames, videoPath, video, frameSize
    path = askopenfilename(defaultextension = '.anm',
                           filetypes=(('Animation', '.anm'),
                                      ("All Files", "*.*")))
    try:
        with open(path, 'rb') as f:
            stickmanFrames, videoPath = pickle.load(f)
            video = VideoProcessing(videoPath)
            setFrame(0)
    except:
        print('Erro ao abrir arquivo')

# Load a new video or set of images
def loadVideo(event = None, askUser = True):
    global videoPath, video, frameSize
    
    validFormats = (('All Files', '*.*'),
                    ('MPEG Layer-4 Audio', '.mp4'),
                    ('Audio Video Interleave', '.avi'),
                    ('JPEG files', '.jpg'),
                    ('JPEG files', '.jpeg'),
                    ('JPEG files', '.jpe'),
                    ('Portable Network Graphics', '.png'),
                    ('Portable image format', '.pbm'))
    
    files = askopenfilenames(parent=root, title='Choose file',
                             defaultextension = '*.*', filetypes=validFormats)
    
    # Verifies if the user entered a video or a bunch of images.
    path = ''
    if len(files) > 1:
        # Go over image formats and verify if file is one of the image formats
        valid = False
        for options in validFormats[3:]:
            if files[0].endswith(options[1]):
                valid = True
        
        # In positive case, we are good
        if valid:
            imagesToVideo(root.tk.splitlist(files), 'temporary.avi')
            path = 'temporary.avi'
        else:
            return
    elif len(files) == 1:
        # Check if file loaded is a video
        if files[0].endswith('.mp4') or files[0].endswith('.avi'):
            path = files[0]
    
    # If path was successifully set, proceed to loading
    if path != '':
        # Update path
        videoPath = path
        video = VideoProcessing(videoPath)
        setFrame(0)

# Use the export animation facility to export our animation
def exportAnimation(event = None):
    folderPath = askdirectory()
    if folderPath != '':
        stickmanFrames.exportAnimation(folderPath, lineThickness, exportColor)

# Instance tk window
root = tk.Tk()
root.iconbitmap('stickmanAnimator.ico')

# Bind special keys and shortcuts
root.bind('<Key>', keyboardInput)
root.bind('<MouseWheel>', mouseWheelEvent)
root.bind("<Button-1>", mouseClick)
root.bind("<Left>", moveNode)
root.bind("<Right>", moveNode)
root.bind("<Up>", moveNode)
root.bind("<Down>", moveNode)
root.bind("<Control-s>", saveDialog)
root.bind("<Control-S>", saveDialog)
root.bind("<Control-o>", loadDialog)
root.bind("<Control-O>", loadVideo)
root.bind("<Control-e>", exportAnimation)

# Create top bar
loadVideoButton = tk.Button(root, text='Load video or images', command=loadVideo)
loadProjectButton = tk.Button(root, text='Load project', command=loadDialog)
saveProjectButton = tk.Button(root, text='Save as', command=saveDialog)
exportAnimButton = tk.Button(root, text='Export animation', command=exportAnimation)
frameConfigButton = tk.Button(root, text='Configuration', command=openConfigWindow)

# Place top bar
loadVideoButton.grid(row = 0, column = 0, columnspan = 4, sticky='we')
loadProjectButton.grid(row = 0, column = 4, columnspan = 4, sticky='we')
saveProjectButton.grid(row = 0, column = 8, columnspan = 4, sticky='we')
exportAnimButton.grid(row = 0, column = 12, columnspan = 4, sticky='we')
frameConfigButton.grid(row = 0, column = 16, columnspan = 4, sticky='we')

# Create entry widget for holding frame number
imLabel = tk.Label(root)
entryText = tk.StringVar()
entryFrame = tk.Entry(root, textvariable=entryText, width=6, justify='center')
entryText.set('1')

# Create buttons to navigate on frames
buttonOk = tk.Button(root, text='ok', command=entryCallback)
buttonPr = tk.Button(root, text='<<', command=previousFrame)
buttonNe = tk.Button(root, text='>>', command=nextFrame)

# Create node manipulation taskbar
addNodeButton     = tk.Button(root, text='Add', command=lambda:setStickyMode(ADD_NODE))
editNodeButton    = tk.Button(root, text='Edit', command=lambda:setStickyMode(EDIT_NODE))
deleteNodeButton  = tk.Button(root, text='Delete', command=lambda:setStickyMode(DELETE_NODE))
addEdgeButton     = tk.Button(root, text='Line', command=lambda:setStickyMode(ADD_LINE))
addCircleButton   = tk.Button(root, text='Circle', command=lambda:setStickyMode(ADD_CIRCLE))
repeatButton      = tk.Button(root, text='Repeat', relief='sunken', command=toggleRepeat)
interpolateButton = tk.Button(root, text='Insert', command=interpolate)

# Our image covers the whole width
imLabel.grid(row=1, column=0, columnspan=20)

# Frame text
frameLabel = tk.Label(root, text = 'Frame:')
frameLabel.grid(row=2, column=0, sticky='e')

# Place frame navigation widgets
entryFrame.grid(row=2, column = 2, sticky='we')
buttonOk.grid(row=2, column = 3, sticky='we')
buttonPr.grid(row=2, column = 1, sticky='we')
buttonNe.grid(row=2, column = 4, sticky='we')

# Node text
nodeLabel = tk.Label(root, text = 'Nodes:')
nodeLabel.grid(row=2, column=7, sticky='e')

# Place node manipulation widgets
addNodeButton.grid(row=2, column = 8, sticky='we')
editNodeButton.grid(row=2, column = 9, sticky='we')
deleteNodeButton.grid(row=2, column = 10, sticky='we')
addEdgeButton.grid(row=2, column = 11, sticky='we')
addCircleButton.grid(row=2, column = 12, sticky='we')

# Buttons for control of repetition and interpolation
repeatButton.grid(row=2, column = 18, sticky='we')
interpolateButton.grid(row=2, column = 19, sticky='we')

# Set uniform for all columns
for i in range(20):
    root.grid_columnconfigure(i, weight=1, uniform="a")
root.grid_rowconfigure(1, weight=1)

# Positionate on first frame and set ADD_NODE as default
setFrame(0)
setStickyMode(ADD_NODE)

root.mainloop()