import telebot
from telebot import types
import os
from dotenv import load_dotenv
from pymongo import MongoClient

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['Subjects']
    collection = db.subjects_for_users
    print('DB connected 📶')
except BaseException:
    print('MongoDB is not working ', BaseException)

load_dotenv()


is_prod = os.environ.get('TOKEN', None)
if is_prod:
    TOKEN = os.getenv('TOKEN')
    bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Список доступных комманд: \n'
                                      '/show - список всех тематик\n'
                                      '/add - добавление сайта или тематики\n'
                                      '/delete - удаление тематики\n'
                                      '/deleteSite - удаление сайта из тематики\n'
                                      '/look (Название тематики) - посмотреть список сайтов по данной тематике')


@bot.message_handler(commands=['deleteSite'])
def delete_site(message):
    msg = bot.send_message(message.chat.id, 'Выберите тематику для удаления сайта')
    show_all(message)
    bot.register_next_step_handler(msg, confirm_delete_site)


def confirm_delete_site(message):
    subject = message.text
    msg = bot.send_message(message.chat.id, 'Введите сайт для удаления')
    print('ААААААААААААААААААА')
    print(collection)
    query = {'subject': subject}
    for document in collection.find(query):
        print('АЛОООООООООООО')
        bot.send_message(message.chat.id, ', '.join(map(str, document['sites'])))
    bot.register_next_step_handler(msg, confirm_delete_site_forever, query)


def confirm_delete_site_forever(message, query):
    del_site = message.text
    del_site_query = {'$pull': {'sites': del_site}}
    collection.update_one(query, del_site_query)
    bot.send_message(message.chat.id, 'Сайт {0} удален.'.format(del_site))


@bot.message_handler(commands=['look'])
def show_sites_in_subject(message):
    subject = message.text
    split = ' '.join(subject.split()[1:])
    print(split)
    for document in collection.find({'subject': split}):
        bot.send_message(message.chat.id, ', '.join(map(str, document['sites'])))
        print('simple doc: ', document)
        print(document['sites'])


@bot.message_handler(commands=['show'])
def show_all(message):
    for document in collection.find():
        bot.send_message(message.chat.id, document['subject'])


@bot.message_handler(commands=['delete'])
def delete_subject(message):
    msg = bot.send_message(message.chat.id, 'Введите тематику для удаления:')
    show_all(message)
    bot.register_next_step_handler(msg, confirm_delete)


def confirm_delete(message):
    deleteSubject = message.text
    if collection.find_one({'subject': deleteSubject}) is not None:
        collection.delete_one({'subject': deleteSubject})
        bot.send_message(message.chat.id, 'Тематика {0} удалена.'.format(deleteSubject))
    else:
        bot.send_message(message.chat.id, 'Тематика {0} не существует.'.format(deleteSubject))


@bot.message_handler(commands=['add'])
def choose_whats_next(message):
    keyboard = types.InlineKeyboardMarkup()
    key_add_subject = types.InlineKeyboardButton(text='Добавить тематику', callback_data='add_subject')
    key_add_sites = types.InlineKeyboardButton(text='Добавить сайт к тематике', callback_data='add_sites')
    keyboard.add(key_add_sites, key_add_subject)
    bot.send_message(message.chat.id, 'Выберите что сделать', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def add_subject(call):
    if call.data == 'add_subject':
        msg = bot.send_message(call.message.chat.id, 'Пожалуйста, введите название для добавления тематики')
        bot.register_next_step_handler(msg, input_subject)
    if call.data == 'add_sites':
        msg = bot.send_message(call.message.chat.id, 'Пожалуйста, выберите тематику')
        show_all(call.message)
        bot.register_next_step_handler(msg, add_sites)


def input_subject(message):
    subjectText = message.text
    if collection.find_one({'subject': subjectText}) is not None:
        bot.send_message(message.chat.id, 'Тематика {0} уже существует.'.format(subjectText))
    else:
        dictionary = {'subject': subjectText, 'sites': []}
        collection.insert_one(dictionary)
        bot.send_message(message.chat.id, 'Спасибо! Тематика {0} добавлена.'.format(subjectText))


def add_sites(message):
    updateSubject = message.text
    query = {'subject': updateSubject}
    if collection.find_one(query) is not None:
        msg = bot.send_message(message.chat.id, 'Введите ссылку для добавления')
        bot.register_next_step_handler(msg, update_sites, query)
    else:
        bot.send_message(message.chat.id, '{0} не существует'.format(updateSubject))


def update_sites(message, query):
    site = message.text
    newSite = {'$push': {'sites': site}}
    print(query)
    print(newSite)
    collection.update_one(query, newSite)
    bot.send_message(message.chat.id, 'Сайт добавлен')


print('Бот запущен')
bot.infinity_polling()
