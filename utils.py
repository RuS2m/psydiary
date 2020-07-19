import logging
from typing import Tuple, List
from telegram import InlineKeyboardButton, Bot, InlineKeyboardMarkup

def get_logger():
    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    return logger

"""
Parse list of lists buttons to list of buttons texts and list of buttons callbacks
"""
def parse_inline_keyboard(custom_keyboard: List[List[InlineKeyboardButton]]) -> Tuple[List[List[str]], List[List[str]]]:
    buttons_texts = [[button.text for button in buttons_list] for buttons_list in custom_keyboard]
    buttons_callbacks = [[button.callback_data for button in buttons_list] for buttons_list in custom_keyboard]
    print(buttons_texts)
    print(buttons_callbacks)
    return buttons_texts, buttons_callbacks


"""
Build inline keyboard from list of buttons texts and buttons callbacks
"""
def inline_keyboard_from_buttons_lists(buttons_texts: List[List[str]], buttons_callbacks: List[List[str]]) -> List[
    List[InlineKeyboardButton]]:
    return [[InlineKeyboardButton(text, callback_data=callback) for text, callback in zip(texts, callbacks)]
            for texts, callbacks in zip(buttons_texts, buttons_callbacks)]