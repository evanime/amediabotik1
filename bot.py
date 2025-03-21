import telebot
import requests
from bs4 import BeautifulSoup
import time
import threading

# Токен вашего бота
token = "8083884181:AAE5QThb0_pPUIhhw5qtQjnqsjZ8rl28n4g"
bot = telebot.TeleBot(token)

# Словарь для хранения состояния отслеживания для каждого пользователя
user_states = {}

# Функция для парсинга данных с сайта
def parse_anime():
    URL = "https://amedia.lol/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 YaBrowser/25.2.0.0 Safari/537.36'
    }

    try:
        # Выполняем запрос к странице
        page = requests.get(URL, headers=headers)
        page.raise_for_status()  # Проверяем, что запрос успешен (статус код 200)

        # Парсим содержимое страницы
        soup = BeautifulSoup(page.content, "html.parser")

        # Извлекаем список аниме
        anime_list = soup.find_all("a", class_="ftop-item")
        result = []

        for anime in anime_list:
            # Название аниме
            title = anime.find("div", class_="ftop-item__title").text.strip()

            # Ссылка на страницу аниме
            link = URL + anime["href"].lstrip("/")

            # Дата и время добавления
            date = anime.find("div", class_="ftop-item__meta").text.strip()

            # Номер серии
            episode = anime.find("div", class_="animseri").text.strip().replace("серия", "").strip()

            # Формируем строку с информацией
            anime_info = (
                f"🎬 <b>Название:</b> {title}\n"
                f"🔗 <b>Ссылка:</b> <a href='{link}'>КЛИК</a>\n"
                f"📅 <b>Дата:</b> {date}\n"
                f"📺 <b>Серия:</b> {episode} серия\n"
                f"────────────────────"
            )
            result.append((anime_info, date))  # Сохраняем информацию и дату

        return result

    except requests.exceptions.RequestException as e:
        return [f"Ошибка при запросе к странице: {e}"]
    except Exception as e:
        return [f"Произошла ошибка: {e}"]

# Функция для проверки обновлений
def check_for_updates(chat_id):
    last_updates = []
    first_run = True  # Флаг для первого запуска

    while user_states.get(chat_id, False):  # Проверяем, что отслеживание включено для этого пользователя
        new_updates = parse_anime()
        if new_updates != last_updates:
            if first_run:
                # При первом запуске отправляем сообщение
                bot.send_message(chat_id, "Теперь тайтлы отслеживаются🔥")
                first_run = False
            else:
                # Находим новые посты
                new_posts = [post for post, date in new_updates if post not in last_updates and "Новая серия в" not in date]
                if new_posts:
                    # Публикуем только первый новый пост
                    bot.send_message(chat_id, new_posts[0], parse_mode="HTML")
            last_updates = new_updates
        time.sleep(30)  # Проверка каждые 30 секунд

# Обработчик команды /start
@bot.message_handler(commands=["start"])
def handle_start(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
    btn_ongoing = telebot.types.KeyboardButton("Начать отслеживание")
    btn_stop = telebot.types.KeyboardButton("Остановить отслеживание")
    btn_anime = telebot.types.KeyboardButton("Аниме")
    btn_today = telebot.types.KeyboardButton("Сегодня выйдет")
    markup.add(btn_ongoing, btn_stop, btn_anime, btn_today)
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите команду:", reply_markup=markup)

# Обработчик команды /ongoing
@bot.message_handler(func=lambda message: message.text == "Начать отслеживание")
def handle_ongoing(message):
    chat_id = message.chat.id
    if not user_states.get(chat_id, False):
        user_states[chat_id] = True
        bot.send_message(chat_id, "Запускаю слежение за новыми публикациями...")
        threading.Thread(target=check_for_updates, args=(chat_id,)).start()
    else:
        bot.send_message(chat_id, "Слежение за публикациями уже запущено.")

# Обработчик команды /stop
@bot.message_handler(func=lambda message: message.text == "Остановить отслеживание")
def handle_stop(message):
    chat_id = message.chat.id
    if user_states.get(chat_id, False):
        user_states[chat_id] = False
        bot.send_message(chat_id, "Слежение за публикациями остановлено.")
    else:
        bot.send_message(chat_id, "Слежение за публикациями уже остановлено.")

# Обработчик команды /anime
@bot.message_handler(func=lambda message: message.text == "Аниме")
def handle_anime(message):
    bot.send_message(message.chat.id, "Секунду, собираю данные...")
    anime_data = parse_anime()  # Получаем данные с сайта

    if anime_data:
        # Отправляем только вышедшие тайтлы
        posts = [post for post, date in anime_data if "Новая серия в" not in date]
        output_message = "\n\n".join(posts)
        bot.send_message(message.chat.id, output_message, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "Не удалось получить данные. Попробуйте позже.")

# Обработчик команды "Сегодня выйдет"
@bot.message_handler(func=lambda message: message.text == "Сегодня выйдет")
def handle_today(message):
    bot.send_message(message.chat.id, "Секунду, собираю данные...")
    anime_data = parse_anime()  # Получаем данные с сайта

    if anime_data:
        # Отправляем только тайтлы, которые выйдут сегодня
        posts = [post for post, date in anime_data if "Новая серия в" in date]
        output_message = "\n\n".join(posts)
        bot.send_message(message.chat.id, output_message, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "Не удалось получить данные. Попробуйте позже.")

# Запуск бота
bot.polling(none_stop=True)