import logging
from aiogram import Bot, Dispatcher, executor, types
from settings import API_TOKEN
from utils import (
    ChatData,
    clear_statistic,
    create_all,
    delete_poll,
    get_data_question,
    get_poll_data,
    get_statistic_string,
    get_topic_from_db,
    import_from_csv,
    save_poll,
    save_statistic,
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from constants import WELCOME_MSG, MEDIAPATH, KEYBOARD_BUTTONS


async def send_quiz(chat_id, quiz_data):
    """
    Функция отправки самого вопроса
    """
    questions_data = quiz_data["question"]
    question_text = (
        f"{questions_data.id}. {questions_data.text} \n"
        f" #{questions_data.topic.name}"
    )
    if questions_data.picture:
        photo = open(MEDIAPATH + questions_data.picture, "rb")
        await bot.send_photo(chat_id=chat_id, photo=photo)
    my_quiz = await bot.send_poll(
        chat_id=chat_id,
        question=question_text,
        options=quiz_data["answers"],
        type="quiz",
        correct_option_id=quiz_data["correct_answer_id"],
        is_anonymous=False,
    )
    save_poll(
        my_quiz["poll"]["id"],
        my_quiz["poll"]["correct_option_id"],
        questions_data.text,
        questions_data.topic.name,
    )


@dp.message_handler(
    commands=[
        "start",
    ]
)
async def send_welcome(message: types.Message):
    """
    Отправляем приветственное сообщение и формируем блок кнопок
    """
    msg = WELCOME_MSG.format(
        first_name=message.chat.first_name,
        last_name=message.chat.last_name,
    )

    greet_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for button_name in KEYBOARD_BUTTONS:
        greet_kb.add(KeyboardButton(button_name))
    await bot.send_message(message.chat.id, msg, reply_markup=greet_kb)


@dp.poll_answer_handler()
async def handle_poll_answer(quiz_answer):
    """
    Проверка ответа
    """
    quiz_answer_data = get_poll_data(quiz_answer["poll_id"])
    topic = quiz_answer_data.topic
    save_statistic(quiz_answer_data, quiz_answer)
    if not get_topic_from_db(topic):
        get_data_question()
    else:
        get_data_question(topic)
    delete_poll(quiz_answer["poll_id"])
    inline_btn_1 = InlineKeyboardButton(
        f"Давай!", callback_data=f"{topic}"
    )
    inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1)
    str_for_inline = f"Еще вопрос на тему {topic}"
    await bot.send_message(
        quiz_answer.user.id, str_for_inline, reply_markup=inline_kb1
    )


@dp.message_handler(
    commands=[
        "initbase",
    ]
)
async def init_base(message: types.Message):
    """
    Инициализация базы даннных
    создаются все таблица, собираются вопросы из db/questions.csv
    """
    message_text = message.text[1:]
    topic_in_database = get_topic_from_db(message_text)
    create_all()
    all_questions, imported_questions = import_from_csv("db/questions.csv")
    if not topic_in_database:
        await bot.send_message(
            message.chat.id,
            "База данных обновлена \n"
            f"Из файла прочитано {all_questions} \n"
            f"Импортировано {imported_questions}",
        )


@dp.message_handler(
    commands=[
        "statistic",
    ]
)
async def get_statistic(message: types.Message):
    """
    Запрос статистики пользователя, выдается в виде отформатированного текста
    """
    user_statistic = get_statistic_string(message)
    msg = f"Ваша статистика: \n" f"{user_statistic}" f""
    await bot.send_message(
        message.chat.id,
        msg,
    )


@dp.message_handler(
    commands=[
        "clearstat",
    ]
)
async def clearstat(message: types.Message):
    """
    Команда очистки статистики пользователя, который отправил команду
    """
    clear_statistic(message)
    msg = f"Ваша статистика очищена"
    await bot.send_message(
        message.chat.id,
        msg,
    )


@dp.message_handler()
async def send_question_message(message: types.Message):
    """
    Прослойка для отлова обычных сообщений и перенаправки на вопрос
    """
    chat = ChatData(
        message.chat.id,
        message.chat.first_name,
        message.chat.last_name,
        message.text[1:],
    )
    await send_question(chat)


@dp.callback_query_handler()
async def send_question_callback(message: types.CallbackQuery):
    """
    Прослойка для отлова коллбеков и перенаправки на вопрос
    """
    chat = ChatData(
        message["from"].id,
        message["from"].first_name,
        message["from"].last_name,
        message.data,
    )
    await send_question(chat)


async def send_question(chat_data):
    """
    Отправка вопроса
    """
    message_text = chat_data.data
    topic_in_database = get_topic_from_db(message_text)
    if not topic_in_database:
        await bot.send_message(
            chat_data.id,
            "Неверная команда",
        )
    else:
        user_name = f"{chat_data.first_name} {chat_data.last_name}"
        data_for_quiz = get_data_question(message_text, user_name)
        if data_for_quiz:
            await send_quiz(chat_data.id, data_for_quiz)
        else:
            await bot.send_message(
                chat_data.id,
                "Эта тема полностью пройдена",
            )


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
