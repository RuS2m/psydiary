from db import engine, Base
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, Bot
from telegram.ext import Updater, CommandHandler, run_async
from utils import get_logger
from sqlalchemy.orm import Session
from config import BotConfig
import datetime
import matplotlib
import matplotlib.pyplot as plt
from models import *
import sys

matplotlib.use('agg')
logger = get_logger()

@run_async
def start(bot: Bot, update: Update):
    chat_id = update.message.chat.id
    text = 'Hello, how to use it:\n' \
           '/note -- (TBD) add note\n' \
           '/rate -- (TBD) rate your self-esteem\n' \
           '/show -- (TBD) shows self-esteem graphs\n'
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
    fig = "self-esteem%s-%s-%s.png" % (d.year, d.month, d.day)
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


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    updater = Updater(token=BotConfig.token)
    dispatcher = updater.dispatcher
    try:
        dispatcher.add_handler(CommandHandler(command='start', callback=start))
        dispatcher.add_handler(CommandHandler(command='rate', callback=rate))
        # dispatcher.add_handler(CommandHandler("rate", rate, pass_args=True))
        dispatcher.add_handler(CommandHandler(command='show', callback=show))
        dispatcher.add_error_handler(error)
        updater.start_polling(allowed_updates=True)
        updater.idle()
    except KeyboardInterrupt:
        print("omg")
        sys.exit(0)