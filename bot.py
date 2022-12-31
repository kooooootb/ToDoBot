import logging
import os
from datetime import datetime

import telegram.error
from telegram import __version__ as tg_ver

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(f'install with pip install -U --pre')

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO,
    filename=os.path.join(os.path.dirname(__file__), 'bot{}.log'.format(datetime.today().strftime('%Y-%m-%d:%H-%M'))),
    filemode='w'
)

(ADD_TASK) = range(1)


async def entry_point(update: Update, _) -> int:
    await update.message.reply_text(text='You can now add your tasks, simply send them in chat')
    return ADD_TASK


async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f'{update.effective_user} edited their tasks')
    message = update.message
    chat_id = message.chat_id
    text = message.text
    await message.delete()

    bot = context.bot
    chat = await bot.get_chat(chat_id)

    tasks_list = []
    tasks_string = ""
    if chat.pinned_message is not None:
        pinned_message = chat.pinned_message
        tasks_string = pinned_message.text
        tasks_list = tasks_string.splitlines()
        await pinned_message.delete()

        if text in tasks_list:
            tasks_list.remove(text)

            if not tasks_list:
                return

            tasks_string = '\n'.join(tasks_list)
        else:
            tasks_list.append(text)
            tasks_string = tasks_string + '\n' + text

        tasks_list = [[line] for line in tasks_list]

        # Planned to edit current pinned message but bot somehow couldn't edit previous pinned message and there is
        # no way to set reply markup (it deletes with message)
        # await bot.edit_message_text(chat_id=chat_id, message_id=pinned_message.id, text=tasks_string)
        # message = await bot.send_message(chat_id=chat_id, reply_markup=ReplyKeyboardMarkup(
        #     tasks_list, one_time_keyboard=True, input_field_placeholder='Choose task to delete:'
        # ))
        # await message.delete()

        # Resend pinned message (drawback: history of pinnings is getting bigger)

        message = await bot.send_message(chat_id=chat_id, text=tasks_string, reply_markup=ReplyKeyboardMarkup(
            tasks_list, one_time_keyboard=True, input_field_placeholder='Choose task to delete:'
        ))
        await bot.pin_chat_message(chat_id=chat_id, message_id=message.id, disable_notification=True)
    else:
        tasks_list.append([text])
        tasks_string += '\n' + text

        # Set pinned message
        message = await bot.send_message(chat_id=chat_id, text=tasks_string, reply_markup=ReplyKeyboardMarkup(
            tasks_list, one_time_keyboard=True, input_field_placeholder='Choose task to delete:'
        ))

        await bot.pin_chat_message(chat_id=chat_id, message_id=message.id, disable_notification=True)

    return ADD_TASK


async def done(update: Update, _) -> int:
    await update.message.reply_text('Что-то пошло не так')
    return ConversationHandler.END


def main() -> None:
    """Run bot."""
    try:
        token = os.environ['TODOBOT_KEY']
    except KeyError as e:
        raise RuntimeError("Need TODOBOT_KEY in environment") from e

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    application.add_handler(MessageHandler(filters.TEXT, add_task))

    application.run_polling()


if __name__ == "__main__":
    main()
