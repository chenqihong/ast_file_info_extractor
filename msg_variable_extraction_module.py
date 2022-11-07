import ast
from common_helper import *
from collections import defaultdict
from method_func_body_extraction_module import method_func_body_extraction
import csv
test_file_dir = 'e.py'
default_run_method_term = '__init__'


def load_sheet(sheet_dir):
    sheet_dict = defaultdict()
    with open(sheet_dir, 'r') as f:
        reader = csv.reader(f)
        for row in list(reader)[1:]:
            pure_call_name, index, _ = row
            sheet_dict[pure_call_name] = index
    return sheet_dict


def find_class_name(start_line_number, end_line_number, class_line_scope_dict):
    for class_name, start_line_number_key in class_line_scope_dict:
        class_start_line_num, class_end_line_num, statement = class_line_scope_dict[(class_name, start_line_number_key)]
        if class_start_line_num <= start_line_number <= end_line_number <= class_end_line_num:
            return class_name, True
    return None, False


def extract_desire_mode_statement(record_list, mode):
    for statement, current_mode in record_list:
        if current_mode == mode:
            return True, statement
    return False, None


def find_largest_scope(current_full_line_ast, current_statement, current_start_line_num, current_end_line_num, block_code_candidates_list):
    """ For the given candidate's range, find its largest range form """
    largest_start_line_num = current_start_line_num
    largest_end_line_num = current_end_line_num
    largest_original_statement = current_statement
    largest_full_ast_statement = current_full_line_ast
    for ast_statement, original_statement, start_line_num, end_line_num in block_code_candidates_list:
        if start_line_num < largest_start_line_num and largest_end_line_num < end_line_num:
            largest_start_line_num = start_line_num
            largest_end_line_num = end_line_num
            largest_original_statement = original_statement
            largest_full_ast_statement = ast_statement
    return largest_full_ast_statement, largest_original_statement, largest_start_line_num, largest_end_line_num


def filter_block_code_candidates_list(block_code_candidates_list):
    """ This function would filter the candidates who are covered by a outer call """
    result_list = list()
    for current_full_line_ast, current_full_line_original, current_start_line_num, current_end_line_num in block_code_candidates_list:
        result_tuple = find_largest_scope(current_full_line_ast, current_full_line_original, current_start_line_num, current_end_line_num, block_code_candidates_list)
        result_list.append(result_tuple)
    return result_list


