# boilerplate for package modules
if __name__ == '__main__':
    from pathlib import Path
    import sys
    file = Path(__file__).resolve()
    parent, root = file.parent, file.parents[1]
    sys.path.append(str(root))

    # Additionally remove the current file's directory from sys.path
    try:
        sys.path.remove(str(parent))
    except ValueError: # Already removed
        pass


import common as cmn
from PyQt5 import QtWidgets, QtGui

class Grid(QtWidgets.QGraphicsScene):
    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.lines = []
        self.scale = 20

        self.setOpacity(1)

    def drawGrid(self):
        arr_x = cmn.mesh.x * self.scale
        width = arr_x[-1]
        arr_y = cmn.mesh.y * self.scale
        height = arr_y[-1]

        self.setSceneRect(0, 0, width, height)
        self.setItemIndexMethod(QtWidgets.QGraphicsScene.NoIndex)

        pen = QtGui.QPen(QtGui.QColor(0,0,0), 1, Qt.SolidLine)

        for x in arr_x:
            self.lines.append(self.addLine(x,0,x,height,pen))

        for y in arr_y:
            self.lines.append(self.addLine(0,y,width,y,pen))

    def setVisible(self,visible=True):
        for line in self.lines:
            line.setVisible(visible)

    def deleteGrid(self):
        for line in self.lines:
            self.removeItem(line)
        del self.lines[:]

    def setOpacity(self,opacity):
        for line in self.lines:
            line.setOpacity(opacity)
