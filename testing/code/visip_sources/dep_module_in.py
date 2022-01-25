import visip as wf
import analysis_in as tool
#import analysis_in



@wf.Class
class Square:
    topleft: tool.Point
    botright: tool.Point

@wf.workflow
def xflip(square):
    return Square(tool.Point(square.botright.x, square.topleft.y), tool.Point(square.topleft.x, square.botright.y))

@wf.workflow
def dependent_action():
    return tool.test_dict(0, 2, 1)    # result: (1. 2)

# Try to use action_lib.add_float