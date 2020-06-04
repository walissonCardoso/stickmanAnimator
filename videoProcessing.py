import cv2
import numpy as np

# I find a little weird to use 0, 1 index for height and width, so we will use
# some contants
X, Y = 1, 0

# This auxiliary function converts a set of images to frames in a video.
def imagesToVideo(imagePathList = [], outPath = 'temp.avi', fps = 24):
    # imagePathList: a list of path of images to convert to frames on a video
    
    # Below we read all images and append
    frameArray = []
    for path in imagePathList:
        img = cv2.imread(path)
        height, width, layers = img.shape
        size = (width, height)
        frameArray.append(img)
    
    # Add frames to video
    video = cv2.VideoWriter(outPath, cv2.VideoWriter_fourcc(*'DIVX'), fps, size)
    for frame in frameArray:
        video.write(frame)
        
    # Save video on disk
    video.release()

class VideoProcessing:
    def __init__(self, path):
        # load video from path
        self.frames = cv2.VideoCapture(path)
        # size of the video
        self.nFrames = int(self.frames.get(cv2.CAP_PROP_FRAME_COUNT))
        # variable to hold current frame
        self.frame = None
    
        self.actualFrame = 0
        self.translation = np.array([0, 0], dtype=np.int)
        self.extraImageWidth = 0
    
    # Run to the required frame and process it
    def setFrame(self, frameIndex = None, frameSize = (600, 800, 3)):
        if frameIndex is None:
            frameIndex = self.actualFrame
        
        self.actualFrame = frameIndex
        if frameIndex >= self.nFrames:
            self.actualFrame = self.nFrames-1
        
        if self.nFrames > 1 or self.frame is None:
            self.frames.set(cv2.CAP_ANY, frameIndex)
            _, self.frame = self.frames.read()
        self.frame = self.processFrame(self.frame, frameSize)
    
    # Just return 
    def getFrame(self):
        return self.frame
    
    # Fit frame on frame screen
    def processFrame(self, frame, frameSize):
        if frame is None:
            return
        #Get frame in RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imageWidth = frameSize[X] + self.extraImageWidth
        
        # Calculate image height based on width. Note that image size can be
        # changed with the zoomming process
        proportion = image.shape[Y] / image.shape[X]
        imageHeight = int(imageWidth * proportion)
        image = cv2.resize(image, (imageWidth, imageHeight))
        
        # Frame background is pure black
        frame = np.zeros(frameSize, dtype=np.uint8)
        imShape = image.shape[:2]
        
        # Those variables get the visible part of the image in the frame
        pfX1 = max(self.translation[X], 0)
        pfY1 = max(self.translation[Y], 0)
        pfX2 = min(imShape[X] + self.translation[X], frameSize[X])
        pfY2 = min(imShape[Y] + self.translation[Y], frameSize[Y])
        
        piX1 = max(-self.translation[X], 0)
        piY1 = max(-self.translation[Y], 0)
        piX2 = piX1 + (pfX2 - pfX1)
        piY2 = piY1 + (pfY2 - pfY1)
        
        # Copy image visible part
        frame[pfY1:pfY2, pfX1:pfX2] = image[piY1:piY2, piX1:piX2]
        
        return frame
    
    # zoom-in (factor > 0) or zoom-out image (factor < 0)
    def zoom(self, factor):
        self.extraImageWidth += int(factor)
        self.setFrame()
    
    # move image in pixels scale
    def translate(self, x = 0, y = 0):
        self.translation[X] = self.translation[X] + int(x)
        self.translation[Y] = self.translation[Y] + int(y)
        self.setFrame()

if __name__ == '__main__':
    imagePath = 'initialScreen.png'
    videoPath = 'temporary.avi'
    
    imagesToVideo([imagePath], videoPath)
    
    video = VideoProcessing(videoPath)
    video.setFrame(0)
    print('Loaded video with', video.nFrames, 'frames')
    print('Frame shape:', video.getFrame().shape)