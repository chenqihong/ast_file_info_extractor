import ast
from common_helper import *


class MyParsedObject:
    """ This class creates a parsed object using ast module """

    def __init__(self, file_dir):
        self.file_dir = file_dir
        self.content = get_content(file_dir)
        self.tree = parse_tree(self.content)
        self.class_name_list = self.build_class_name_list()

    def build_class_name_list(self):
        class_name_list = list()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                start_line_number, end_line_number = node.lineno - 1, node.end_lineno - 1
                class_name_list.append((node.name, start_line_number, end_line_number))
        return class_name_list

    def get_class_name_list(self):
        print('class names of the file: ', self.class_name_list)
        return self.class_name_list


def class_name_extraction(file_dir):
    my_parsed_obj = MyParsedObject(file_dir)
    return my_parsed_obj.get_class_name_list()