import visip as wf
#import analysis_in as tool
import analysis_in



@wf.Class
class Square:
    topleft: analysis_in.Point
    botright: analysis_in.Point

@wf.workflow
def xflip(square):
    return Square(analysis_in.Point(square.botright.x, square.topleft.y), analysis_in.Point(square.topleft.x, square.botright.y))

@wf.workflow
def dependent_action():
    return analysis_in.test_dict(0, 2, 1)    # result: (1. 2)

# Try to use action_lib.add_float