# ast_file_info_extractor

This tool can be used to extract different information for a given file.


Usage: Python3 main.py mode args

if mode == body_extraction:
    It takes the line number and the full directory of a python script, and returns the body of the method that contains this the desired line.

if mode == class_name_extraction:
    It takes the file_dir and returns the list of all defined class names in that file, empty list otherwise.

if mode == msg_variable_extraction:
    it takes the file dir, and statement_arg_index_dir and return the list of all assert calls and its msg.
