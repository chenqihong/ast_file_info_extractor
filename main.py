import sys
from method_func_body_extraction_module import method_func_body_extraction
from class_name_extraction_module import class_name_extraction
from msg_variable_extraction_module import msg_variable_extraction

mode = sys.argv[1]
if mode == 'body_extraction':
    pass_line_num, pass_file_dir = sys.argv[2], sys.argv[3]
    method_func_body_extraction(pass_line_num, pass_file_dir)
elif mode == 'class_name_extraction':
    pass_file_dir = sys.argv[2]
    class_name_extraction(pass_file_dir)
elif mode == "msg_variable_extraction":
    pass_file_dir = sys.argv[2]
    msg_variable_extraction(pass_file_dir)