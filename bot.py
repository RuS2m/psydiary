from db import engine, Base
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, Bot, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, run_async, CallbackQueryHandler
from utils import get_logger
from sqlalchemy.orm import Session
from config import BotConfig
import datetime
import matplotlib
import matplotlib.pyplot as plt
from models import *
import sys
import calendar

matplotlib.use('agg')
logger = get_logger()

@run_async
def start(bot: Bot, update: Update):
    chat_id = update.message.chat.id
    text = 'Hello, here instruction how to use this bot:\n' \
           '/note -- add note\n' \
           '/calendar -- show calendar, representing all notes\n' \
           '/rate -- rate your self-esteem\n' \
           '/show -- shows self-esteem graphs\n'
    bot.send_message(chat_id=chat_id, text=text)


@run_async
def rate(bot: Bot, update: Update):
    chat_id = update.message.chat.id
    arg = update.message.__dict__['text'].split('/rate')[1]
    if not arg:
        update.message.reply_text("Sorry, you were't provided rating :(")
    else:
        rating = int(arg)
        if is_rate_exist(chat_id):
            update.message.reply_text("Sorry, you already rated your self-esteem today :(")
        else:
            save_rate(chat_id, rating)
            update.message.reply_text("Rating was successfully send")

@run_async
def show(bot: Bot, update: Update):
    chat_id = update.message.chat.id
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


def save_rate(chat_id: int, rate: int):
    session = Session(engine)
    session.execute(
        "INSERT INTO rates(chat_id, date_time, rate) SELECT :chat_id, now(), :rate",
        {"chat_id": chat_id, "rate": rate}
    )
    session.commit()
    session.close()


