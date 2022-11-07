import ast
from collections import defaultdict


def get_content(file_dir, mode='str'):
    with open(file_dir, 'r') as f:
        if mode == 'str':
            return f.read()
        else:
            return f.readlines()


def parse_tree(file_content_str, file_dir=None, mode=None):
    try:
        return ast.parse(file_content_str)
    except Exception:
        if mode is None:
            print("For file dir: ", file_dir, " tree failed")
            exit(0)


def extract_full_statement(current_line_number, my_parsed_object):
    single_statement_line_scope_dict = my_parsed_object.get_single_statement_line_scope_dict()
    for ast_statement, start_line_number, mode in single_statement_line_scope_dict:
        start_line_number, end_line_number = single_statement_line_scope_dict[(ast_statement, start_line_number, mode)]
        if start_line_number == current_line_number:
            return ast_statement, start_line_number, end_line_number, mode
    return None, current_line_number, current_line_number, None


def find_full_line_original(file_content_list, start_line_num, end_line_num):
    result_line = ""
    for line in file_content_list[start_line_num:end_line_num+1]:
        result_line += line.rstrip() + '\n'
    return result_line


def analysis_call_statement(statement):
    """ This function takes a call statement, and gets the method call object name and function_pure_name """
    if '.' in statement:
        method_call_object_name, function_pure_name = statement.split(".", 1)
        method_call_object_name = method_call_object_name.strip()
        function_pure_name = function_pure_name.split("(", 1)[0].strip()
    else:
        method_call_object_name = None
        function_pure_name = statement.split('(', 1)[0].strip()
    return method_call_object_name, function_pure_name


def find_node_type_list(full_line):
    tree = parse_tree(full_line, mode='skip')
    node_type_list = list()
    for node in ast.walk(tree):
        node_type_list.append(type(node))
    return list(set(node_type_list))


def is_disqualify_line(full_line_original):
    """ This function checks if the given line is a valid assert statement """
    full_line_original = full_line_original.strip()
    try:
        node_type_list = find_node_type_list(full_line_original)
    except:
        node_type_list = list()
    if 'super(' in full_line_original and 'class ' not in full_line_original:
        return True
    if 'import ' in full_line_original:
        return True
    if full_line_original.endswith(":"):
        return True
    if 'nonlocal ' in full_line_original:  # just a way to declare var
        return True
    if 'def ' in full_line_original:
        return True
    if 'global ' in full_line_original:
        return True
    if 'except ' in full_line_original and ast.excepthandler in node_type_list:
        return True
    if 'except:' in full_line_original and ast.excepthandler in node_type_list:
        return True
    if full_line_original.startswith('elif ') and ast.If in node_type_list:
        return True
    if 'for ' in full_line_original and ast.For in node_type_list:
        return True
    if full_line_original.startswith("@") or full_line_original == "":
        return True
    if (full_line_original.startswith("else:") or full_line_original.startswith('if ')) and ast.If in node_type_list:
        return True
    if full_line_original.startswith('while ') and ast.While in node_type_list:
        return True
    if full_line_original.startswith("with ") and ast.With in node_type_list:
        return True
    method_call_obj_name, function_pure_name = analysis_call_statement(full_line_original)
    if method_call_obj_name is not None and method_call_obj_name != 'self':
        return True
    if 'assert' not in function_pure_name:
        return True
    return False


def is_call_statement(full_line):
    full_line = full_line.strip()
    parsed_tree = ast.parse(full_line)
    for node in ast.walk(parsed_tree):
        if isinstance(node, ast.Call):
            return True
    return False


def is_include_in_candidate_list(all_candidates_list, start_line_num, end_line_num):
    for full_line_original, start_line_num_include, end_line_num_include in all_candidates_list:
        if start_line_num_include <= start_line_num and end_line_num_include >= end_line_num:
            return True
    return False


def build_line_parameter_dict(current_line):
    tree = ast.parse(current_line)
    line_parameter_dict = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            param_list = list()
            call = ast.get_source_segment(current_line, node)
            args = node.args
            keywords = node.keywords
            for ast_node in args:
                param_list.append(ast.get_source_segment(current_line, ast_node))
            for keyword_ast_node in keywords:
                try:
                    param_list.append(keyword_ast_node.arg + '=' + str(keyword_ast_node.value.value))
                except AttributeError:
                    param_list.append(keyword_ast_node.arg + '=' + str(ast.get_source_segment(current_line, keyword_ast_node.value)))
                except TypeError:
                    param_list.append(keyword_ast_node.value.id)
            line_parameter_dict[call] = param_list
    return line_parameter_dict


def get_left_right(current_line):
    tree = ast.parse(current_line)
    target = None
    value = current_line
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            target = ast.get_source_segment(current_line, node.targets[0])
            value = ast.get_source_segment(current_line, node.value)
            break
    return target, value