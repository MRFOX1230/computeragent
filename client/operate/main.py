import argparse
#from operate.utils.style import ANSI_BRIGHT_MAGENTA

import asyncio
import io
import platform
import socketio
import pyautogui

import time
import asyncio
# from prompt_toolkit import prompt
from operate.exceptions import ModelNotRecognizedException
import threading
from pynput import keyboard
import traceback
import logging
import sys

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
# Настраиваем логирование для записи в файл и вывода в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("client_debug.log", mode='w'), # Запись в файл
        logging.StreamHandler(sys.stdout) # Вывод в консоль
    ]
)


from operate.models.prompts import (
    USER_QUESTION,
    get_system_prompt,
)
from operate.config import Config
# from operate.utils.style import (
#     ANSI_GREEN,
#     ANSI_RESET,
#     ANSI_YELLOW,
#     ANSI_RED,
#     ANSI_BRIGHT_MAGENTA,
#     ANSI_BLUE,
#     style,
# )
from operate.utils.operating_system import OperatingSystem

# ------------------------------------------------------------

# Комманды для клиента
sio = socketio.AsyncClient(logger=False, engineio_logger=False)


# @sio.event
# async def connect():
#     logging.info('Успешно подключено к серверу!')

#     model = "gemini-pro-with-ocr"
#     os_type = platform.system()
#     prompt_text = "Зайди в Chrome" # Пример промпта

#     await send_initial_info(model, os_type, prompt)
#     sio.sleep(2)
#     await main_entry(initial_prompt=prompt_text)

# Файл: main.py


# Наши параметры
model = "gemini-pro-with-ocr"
os_type = platform.system()
objective = "Сверни все окна, на рабочем столе найди приложение Postman и через курсор мыши запусти его"

@sio.event
async def connect():
    logging.info('Успешно подключено к серверу!')

    # --- Параметры для нашей задачи ---
    global model
    global os_type
    global objective

    # 1. Отправляем начальную информацию на сервер и ждем команды "start_task"
    await send_initial_info(model, os_type, objective)
    logging.info("Информация отправлена, ожидаю команды от сервера для старта...")


# НОВЫЙ ОБРАБОТЧИК: Запускается по команде от сервера
@sio.on('start_task')
async def on_start_task():
    print("!!! ПОЛУЧЕНА КОМАНДА 'start_task'. НАЧИНАЮ ОБРАБОТКУ !!!") # <-- Добавьте эту строку
    # --- Параметры для нашей задачи (берем те же, что и в connect) ---
    global model
    global objective
    verbose_mode = True

    # --- Настраиваем конфигурацию ---
    config.verbose = verbose_mode
    try:
        config.validation(model, voice_mode=False)
    except Exception as e:
        logging.error(f"Ошибка валидации конфигурации: {e}")
        return

    def task_done_callback(task: asyncio.Task):
        """Callback to handle task completion and exceptions."""
        try:
            task.result()
        except asyncio.CancelledError:
            pass  # Task was cancelled, ignore.
        except Exception:
            logging.error(f"ФОНОВАЯ ЗАДАЧA УПАЛА С ОШИБКОЙ:")
            # Записываем traceback в лог-файл
            logging.error(traceback.format_exc())


    # Запускаем основную задачу в фоне и добавляем обработчик ошибок
    task = asyncio.create_task(run_objective_task(objective, model))
    task.add_done_callback(task_done_callback)


@sio.event
async def disconnect():
    """
    Вызывается при отключении от сервера.
    """
    logging.info('Отключено от сервера.')


@sio.on('request_screenshot')
async def handle_request_screenshot(_=None):
    logging.info("Получен запрос на скриншот от сервера...")
    try:
        def _make_screenshot():
            img = pyautogui.screenshot()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()

        img_bytes = await asyncio.to_thread(_make_screenshot)
        logging.info("Скриншот готов, отправляю ответ серверу.")
        return {"image": img_bytes, "format": "PNG"}

    except Exception as e:
        logging.error(f"Ошибка при создании скриншота: {e}")
        return {"error": str(e)}


# --- Вспомогательные функции ---

async def send_initial_info(model, os_type, prompt):
    data = {"os": os_type, "prompt": prompt, "model": model}
    await sio.emit('client_info', data=data)
    logging.info(f"Начальная информация ({os_type}, '{prompt}') отправлена на сервер.")



async def get_next_action_from_server(messages):
    logging.info("\n[Клиент] Отправляю задачу на сервер для получения следующего действия...")
    payload = {
        "messages": messages
    }
    # sio.call отправляет данные и ждет `return` от обработчика на сервере
    response = await sio.call('get_next_action', data=payload, timeout=500) # Увеличено время ожидания
    
    # ИСПРАВЛЕНИЕ: Добавляем проверку на ошибку от сервера
    if response.get("status") == "error":
        error_message = response.get("message", "Неизвестная ошибка на сервере")
        logging.error(f"[Клиент] Сервер вернул ошибку: {error_message}")
        raise Exception(f"Ошибка на сервере: {error_message}")
        
    return response["operations"]

async def main_client():
    """
    Основная функция для подключения к серверу и ожидания событий.
    """
    server_address = 'http://localhost:9003'
    try:
        logging.info(f"Подключение к серверу {server_address}...")
        await sio.connect(server_address)
        # sio.wait() будет работать вечно, пока соединение активно
        await sio.wait()
    except socketio.exceptions.ConnectionError as e:
        logging.error(f"Не удалось подключиться к серверу: {e}")
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
    finally:
        logging.info("Программа завершена.")

# ------------------------------------------------------------

# Комманды operate 

# Load configuration
config = Config()
operating_system = OperatingSystem()


