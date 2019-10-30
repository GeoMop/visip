import common as wf
import analysis_in as tool


@wf.Class
class Square:
    topleft:tool.Point
    botright:tool.Point


@wf.workflow
def xflip(self, square):
    Point_2 = tool.Point(x=square.topleft.x, y=square.botright.y)
    Square_1 = Square(topleft=tool.Point(x=square.botright.x, y=square.topleft.y), botright=Point_2)
    return Square_1