def is_rate_exist(chat_id: int):
    session = Session(engine)
    rs = session.execute(
        "SELECT COUNT(*) FROM rates WHERE chat_id = :chat_id AND date_time > now()-interval '1 day'",
        {"chat_id": chat_id}
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


@run_async
def note(bot: Bot, update: Update):
    chat_id = update.message.chat.id
    abc = update.message.__dict__['text'].split('/note')[1].split("#")
    if len(abc) < 3:
        update.message.reply_text("Something went wrong, please provide text, spaced with two '#' signs :(")
    else:
        a = abc[0]
        b = abc[1]
        c = abc[2]
        save_note(chat_id, a, b, c)
        update.message.reply_text("Note was successfully send")


@run_async
def calendar_handler(bot: Bot, update: Update):
    chat_id = update.message.chat.id
    update.message.reply_text("Select date:", reply_markup=create_calendar(chat_id=chat_id))

@run_async
def inline_handler(bot,update):
    chat_id = update.effective_chat['id']
    selected,date = process_calendar_selection(bot, update)
    if selected:
        text, reply_keyboard = note_with_keyboard_on_page(chat_id, date, 0)
        bot.send_message(chat_id=update.callback_query.from_user.id,
                        text=text,
                        reply_markup=reply_keyboard,
                        parse_mode='HTML')


@run_async
def notes_inline_handler(bot,update):
    chat_id = update.effective_chat['id']
    query = update.callback_query
    (action, page, year, month, day) = separate_callback_data(query.data)
    date = datetime.datetime(int(year), int(month), int(day))
    text, reply_keyboard = note_with_keyboard_on_page(chat_id, date, int(page))
    bot.edit_message_text(text=text,
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          reply_markup=reply_keyboard,
                          parse_mode='HTML')


def note_with_keyboard_on_page(chat_id, date, page_number):
    notes = get_notes(chat_id, date)
    strnotes = [str(note) for note in notes]
    html_text="<b>%s</b>" % date.strftime("%d/%m/%Y")
    if len(strnotes) > page_number:
        html_text = strnotes[page_number]
        html_text = "<b>%s</b>\n\n %s" % (date.strftime("%d/%m/%Y"), html_text)
    keyboard = []
    row = []
    row.append(
        InlineKeyboardButton("🗓️", callback_data=create_callback_data("CALENDAR", date.year, date.month, date.day)))
    keyboard.append(row)
    row = []
    if page_number > 0:
        row.append(InlineKeyboardButton("<", callback_data="n_NOTES;%s;%s;%s;%s" % (page_number - 1, date.year, date.month, date.day)))
    if len(notes) > page_number + 1:
        row.append(
            InlineKeyboardButton(">", callback_data="n_NOTES;%s;%s;%s;%s" % (page_number + 1, date.year, date.month, date.day))
        )
    keyboard.append(row)
    reply_keyboard = InlineKeyboardMarkup(keyboard)
    return html_text, reply_keyboard



def create_callback_data(action,year,month,day):
    return "c_%s" % ";".join([action,str(year),str(month),str(day)])

def separate_callback_data(data):
    return data.split("_")[1].split(";")


def create_calendar(year=None,month=None,chat_id=None):
    now = datetime.datetime.now()
    if year == None: year = now.year
    if month == None: month = now.month
    data_ignore = create_callback_data("IGNORE", year, month, 0)
    keyboard = []
    #First row - Month and Year
    row=[]
    row.append(InlineKeyboardButton(calendar.month_name[month]+" "+str(year),callback_data=data_ignore))
    keyboard.append(row)

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
                row.append(InlineKeyboardButton(button_name,callback_data=create_callback_data("DAY",year,month,day_number)))
        keyboard.append(row)
    #Last row - Buttons
    row=[]
    row.append(InlineKeyboardButton("<",callback_data=create_callback_data("PREV-MONTH",year,month,day_number)))
    row.append(InlineKeyboardButton(" ",callback_data=data_ignore))
    row.append(InlineKeyboardButton(">",callback_data=create_callback_data("NEXT-MONTH",year,month,day_number)))
    keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def process_calendar_selection(bot,update):
    ret_data = (False,None)
    query = update.callback_query
    (action,year,month,day) = separate_callback_data(query.data)
    curr = datetime.datetime(int(year), int(month), 1)
    if action == "IGNORE":
        bot.answer_callback_query(callback_query_id= query.id)
    elif action == "DAY":
        bot.delete_message(chat_id=query.message.chat_id,message_id=query.message.message_id)
        ret_data = True,datetime.datetime(int(year),int(month),int(day))
    elif action == "PREV-MONTH":
        pre = curr - datetime.timedelta(days=1)
        bot.edit_message_text(text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=create_calendar(int(pre.year),int(pre.month), query.message.chat_id))
    elif action == "NEXT-MONTH":
        ne = curr + datetime.timedelta(days=31)
        bot.edit_message_text(text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=create_calendar(int(ne.year),int(ne.month), query.message.chat_id))
    elif action == "CALENDAR":
        bot.edit_message_text(text="Select date:",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=create_calendar(int(year),int(month), query.message.chat_id))
    else:
        bot.answer_callback_query(callback_query_id= query.id,text="Something went wrong!")
    return ret_data



def save_note(chat_id: int, a: str, b: str, c: str):
    session1 = Session(engine)
    rs1 = session1.execute("SELECT note_id FROM diary ORDER BY note_id DESC LIMIT 1")
    session1.commit()
    session1.close()
    rate_num = rs1.first()
    max_note_id = 1
    if (rate_num is not None) and len(rate_num) != 0 and (rate_num[0]) and (rate_num[0] > 0):
        max_note_id = rate_num[0]
    session2 = Session(engine)
    session2.execute(
        "INSERT INTO diary(note_id, chat_id, date_time, a, b, c, is_reflected) SELECT :note_id, :chat_id, now(), :a, :b, :c, 'f'",
        {"note_id": max_note_id, "chat_id": chat_id, "a": a, "b": b, "c": c}
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


def get_notes(chat_id: int, date):
    session = Session(engine)
    rs = session.execute(
        "SELECT note_id, a, b, c, b1, c1 FROM diary "
        "WHERE chat_id = :chat_id AND "
        "(date_time > :date-interval '12 hours' AND date_time < :date+interval '12 hours')",
        {"chat_id": chat_id, "date": date}
    )
    answer = []
    for row in rs:
        print(row)
        answer.append(Note(int(row[0]), row[1], row[2], row[3], row[4], row[5]))
    session.commit()
    session.close()
    return answer


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    updater = Updater(token=BotConfig.token)
    dispatcher = updater.dispatcher
    try:
        dispatcher.add_handler(CommandHandler(command='start', callback=start))
        dispatcher.add_handler(CommandHandler(command='note', callback=note))
        dispatcher.add_handler(CommandHandler(command='rate', callback=rate))
        dispatcher.add_handler(CommandHandler(command='show', callback=show))
        dispatcher.add_handler(CommandHandler(command='calendar', callback=calendar_handler))
        dispatcher.add_handler(CallbackQueryHandler(inline_handler, pattern="c_"))
        dispatcher.add_handler(CallbackQueryHandler(notes_inline_handler, pattern="n_"))
        dispatcher.add_error_handler(error)
        updater.start_polling(allowed_updates=True)
        updater.idle()
    except KeyboardInterrupt:
        print("omg")
        sys.exit(0)