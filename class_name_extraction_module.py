import ast


class MyParsedObject:
    """ This class creates a parsed object using ast module """

    def __init__(self, file_dir):
        self.file_dir = file_dir
        self.content = self.get_content()
        self.tree = self.parse_tree()
        self.class_name_list = self.build_class_name_list()

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

    def build_class_name_list(self):
        class_name_list = list()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                class_name_list.append(node.name)
        return class_name_list

    def get_class_name_list(self):
        print('class names of the file: ', self.class_name_list)
        return self.class_name_list


def class_name_extraction(file_dir):
    my_parsed_obj = MyParsedObject(file_dir)
    return my_parsed_obj.get_class_name_list()