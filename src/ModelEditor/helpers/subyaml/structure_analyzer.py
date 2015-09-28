from data import Position, Span, CompositeNode
from helpers.subyaml.node_analyzer import NodeStructureType, NodeAnalyzer
from helpers.subyaml.line_analyzer import LineAnalyzer
from helpers import Notification


class StructureAnalyzer:
    """
    Anayze yaml file for find specific attribute, for examle json structure
    """
    def __init__(self):
        """init"""
        pass

    @staticmethod
    def _get_array_separator(lines, start_pos, end_pos):
        """get array separator"""
        if start_pos is not None and end_pos is not None and \
           start_pos.line <= end_pos.line:
            for i in range(start_pos.line, end_pos.line+1):
                if i>len(lines):
                    break
                start=0
                if start_pos.line == i:
                   start = start_pos.column - 1
                end = len(lines[i-1])
                if end_pos.line == i:
                    end = end_pos.column - 1
                pos = LineAnalyzer.get_separator(lines[i-1],"-", start, end)
                if pos != -1:
                    return Position(i, pos+1)
        return None

    @staticmethod
    def _get_json_separator(lines, start_pos, end_pos):
        """get array separator"""
        if start_pos is not None and end_pos is not None and \
           start_pos.line <= end_pos.line:
            for i in range(start_pos.line, end_pos.line+1):
                if i > len(lines):
                    break
                start = 0
                if start_pos.line == i:
                    start = start_pos.column - 1
                end = len(lines[i-1])
                if end_pos.line == i:
                    end = end_pos.column - 1
                for char in ["{", "[", ",", "}", "]"]:
                    pos = LineAnalyzer.get_separator(lines[i-1], char, start, end)
                    if pos != -1:
                        return Position(i, pos+1)
        return None

    @classmethod
    def add_node_info(cls, doc, root, notification_handler):
        """Add border information about nodes"""
        lines = doc.splitlines()
        if isinstance(root, CompositeNode):
            cls._analyze_node(lines, root, notification_handler)

    @classmethod
    def _analyze_node(cls, lines, node, notification_handler):
        """Node analysis is performed recursively"""
        na = NodeAnalyzer(lines, node)
        node_type = na. get_node_structure_type()
        if node_type == NodeStructureType.json_array or \
                node_type == NodeStructureType.json_dict:
            cls._split_children(lines, node, cls._get_json_separator)
            if (len(node.children) > 0 and
                    node.children[0].separators is not None and
                    node.children[0].separators.start is not None and
                    node.children[len(node.children) - 1].separators is not None and
                    node.children[len(node.children) - 1].separators.end is not None and
                    node.children[0].separators.start.line <
                    node.children[len(node.children) - 1].separators.end.line):
                notification = Notification.from_name('MultiLineFlow')
                notification.span = node.span
                notification_handler.report(node)
        elif node_type == NodeStructureType.array:
            cls._split_children(lines, node, cls._get_array_separator, False)
        for child in node.children:
            if isinstance(child, CompositeNode):
                cls._analyze_node(lines, child, notification_handler)

    @classmethod
    def _split_children(cls, lines, node, func, is_flow=True):
        """Find and write separators (borders) positions between nodes"""
        if len(node.children) > 0:
            na = NodeAnalyzer(lines, node)
            start_pos = func(lines, na.get_node_key_end(), node.children[0].start)
            if len(node.children) == 1:
                end_pos = func(lines, node.children[0].end, node.end)
            else:
                end_pos = func(lines, node.children[0].end,  node.children[1].start)
            node.children[0].is_flow = is_flow
            node.children[0].separators = Span(start_pos, end_pos)
        for i in range(1, len(node.children)-1):
            start_pos = end_pos
            end_pos = func(lines, node.children[i].end,  node.children[i+1].start)
            node.children[i].is_flow = True
            node.children[i].separators = Span(start_pos, end_pos)
        if len(node.children) > 1:
            start_pos = end_pos
            end_pos = func(lines, node.children[len(node.children)-1].end,  node.end)
            node.children[len(node.children)-1].is_flow = True
            node.children[len(node.children)-1].separators = Span(start_pos, end_pos)