class MyParsedObject:
    """ This class creates a parsed object using ast module """
    def __init__(self, file_dir=None):
        self.file_dir = file_dir
        self.content_str = get_content(file_dir, 'str')
        self.content_list = get_content(file_dir, 'list')
        self.tree = parse_tree(self.content_str)
        self.class_line_scope_dict = self.build_class_line_scope_dict()
        self.class_method_line_scope_dict = self.build_class_method_line_scope_dict()
        self.function_line_scope_dict = self.build_function_line_scope_dict()
        self.single_statement_line_scope_dict = self.build_single_statement_line_scope_dict()

    def build_class_line_scope_dict(self):
        class_line_scope_dict = defaultdict(list)
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                statement = ast.get_source_segment(self.content_str, node)
                start_line_number, end_line_number = node.lineno-1, node.end_lineno-1
                class_name = node.name
                class_line_scope_dict[(class_name, start_line_number)] = [start_line_number, end_line_number, statement]
        return class_line_scope_dict

    def build_class_method_line_scope_dict(self):
        class_method_line_scope_dict = defaultdict(list)
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                statement = ast.get_source_segment(self.content_str, node)
                start_line_number, end_line_number = node.lineno - 1, node.end_lineno - 1
                method_name = node.name
                class_name, is_method = find_class_name(start_line_number, end_line_number, self.class_line_scope_dict)
                if class_name is not None and is_method:
                    class_method_line_scope_dict[(class_name, method_name, start_line_number)] = [start_line_number, end_line_number, statement]
        return class_method_line_scope_dict

    def build_function_line_scope_dict(self):
        function_line_scope_dict = defaultdict(list)
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                statement = ast.get_source_segment(self.content_str, node)
                start_line_number, end_line_number = node.lineno - 1, node.end_lineno - 1
                function_name = node.name
                class_name, is_method = find_class_name(start_line_number, end_line_number, self.class_line_scope_dict)
                if class_name is None and not is_method:
                    function_line_scope_dict[(function_name, start_line_number)] = [start_line_number, end_line_number, statement]
        return function_line_scope_dict

    def build_single_statement_line_scope_dict(self):
        single_statement_record_dict = defaultdict(list)
        for node in ast.walk(self.tree):
            try:
                statement = ast.get_source_segment(self.content_str, node)
                start_line_num, end_line_num = node.lineno - 1, node.end_lineno - 1
            except AttributeError:
                continue
            if isinstance(node, ast.Call):
                single_statement_record_dict[(start_line_num, end_line_num)].append((statement, 'call'))
            if isinstance(node, ast.Assign):
                single_statement_record_dict[(start_line_num, end_line_num)].append((statement, 'assign'))
            if isinstance(node, ast.Return):
                single_statement_record_dict[(start_line_num, end_line_num)].append((statement, 'return'))
            else:
                single_statement_record_dict[(start_line_num, end_line_num)].append((statement, 'others'))
        single_statement_line_scope_dict = defaultdict(list)
        single_statement_record_dict = dict(single_statement_record_dict)
        for start_line_num, end_line_num in single_statement_record_dict:
            record_list = single_statement_record_dict[(start_line_num, end_line_num)]
            is_contain_return_result, return_statement = extract_desire_mode_statement(record_list, 'return')

            is_contain_assign_result, assign_statement = extract_desire_mode_statement(record_list, 'assign')

            is_contain_call_result, call_statement = extract_desire_mode_statement(record_list, 'call')
            is_contain_others_result, others_statement = extract_desire_mode_statement(record_list, 'others')
            if is_contain_return_result:
                single_statement_line_scope_dict[(return_statement, start_line_num, 'return')] = [start_line_num, end_line_num]
            elif is_contain_assign_result:
                single_statement_line_scope_dict[(assign_statement, start_line_num, 'assign')] = [start_line_num, end_line_num]
            elif is_contain_call_result:
                single_statement_line_scope_dict[(call_statement, start_line_num, 'call')] = [start_line_num, end_line_num]
            elif is_contain_others_result:
                single_statement_line_scope_dict[(others_statement, start_line_num, 'others')] = [start_line_num, end_line_num]
        return single_statement_line_scope_dict

    def get_file_content(self, mode):
        if mode == 'str':
            return self.content_str
        else:
            return self.content_list

    def get_single_statement_line_scope_dict(self):
        return self.single_statement_line_scope_dict

    def get_file_dir(self):
        return self.file_dir

    def get_class_method_line_scope_dict(self):
        return self.class_method_line_scope_dict

    def get_class_line_scope_dict(self):
        return self.class_line_scope_dict

    def get_function_line_scope_dict(self):
        return self.function_line_scope_dict


def check_block_code_statement(my_parsed_obj, all_candidates_list):
    single_statement_line_scope_dict = my_parsed_obj.get_single_statement_line_scope_dict()
    file_content_list = my_parsed_obj.get_file_content('list')
    block_code_candidate_list = list()
    for statement, start_line_num, mode in single_statement_line_scope_dict:
        start_line_num, end_line_num = single_statement_line_scope_dict[(statement, start_line_num, mode)]
        # print("start line num = ", start_line_num, " end line num = ", end_line_num)
        if is_include_in_candidate_list(all_candidates_list, start_line_num, end_line_num) or mode == 'others':
            continue
        full_line_original = find_full_line_original(file_content_list, start_line_num, end_line_num)
        # print("found full line original = ", full_line_original)
        full_line_ast, start_line_num, end_line_num, mode = extract_full_statement(start_line_num, my_parsed_obj)
        if is_disqualify_line(full_line_original):
            continue
        block_code_candidate_list.append((full_line_ast, full_line_original, start_line_num, end_line_num))
    return block_code_candidate_list, my_parsed_obj


def print_candidates(candidates_list, types='original', mode='full'):
    print("Printing for candidates of ", types)
    for full_line_original, start_line_num, end_line_num in candidates_list:
        if mode == 'line_num_only':
            print("start: ", start_line_num+1, " end: ", end_line_num+1)
        else:
            print(full_line_original, start_line_num, end_line_num)


