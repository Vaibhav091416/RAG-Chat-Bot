from logger import logging
import sys 

def error_message_details(error,error_details:sys):
    _,_,exc_tb=error_details.exc_info()

    filename=exc_tb.tb_frame.f_code.co_name
    line_no=exc_tb.tb_lineno

    error_msg=f'There was an error in the file: {filename},line no: {line_no}\nstr({error})'
    return error_msg
    

class CustomException(Exception):
    def __init__(self,error_message,error_details:sys):
        super().__init__()
        self.error_message=error_message_details(error_message,error_details)
        return error_message
    
    def __str__(self):
        return self.error_message