def on_press(key):
    if key == keyboard.Key.esc:
        logging.info(f"\nНажата клавиша ESC! Прерывание текущей задачи...")
        config.stop_execution_flag = True
        # Возвращаем False, чтобы остановить слушатель
        return False

def listen_for_esc():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()



async def main(model, terminal_prompt, voice_mode=False, verbose_mode=False):
    config.verbose = verbose_mode
    config.validation(model, voice_mode)

    # При первом запуске используем аргумент из терминала, если он есть
    initial_prompt = terminal_prompt

    while True:
        # Получаем задачу от пользователя
        objective = initial_prompt
        # Используем начальный промпт только один раз
        initial_prompt = None

        if objective.lower() == 'exit':
            logging.info(f"Выход из программы...")
            break

        if not objective:
            logging.warning(f"Команда не может быть пустой. Попробуйте снова.")
            continue

        # Запускаем выполнение полученной задачи
        await run_objective_task(objective, model)


async def run_objective_task(objective, model):
    logging.info(f"\n[DEBUG] ==> ЗАПУСК run_objective_task с задачей: {objective}")

    try:
        system_prompt = get_system_prompt(model, objective)
        system_message = {"role": "system", "content": system_prompt}
        messages = [system_message]
        loop_count = 0

        while True:
            if config.verbose:
                logging.info(f"[Self Operating Computer] loop_count {loop_count}")

            config.stop_execution_flag = False

            try:
                logging.info(f"[DEBUG] ==> ШАГ 1: Пытаюсь получить следующее действие от сервера...")
                operations = await get_next_action_from_server(messages)
                if operations is None: # Проверка на случай если get_next_action_from_server вернет None после ошибки
                    logging.error("Не удалось получить операции от сервера. Прерываю задачу.")
                    break
                    
                logging.info(f"[DEBUG] ==> ШАГ 2: Успешно получен ответ от сервера. Операции: {operations}")

                stop_task = operate(operations, model)
                if stop_task or config.stop_execution_flag:
                    if not config.stop_execution_flag:
                        logging.info(f"Задача выполнена или прервана AI.")
                    break

                loop_count += 1
                if loop_count > 10:
                    logging.warning(f"Достигнут лимит итераций для этой задачи.")
                    break
            except Exception as e:
                # ИСПРАВЛЕНИЕ: Логируем ошибку, но не выводим полный traceback, так как он уже есть в get_next_action_from_server
                logging.error(f"КРИТИЧЕСКАЯ ОШИБКА в цикле run_objective_task: {e}")
                break

    except Exception as e:
        logging.error(f"КРИТИЧЕСКАЯ ОШИБКА при инициализации run_objective_task:")
        logging.error(traceback.format_exc())


def operate(operations, model):
    
    # listener_thread = threading.Thread(target=listen_for_esc, daemon=True)
    # listener_thread.start()

    logging.info(f"▶ Выполняю задачу... (для преждевременной отмены нажмите ESC)")

    for operation in operations:

        if config.stop_execution_flag:
            break

        if config.verbose:
            logging.info(f"[Self Operating Computer][operate] operation: {operation}")
        
        interrupted = False
        for _ in range(10):
            if config.stop_execution_flag:
                interrupted = True
                break
            time.sleep(0.1)
        if interrupted:
            break

        operate_type = operation.get("operation").lower()
        operate_thought = operation.get("thought")
        operate_detail = ""

        if operate_type == "press" or operate_type == "hotkey":
            keys = operation.get("keys")
            operate_detail = keys
            operating_system.press(keys)
        elif operate_type == "write":
            content = operation.get("content")
            operate_detail = content
            operating_system.write(content)
        elif operate_type == "click":
            x = operation.get("x")
            y = operation.get("y")
            click_detail = {"x": x, "y": y}
            operate_detail = click_detail
            operating_system.mouse(click_detail)
        elif operate_type == "done":
            summary = operation.get("summary")
            logging.info(f"[Self-Operating Computer | {model}]")
            logging.info(f"Objective Complete: {summary}\n")
            return True # Сигнал о завершении ЗАДАЧИ
        else:
            logging.error(f"[Self-Operating Computer] unknown operation response :(")
            logging.error(f"[Self-Operating Computer] AI response {operation}")
            return True

        logging.info(f"[Self-Operating Computer | {model}]")
        logging.info(f"{operate_thought}")
        logging.info(f"Action: {operate_type} {operate_detail}\n")

    return False





# ------------------------------------------------------------

# Комманды main

async def main_entry(initial_prompt=None):
    parser = argparse.ArgumentParser(
        description="Run the self-operating-computer with a specified model."
    )
    parser.add_argument(
        "-m",
        "--model",
        help="Specify the model to use",
        required=False,
        default="gpt-4-with-ocr",
    )

    # Add a voice flag
    parser.add_argument(
        "--voice",
        help="Use voice input mode",
        action="store_true",
    )
    
    # Add a flag for verbose mode
    parser.add_argument(
        "--verbose",
        help="Run operate in verbose mode",
        action="store_true",
    )
    
    # Allow for direct input of prompt
    parser.add_argument(
        "--prompt",
        help="Directly input the objective prompt",
        type=str,
        required=False,
    )

    try:
        args = parser.parse_args()
        final_prompt = initial_prompt if initial_prompt is not None else args.prompt
        await main(args.model,
            terminal_prompt=final_prompt,
            voice_mode=args.voice,
            verbose_mode=args.verbose
            )
    except KeyboardInterrupt:
        logging.info(f"\nExiting...")


if __name__ == '__main__':
    # Запускаем основную асинхронную функцию
    asyncio.run(main_client())
