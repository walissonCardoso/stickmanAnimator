import tkinter as tk

from tkinter.ttk import Separator

# A modified entry widget that is capable of reseting its own value, detect
# focus, and check for valid values
class IntEntry(tk.Entry):
    def __init__(self, master, initValue = '', minValue = 0, maxValue = 1e10, **kwargs):
        # Create a variable to keep track of the widget's value
        self.var = tk.StringVar()
        tk.Entry.__init__(self, master, textvariable=self.var, **kwargs)
        
        # Back up of the old value and max possible value
        self.oldValue = str(initValue)
        self.var.set(self.oldValue)
        self.minValue = minValue
        self.maxValue = maxValue
        
        # Check value at each modification
        self.var.trace('w', self.check)
        self.get, self.set = self.var.get, self.var.set
        
        # Bind focus in and out for smart response
        self.bind("<FocusIn>", self.onFocusIn)
        self.bind("<FocusOut>", self.onFocusOut)
    
    # Check at every field moodification
    def check(self, *args):
        # Allow empty string
        value = self.get()
        if value == '':
            self.set(value)
            return
        
        # see if it is integer and is inside range
        try:
            value = int(value)
            if value >= self.minValue and value <= self.maxValue:
                self.oldValue = value
                self.set(self.oldValue)
        except:
            # reset  value
            self.set(self.oldValue) 
            
    
    # If focus in, erase value displayed
    def onFocusIn(self, event = None):
        if event is None or event.widget is self:
            self.var.set('')
    
    # If focus out, and text is still empty, reset to last valid value
    def onFocusOut(self, event = None):
        if event is None or event.widget is self:
            if self.get() == '':
                self.set(self.oldValue)
        


# This class shows a popup window to update the confguration variables
class ConfigWindow(tk.Toplevel):
    def __init__(self, parent, nodeColor, lineColor, selectedColor,
                 exportColor, lineThickness, frameJump, onClosing):
        # Base class constructor
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        # Make the window appears above the main window
        self.transient(parent)
        # Grab clicks
        self.grab_set()
        
        ### color part in the interface
        # Just print labels
        labels = ('Color', 'R', 'G', 'B')
        for j, label in enumerate(labels):
            tk.Label(self, text = label).grid(row=0, column=j)
        
        # color fields
        colors = (nodeColor, lineColor, selectedColor, exportColor)
        names = ('Node', 'Edge', 'Selected', 'Export')
        
        # Create labels and entries (one color per row)
        self.colorsGrid = {}
        for name, color in zip(names, colors):
            gridRow = [tk.Label(self, text = name)]
            for c in color:
                gridRow.append(IntEntry(self, c, 255, width=4, justify='center'))
            self.colorsGrid[name] = gridRow
        
        # positionate on grid (put to screen)
        for index, key in enumerate(self.colorsGrid):
            self.colorsGrid[key][0].grid(row=index+1, column=0, sticky='e')
            for j in range(1, len(gridRow)):
                self.colorsGrid[key][j].grid(row=index+1, column=j, sticky='we', padx=3)
        
        row = len(colors) + 1
        Separator(self, orient=tk.HORIZONTAL).grid(row=row, columnspan=4,
                                                   sticky='we', pady=3)
        
        self.lineThicknessLabel = tk.Label(self, text='Line thickness')
        self.lineThicknessEntry = IntEntry(self, lineThickness, 200, width=4, justify='center')
        
        self.skipFramesLabel = tk.Label(self, text='Frame jump')
        self.skipFramesEntry = IntEntry(self, initValue=frameJump, width=4,
                                        minValue=1, maxValue=24, justify='center')
        
        row += 1
        self.lineThicknessLabel.grid(row=row, column=0, columnspan=2, sticky='e')
        self.lineThicknessEntry.grid(row=row, column=2)
        self.skipFramesLabel.grid(row=row+1, column=0, columnspan=2, sticky='e')
        self.skipFramesEntry.grid(row=row+1, column=2)
        
        self.resizable(False, False)
        
        def closeWindow():
            # First focus out every single entry box in this interface
            for key in self.colorsGrid:
                entries = self.colorsGrid[key][1:]
                for entry in entries:
                    entry.onFocusOut()
            self.lineThicknessEntry.onFocusOut()
            self.skipFramesEntry.onFocusOut()
            
            # Call callback we created outside
            onClosing()
            # Destroy this window
            self.destroy()
        
        # Connect closing procedure
        self.protocol("WM_DELETE_WINDOW", closeWindow)
        
    
    def entryValidator(self, number):
        try:
            int(number)
            return number >= 0 and number <= 255
        except:
            return False
    
    def getColor(self, key):
        if key in self.colorsGrid:
            color = self.colorsGrid[key][1:]
            return (int(color[0].get()),
                    int(color[1].get()),
                    int(color[2].get()))
    
    def getLineThickness(self):
        return int(self.lineThicknessEntry.get())
    
    def getFrameJump(self):
        return int(self.skipFramesEntry.get())
        

# The code below shows how this class works. We define some really simple
# interface and show a work simulation
if __name__ == '__main__':
    # Create interface
    root = tk.Tk()
    
    global nodeColor, lineColor, selectedColor, exportColor, lineThickness, frameJump
    nodeColor = (0, 255, 0)
    lineColor = (0, 255, 0)
    selectedColor = (255, 0, 0)
    exportColor = (0, 0, 0)
    lineThickness = 10
    frameJump = 0
    
    global config
    config = None
    
    def configWindowClosed():
        global config, nodeColor, lineColor, selectedColor, exportColor, lineThickness, frameJump
        nodeColor     = config.getColor('Node')
        lineColor     = config.getColor('Edge')
        selectedColor = config.getColor('Selected')
        exportColor   = config.getColor('Export')
        lineThickness = config.getLineThickness()
        frameJump     = config.getFrameJump()
    
    # A simple function that starts the processing. Some thing like this would
    # exist in the real application
    def openConfigWindow():
        global config
        # Creates progress bar (immediatly appears on screen)
        config = ConfigWindow(root, nodeColor, lineColor, selectedColor,
                              exportColor, lineThickness, frameJump, configWindowClosed)
    
    # Position a button for our example
    tk.Button(root, text = 'Configuration', command=openConfigWindow).grid(sticky='we')
    # Execute everything
    root.mainloop()