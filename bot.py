import calendar
import datetime
import os
import sys
import logging
import matplotlib
import matplotlib.pyplot as plt
from sqlalchemy.orm import Session
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, Bot
from telegram.ext import Updater, CallbackQueryHandler, Filters, MessageHandler

from config import BotConfig
from db import engine, Base
from models import *

matplotlib.use('agg')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

HELLO_MESSAGE = 'Hello, here instruction how to use this bot:\n' \
               '/note -- add note in ABC model format, where all three parts separated from each other with # sign\n' \
               '/calendar -- show calendar, representing all notes\n' \
               '/rate -- rate your self-esteem\n' \
               '/show -- shows self-esteem graphs\n'
START_COMMAND = "/start"
RATE_COMMAND = "/rate"
SHOW_COMMAND = "/show"
NOTE_COMMAND = "/note"
CALENDAR_COMMAND = "/calendar"
QUERY_SEPARATOR_SYMBOL = ";"
IGNORE_ACTION = "IGNORE"
CALENDAR_ACTION = "CALENDAR"
PREV_MONTH_ACTION = "PREV-MONTH"
NEXT_MONTH_ACTION = "NEXT-MONTH"
DAY_ACTION = "DAY"
NOTES_ACTION = "NOTES"
REFLECT_ACTION = "REFLECT"
CALENDAR_ACTIONS=[CALENDAR_ACTION, PREV_MONTH_ACTION, NEXT_MONTH_ACTION, DAY_ACTION]

def handle_message(bot: Bot, update: Update):
    chat_id = update.message.chat.id
    message_text = update.message.text
    if START_COMMAND in message_text:
        bot.send_message(chat_id=chat_id, text=HELLO_MESSAGE)
    elif RATE_COMMAND in message_text:
        rate_handler(bot, chat_id, message_text)
    elif SHOW_COMMAND in message_text:
        show_handler(bot, chat_id)
    elif NOTE_COMMAND in message_text:
        note_handler(bot, chat_id, message_text)
    elif CALENDAR_COMMAND in message_text:
        bot.send_message(chat_id, text="Select date:", reply_markup=create_calendar(chat_id=chat_id))
    else:
        reflect_needed, answer_info = is_answer_needed(chat_id, "REFLECT")
        if reflect_needed:
            reflection_answer(bot, message_text, chat_id, answer_info)