def find_all_candidates(my_parsed_obj):
    current_line_number = 0
    all_candidates_list = list()
    file_content_list = my_parsed_obj.get_file_content('list')
    while current_line_number < len(file_content_list):
        full_line_ast, start_line_num, end_line_num, mode = extract_full_statement(current_line_number, my_parsed_obj)
        line_size = end_line_num - start_line_num + 1
        full_line_original = find_full_line_original(file_content_list, start_line_num, end_line_num)
        if full_line_ast is None or is_disqualify_line(full_line_original) or not is_call_statement(full_line_original):
            current_line_number += line_size
            continue
        all_candidates_list.append((full_line_ast, full_line_original, start_line_num, end_line_num))
    block_code_candidates_list, my_parsed_obj = check_block_code_statement(my_parsed_obj, all_candidates_list)
    block_code_candidates_list = filter_block_code_candidates_list(block_code_candidates_list)
    # print_candidates(block_code_candidates_list, 'block_candidates', 'line_num_only')
    # print_candidates(all_candidates_list, 'original', 'line_num_only')
    all_candidates_list = all_candidates_list + block_code_candidates_list
    all_candidates_list = list(set(all_candidates_list))
    return all_candidates_list


def is_contain_msg_indicator(parameter_list):
    for parameter in parameter_list:
        if '=' in parameter:
            left, right = parameter.split('=')
            left, right = left.strip(), right.strip()
            if 'msg' == left:
                return True, right
    return False, None


def get_current_method_class_name(body_start_line_num, my_parsed_obj):
    class_line_scope_dict = my_parsed_obj.get_class_line_scope_dict()
    for class_name, start_line_number in class_line_scope_dict:
        start_line_number, end_line_number, statement = class_line_scope_dict[(class_name, start_line_number)]
        if start_line_number <= body_start_line_num <= end_line_number:
            return class_name
    return None


def find_init_setup_body(pass_class_name, my_parsed_obj):
    class_method_line_scope_dict = my_parsed_obj.get_class_method_line_scope_dict()
    for class_name, method_name, start_line_number in class_method_line_scope_dict:
        if class_name != pass_class_name:
            continue
        start_line_number, end_line_number, statement = class_method_line_scope_dict[(class_name, method_name, start_line_number)]
        if method_name == default_run_method_term:
            return statement.split('\n')


def is_class_body(class_line_scope_dict, line_num):
    for class_name, start_line_number_key in class_line_scope_dict:
        class_start_line_num, class_end_line_num, statement = class_line_scope_dict[(class_name, start_line_number_key)]
        if class_start_line_num <= line_num <= class_end_line_num:
            return True
    return False


def is_function_body(function_line_scope_dict, line_num):
    for function_name, start_line_number in function_line_scope_dict:
        start_line_number, end_line_number, statement = function_line_scope_dict[(function_name, start_line_number)]
        if start_line_number <= line_num <= end_line_number:
            return True
    return False


def build_global_statement_list(my_parsed_obj):
    global_statement_list = list()
    class_line_scope_dict = my_parsed_obj.get_class_line_scope_dict()
    function_line_scope_dict = my_parsed_obj.get_function_line_scope_dict()
    for line_num, line in enumerate(my_parsed_obj.get_file_content('list')):
        if is_class_body(class_line_scope_dict, line_num):
            continue
        if is_function_body(function_line_scope_dict, line_num):
            continue
        global_statement_list.append((my_parsed_obj.get_file_content('list')[line_num], line_num))
    return global_statement_list


def find_target_str_same_scope(body_start_line_num, target_statement_start_line_num, my_parsed_obj, target_parameter):
    print('try to find target param = ', target_parameter)
    print("from line: ", body_start_line_num, " to ", target_statement_start_line_num)
    target_str = None
    current_counter = body_start_line_num + 1
    file_content_list = my_parsed_obj.get_file_content('list')
    while current_counter < target_statement_start_line_num:
        body_full_line_ast, body_full_line_start_line_num, body_full_line_end_line_num, mode = extract_full_statement(current_counter, my_parsed_obj)
        if mode is None or mode == 'others':
            current_counter += 1
            continue
        line_size = body_full_line_end_line_num - body_full_line_start_line_num + 1
        body_full_line_original = find_full_line_original(file_content_list, body_full_line_start_line_num, body_full_line_end_line_num)
        print('line_size = ', line_size)
        print('body_full_line_original = ', body_full_line_original)
        if body_full_line_ast is None:
            current_counter += line_size
            continue
        var, expr = get_left_right(body_full_line_ast)
        print("var, expr = ", var)
        if var == target_parameter:
            if '"' in expr or "'" in expr:
                target_str = expr
            if is_call_statement(body_full_line_original):
                break
        current_counter += line_size

    return target_str


