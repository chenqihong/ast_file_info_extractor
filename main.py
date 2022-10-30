# !/usr/bin/env python
__author__ = "Qi Hong Chen"

import ast
import math
import sys
from collections import defaultdict


class MyParsedObject:
    """ This class creates a parsed object using ast module """

    def __init__(self, file_dir):
        self.file_dir = file_dir
        self.content = self.get_content()
        self.tree = self.parse_tree()
        self.func_method_body_line_num_dict = self.build_func_method_line_num_dict()

    def get_content(self):
        with open(self.file_dir, 'r') as f:
            content = f.read()
        return content

    def parse_tree(self):
        try:
            return ast.parse(self.content)
        except Exception as a:
            print("Invalid Syntax:", a, "\nExiting...")
            exit(0)

    def build_func_method_line_num_dict(self):
        """ Create a dict, key: the line number scope and value: the body content """
        result = defaultdict(str)
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                start_line_number, end_line_number = node.lineno - 1, node.end_lineno - 1
                result[(start_line_number, end_line_number)] = ast.get_source_segment(self.content, node)
        return result

    def get_func_method_body_line_num_dict(self):
        """ return the func method body dict """
        return self.func_method_body_line_num_dict


def choose_close_body(potential_candidates):
    """ Returns the body of method/func for nested case"""
    closest_dist = math.inf
    result_body = None
    for start_line_num, end_line_num, statement in potential_candidates:
        diff = end_line_num - start_line_num + 1
        if diff < closest_dist:
            result_body = statement
    return result_body


def get_body(body_dict, line_num):
    """ Get the body of the method/func for the given line number"""
    potential_candidates = list()
    for start_line_num, end_line_num in body_dict:
        if start_line_num <= line_num <= end_line_num:
            potential_candidates.append((start_line_num, end_line_num, body_dict[(start_line_num, end_line_num)]))
    if not potential_candidates:
        print("Body not found, exiting .... ")
        exit(-1)
    return choose_close_body(potential_candidates)


def find_body(line_num, file_dir):
    """ The starter call, takes line num and file dir, find the body, exit if syntactically incorrect or not found """
    my_parsed_obj = MyParsedObject(file_dir)
    body_scope_dict = my_parsed_obj.get_func_method_body_line_num_dict()
    return get_body(body_scope_dict, line_num)


pass_line_num, pass_file_dir = sys.argv[1], sys.argv[2]
print(find_body(line_num=int(pass_line_num), file_dir=pass_file_dir))