def inline_handler(bot,update):
    chat_id = update.effective_chat['id']
    query = update.callback_query
    action = query.data.split(QUERY_SEPARATOR_SYMBOL)[0]
    if action == IGNORE_ACTION:
        bot.answer_callback_query(callback_query_id=query.id)
    if action == DAY_ACTION:
        (action, year, month, day) = separate_callback_data(query.data)
        date = datetime.datetime(int(year), int(month), int(day))
        text, reply_keyboard = note_with_keyboard_on_page(chat_id, date, 0)
        bot.edit_message_text(text=text,
                         chat_id=query.message.chat_id,
                         reply_markup=reply_keyboard,
                         message_id=query.message.message_id,
                         parse_mode='HTML')
    elif action == PREV_MONTH_ACTION:
        (action, year, month, day) = separate_callback_data(query.data)
        date = datetime.datetime(int(year), int(month), 1)
        pre = date - datetime.timedelta(days=1)
        bot.edit_message_text(text=query.message.text,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=create_calendar(int(pre.year), int(pre.month), query.message.chat_id))
    elif action == NEXT_MONTH_ACTION:
        (action, year, month, day) = separate_callback_data(query.data)
        date = datetime.datetime(int(year), int(month), 1)
        ne = date + datetime.timedelta(days=31)
        bot.edit_message_text(text=query.message.text,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=create_calendar(int(ne.year), int(ne.month), query.message.chat_id))
    elif action == CALENDAR_ACTION:
        (action, year, month, day) = separate_callback_data(query.data)
        bot.edit_message_text(text="Select date:",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=create_calendar(int(year), int(month), query.message.chat_id))
    elif action == NOTES_ACTION:
        (action, page, year, month, day) = separate_callback_data(query.data)
        date = datetime.datetime(int(year), int(month), int(day))
        text, reply_keyboard = note_with_keyboard_on_page(chat_id, date, int(page))
        bot.edit_message_text(text=text,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=reply_keyboard,
                              parse_mode='HTML')
    elif action == REFLECT_ACTION:
        (action, note_id) = separate_callback_data(query.data)
        answer_need_switch(chat_id, "REFLECT", str(note_id))
        bot.edit_message_text(text="Write your reflection parts (B1, C1), separated by '#'",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
    else:
        bot.answer_callback_query(callback_query_id=query.id, text="Something went wrong!")
        # print("something triggered, but nothing happened: %s" % action)


def rate_handler(bot: Bot, chat_id: int, message: str):
    rating = parse_command_argument(message, RATE_COMMAND)
    if (not rating) or (not rating.isdigit()):
        bot.send_message(chat_id, "Sorry, you were't provided rating :(")
    else:
        rating = int(rating)
        if is_rate_exist(chat_id):
            bot.send_message(chat_id, "Sorry, you already rated your self-esteem today :(")
        else:
            save_rate(chat_id, rating)
            bot.send_message(chat_id, "Rating was successfully send")


def show_handler(bot: Bot, chat_id: int):
    r = get_rates(chat_id)
    r = r[-30:]
    d = datetime.date.today()

    with plt.style.context('Solarize_Light2'):
        fig, ax = plt.subplots()
        events = [re.datetime for re in r]
        readings = [re.rate for re in r]
        ax.plot(events, readings, 'k-o')
        ax.set_ylim([-10, 10])
        month = ""
        if (d.month > 10):
            month = "%s" % d.month
        else:
            month = "0%s" % d.month
        title = "Self-esteem ratings for moth until %s.%s" % (month, d.year)
        ax.set_title(title, family="monospace", pad=20)
        fig.autofmt_xdate()
    fig = "self-esteem%s.png" % chat_id
    plt.savefig(fig)
    bot.send_photo(chat_id=chat_id, photo=open(fig, 'rb'))
    os.remove(fig)


def note_handler(bot: Bot, chat_id: int, message: str):
    abc = parse_command_argument(message, NOTE_COMMAND).split("#")
    if len(abc) < 3:
        bot.send_message(chat_id, "Something went wrong, please provide text, spaced with two '#' signs :(")
    else:
        a = abc[0]
        b = abc[1]
        c = abc[2]
        save_note(chat_id, a, b, c)
        bot.send_message(chat_id, "Note was successfully send")


def reflection_answer(bot: Bot, message: str, chat_id: int, answer_info: str):
    b1c1 = message.split("#")
    note_id = int(answer_info)
    if len(b1c1) < 2:
        bot.send_message("Something went wrong, please provide text, spaced with '#' signs :(")
    else:
        b1 = b1c1[0]
        c1 = b1c1[1]
        reflect_on_note(note_id, b1, c1)
        answer_need_switch(chat_id, "REFLECT", "")
        bot.send_message(chat_id, "Reflection note was successfully send")


def note_with_keyboard_on_page(chat_id, date, page_number):
    notes = get_notes(chat_id, date)
    if notes is None or len(notes) == 0:
        html_text = "<b>%s</b>" % date.strftime("%d/%m/%Y")
        return html_text, InlineKeyboardMarkup(
            [[InlineKeyboardButton("🗓️", callback_data=create_callback_data(CALENDAR_ACTION, date.year, date.month, date.day))]]
        )
    else:
        note = notes[page_number]
        html_text="<b>%s</b>" % date.strftime("%d/%m/%Y")
        if len(notes) > page_number:
            html_text = "<b>%s</b>\n\n %s" % (date.strftime("%d/%m/%Y"), str(note))
        keyboard = []
        row = []
        if page_number > 0:
            row.append(InlineKeyboardButton("<", callback_data=create_callback_data(NOTES_ACTION, page_number - 1, date.year, date.month, date.day)))
        if len(notes) > page_number + 1:
            row.append(
                InlineKeyboardButton(">", callback_data=create_callback_data(NOTES_ACTION, page_number + 1, date.year, date.month, date.day))
            )
        keyboard.append(row)
        row = []
        row.append(
            InlineKeyboardButton("🗓️", callback_data=create_callback_data(CALENDAR_ACTION, date.year, date.month, date.day)))
        if not note.is_reflected:
            row.append(
                InlineKeyboardButton("reflect", callback_data=create_callback_data(REFLECT_ACTION, note.note_id)))
        keyboard.append(row)
        reply_keyboard = InlineKeyboardMarkup(keyboard)
        return html_text, reply_keyboard


def create_calendar(year=None,month=None,chat_id=None):
    now = datetime.datetime.now()
    if year == None: year = now.year
    if month == None: month = now.month
    data_ignore = create_callback_data(IGNORE_ACTION, year, month, 0)
    keyboard = []
    keyboard.append([InlineKeyboardButton(calendar.month_name[month]+" "+str(year),callback_data=data_ignore)])

    my_calendar = calendar.monthcalendar(year, month)
    number_of_days = 0
    for week in my_calendar:
        for day in week:
            if day != 0:
                number_of_days+=1
    notes = get_last_notes_existence_since_date(chat_id, datetime.date(year, month, number_of_days), number_of_days)
    note_dates = [ note.note_date for note in notes ]
    for week in range(len(my_calendar)):
        row=[]
        for day in range(len(my_calendar[week])):
            day_number = my_calendar[week][day]
            if(day_number==0):
                row.append(InlineKeyboardButton(" ",callback_data=data_ignore))
            else:
                button_name = str(day_number)
                if datetime.date(year, month, day_number) in note_dates:
                    button_name = "📓"
                if int(day_number) == now.day and month == now.month and year == now.year:
                    button_name = "☘️"
                row.append(InlineKeyboardButton(button_name,callback_data=create_callback_data(DAY_ACTION,year,month,day_number)))
        keyboard.append(row)
    row=[
        InlineKeyboardButton("<",callback_data=create_callback_data(PREV_MONTH_ACTION,year,month,day_number)),
        InlineKeyboardButton(" ",callback_data=data_ignore),
        InlineKeyboardButton(">",callback_data=create_callback_data(NEXT_MONTH_ACTION,year,month,day_number))]
    keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def save_rate(chat_id: int, rate: int):
    date = datetime.date.today()
    session = Session(engine)
    session.execute(
        "INSERT INTO rates(chat_id, date_time, rate) SELECT :chat_id, :date, :rate",
        {"chat_id": chat_id, "rate": rate, "date": date}
    )
    session.commit()
    session.close()


def is_rate_exist(chat_id: int):
    date = datetime.date.today()
    session = Session(engine)
    rs = session.execute(
        "SELECT COUNT(*) FROM rates WHERE chat_id = :chat_id AND date_time > :date-interval '1 day'",
        {"chat_id": chat_id, "date": date}
    )
    session.commit()
    session.close()
    rate_num = rs.first()[0]
    is_exist = rate_num > 0
    return is_exist


def get_rates(chat_id: int):
    session = Session(engine)
    answer = []
    rs = session.execute(
        "SELECT rate, date_time FROM rates WHERE chat_id = :chat_id ORDER BY date_time ",
        { "chat_id": chat_id }
    )
    for row in rs:
        answer.append(RatingEvent(int(row[0]), row[1]))
    session.commit()
    session.close()
    return answer


def save_note(chat_id: int, a: str, b: str, c: str):
    session1 = Session(engine)
    rs1 = session1.execute("SELECT note_id FROM diary ORDER BY note_id DESC LIMIT 1")
    session1.commit()
    session1.close()
    rate_num = rs1.first()
    max_note_id = 1
    if (rate_num is not None) and len(rate_num) != 0 and (rate_num[0]) and (rate_num[0] > 0):
        max_note_id = rate_num[0] + 1
    date_time = datetime.datetime.now()
    session2 = Session(engine)
    session2.execute(
        "INSERT INTO diary(note_id, chat_id, date_time, a, b, c, is_reflected) SELECT :note_id, :chat_id, :date_time, :a, :b, :c, 'f'",
        {"note_id": max_note_id, "chat_id": chat_id, "a": a, "b": b, "c": c, "date_time": date_time}
    )
    session2.commit()
    session2.close()


def get_last_notes_existence_since_date(chat_id: int, date, n):
    session = Session(engine)
    rs = session.execute(
        "WITH date_grouped AS ("
        "SELECT date_time::timestamp::date AS date, COUNT(a) FROM diary WHERE chat_id = :chat_id GROUP BY date"
        ") SELECT * FROM date_grouped "
        "WHERE date < :date "
        "ORDER BY date "
        "LIMIT :n",
        {"chat_id": chat_id, "date": date, "n": n}
    )
    answer = []
    for row in rs:
        answer.append(NoteExistence(row[0], row[1]))
    session.commit()
    session.close()
    return answer


def answer_need_switch(chat_id: int, answer_type: str, additional_info: str):
    session1 = Session(engine)
    rs1 = session1.execute("SELECT COUNT(*) FROM answer_needs WHERE chat_id = :chat_id AND answer_type = :answer_type AND is_answer_needed = 't' LIMIT 1",
                           {"chat_id": chat_id, "answer_type": answer_type})
    rs_number = int(rs1.first()[0])
    session1.commit()
    session1.close()
    session2 = Session(engine)
    if rs_number > 0:
        session2.execute(
            "DELETE FROM answer_needs WHERE chat_id = :chat_id AND answer_type = :answer_type AND is_answer_needed = 't'",
            {"chat_id": chat_id, "answer_type": answer_type, "additional_info": additional_info}
        )
    else:
        session2.execute(
            "INSERT INTO answer_needs(chat_id, answer_type, additional_info, is_answer_needed) SELECT :chat_id, :answer_type, :additional_info, 't'",
            {"chat_id": chat_id, "answer_type": answer_type, "additional_info": additional_info}
        )
    session2.commit()
    session2.close()


def is_answer_needed(chat_id: int, answer_type: str):
    session = Session(engine)
    if not answer_type:
        rs = session.execute("SELECT is_answer_needed, additional_info FROM answer_needs WHERE chat_id = :chat_id", {"chat_id": chat_id})
    else:
        rs = session.execute("SELECT is_answer_needed, additional_info FROM answer_needs WHERE chat_id = :chat_id AND answer_type = :answer_type",
                             {"chat_id": chat_id, "answer_type": answer_type})
    row = rs.first()
    if (row is None) or (len(row) < 2):
        session.commit()
        session.close()
        return False, None
    else:
        answer_need = bool(row[0])
        text = row[1]
        session.commit()
        session.close()
        return answer_need, text


def reflect_on_note(note_id: int, b1: str, c1: str):
    session = Session(engine)
    session.execute("UPDATE diary SET(b1, c1, is_reflected) = (:b1, :c1, 't') WHERE note_id = :note_id",
                             {"note_id": note_id, "b1": b1, "c1": c1})
    session.commit()
    session.close()


def get_notes(chat_id: int, date):
    session = Session(engine)
    rs = session.execute(
        "SELECT note_id, a, b, c, b1, c1, is_reflected FROM diary "
        "WHERE chat_id = :chat_id AND "
        "(date_time > :date AND date_time < :date+interval '1 days')",
        {"chat_id": chat_id, "date": date}
    )
    answer = []
    for row in rs:
        print(row)
        answer.append(Note(int(row[0]), row[1], row[2], row[3], row[4], row[5], bool(row[6])))
    session.commit()
    session.close()
    return answer


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def parse_command_argument(message: str, command: str):
    return message.split(command)[1].strip()

def create_callback_data(*args):
    return QUERY_SEPARATOR_SYMBOL.join([ str(arg) for arg in args ])

def separate_callback_data(data: str):
    return data.split(QUERY_SEPARATOR_SYMBOL)

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    updater = Updater(token=BotConfig.token)
    dispatcher = updater.dispatcher
    try:
        dispatcher.add_handler(MessageHandler(Filters.text | Filters.command, handle_message))
        dispatcher.add_handler(CallbackQueryHandler(inline_handler))
        dispatcher.add_error_handler(error)
        updater.start_polling(allowed_updates=True)
        updater.idle()
    except KeyboardInterrupt:
        print("omg")
        sys.exit(0)