def find_backward_content_str(target_parameter, start_line_num, my_parsed_obj):
    file_dir = my_parsed_obj.get_file_dir()
    body, body_start_line_num, body_end_line_num = method_func_body_extraction(start_line_num, file_dir)
    target_str = find_target_str_same_scope(body_start_line_num, start_line_num, my_parsed_obj, target_parameter)
    if target_str is None:
        print("never been mentioned...check the init or setup method")
        class_name = get_current_method_class_name(body_start_line_num, my_parsed_obj)
        if class_name is not None:
            # print("check init or setup...")
            init_setup_body_list = find_init_setup_body(class_name, my_parsed_obj)
            if init_setup_body_list is not None:
                for body_statement in init_setup_body_list:
                    if is_call_statement(body_statement):
                        break
                    var, expr = get_left_right(body_statement)
                    if var == target_parameter:
                        if '"' in expr or "'" in expr:
                            target_str = expr
                        break
        if target_str is None:
            ''' check for global vars'''
            print("check for global now..")
            global_statement_list = build_global_statement_list(my_parsed_obj)
            for global_statement, global_statement_line_num in global_statement_list:
                global_ast_statement, global_statement_start_line_number, global_statement_end_line_number, mode = extract_full_statement(global_statement_line_num, my_parsed_obj)
                if global_ast_statement is None:
                    continue
                if is_call_statement(global_ast_statement):
                    continue
                var, expr = get_left_right(global_ast_statement)
                if var == target_parameter:
                    if '"' in expr or "'" in expr:
                        target_str = expr
    return target_str


def generate_results(all_candidate_list, my_parsed_obj, sheet_dict):
    result_list = list()
    for ast_statement, full_line_original_statement, start_line_num, end_line_num in all_candidate_list:
        parameter_dict = build_line_parameter_dict(ast_statement)
        print("doing ast statement = ", ast_statement)
        print("full_line_original_statement = ", full_line_original_statement)
        method_call_object_name, pure_call_name = analysis_call_statement(full_line_original_statement)
        for key_statement in dict(parameter_dict):
            parameter_list = parameter_dict[key_statement]
            is_contain_msg_indicator_result, right_content = is_contain_msg_indicator(parameter_list)
            if is_contain_msg_indicator_result:
                print('contain msg indicator')
                if '.format' in right_content or '.join' in right_content:
                    break
                if '"' in right_content or "'" in right_content:
                    result_list.append((ast_statement, start_line_num, end_line_num, right_content))
                    break
                else:
                    trace_str_result = find_backward_content_str(right_content, start_line_num, my_parsed_obj)
                    result_list.append((ast_statement, start_line_num, end_line_num, trace_str_result))
                    break
            else:
                parameter_len = len(parameter_list)
                desire_parameter_index = int(sheet_dict[pure_call_name])
                print('desire_parameter_index = ', desire_parameter_index)
                print("parameter list = ", parameter_list)
                print("len parameter list = ", len(parameter_list))
                if desire_parameter_index == -1 or parameter_len < desire_parameter_index:
                    print("parameter len < desire parameter index")
                    result_list.append((ast_statement, start_line_num, end_line_num, None))
                    break
                else:
                    target_parameter = parameter_list[desire_parameter_index-1]
                    print("target parameter = ", target_parameter)
                    if '"' in target_parameter or "'" in target_parameter:
                        if '.format' in target_parameter or '.join' in target_parameter:
                            result_list.append((ast_statement, start_line_num, end_line_num, None))
                            break
                        trace_str_result = target_parameter
                    else:
                        trace_str_result = find_backward_content_str(target_parameter, start_line_num, my_parsed_obj)
                    print("trace str result = ", trace_str_result)
                    if '.format' in trace_str_result or '.join' in trace_str_result:
                        result_list.append((ast_statement, start_line_num, end_line_num, None))
                        break
                    result_list.append((ast_statement, start_line_num, end_line_num, trace_str_result))
                    break
    return result_list


def msg_variable_extraction(file_dir, statement_arg_index_dir):
    file_dir = test_file_dir
    statement_arg_index_dir = 'statement_arg_index_file - Sheet1.csv'
    my_parsed_obj = MyParsedObject(file_dir)
    sheet_dict = load_sheet(statement_arg_index_dir)
    all_candidate_list = find_all_candidates(my_parsed_obj)
    print("all candidate list = ", all_candidate_list)
    result_list = generate_results(all_candidate_list, my_parsed_obj, sheet_dict)
    print('all candidate list = ', all_candidate_list)
    print("\n\n")
    for candidate in result_list:
        print("candidate[0] = ", candidate[0])
        print("candidate[1:] = ", candidate[1:])
        print("================================")