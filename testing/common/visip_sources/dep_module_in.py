import common as wf
import analysis_in as tool



@wf.Class
class Square:
    topleft: tool.Point
    botright: tool.Point

@wf.workflow
def xflip(square):
    return Square(tool.Point(square.botright.x, square.topleft.y), tool.Point(square.topleft.x, square.botright.y))
