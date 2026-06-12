import asyncio
import os
import time
import socketio
import uvicorn
from PIL import Image
import traceback
import json
import base64
import io
import easyocr
import google.generativeai as genai

from operate.config import Config
from operate.exceptions import ModelNotRecognizedException
from operate.models.prompts import (
    get_system_prompt,
    get_user_first_message_prompt,
    get_user_prompt,
)
from operate.utils.label import (
    add_labels,
    get_click_position_in_percent,
    get_label_coordinates,
)
from operate.utils.ocr import get_text_coordinates, get_text_element
# from operate.utils.screenshot import capture_screen_with_cursor, compress_screenshot

GOOGLE_API_KEY = "AIzaSyC3mUqiDEJrW4MNohe_a88j18i2s32CEVY"

client_state = {
    "sid": None,
    "os": None,
    "prompt": None,
    "model": None,
    "is_running": False
}


# --- Настройка Socket.IO Сервера ---
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    ping_timeout=30,
    ping_interval=25,
    max_http_buffer_size=10_000_000,
)
app = socketio.ASGIApp(sio)


# --- Обработчики событий Socket.IO ---

@sio.on('connect')
async def handle_connect(sid, environ):
    """
    Вызывается, когда клиент успешно подключается к серверу.
    """
    print(f"Клиент {sid} подключился.")
    # Если уже есть активный клиент, отклоняем новое подключение
    if client_state["sid"] is not None:
        print(f"Отклонение подключения от {sid}: другой клиент уже активен.")
        await sio.disconnect(sid)
        return

    client_state["sid"] = sid


@sio.on('disconnect')
async def handle_disconnect(sid):
    """
    Вызывается, когда клиент отключается.
    """
    print(f"Клиент {sid} отключился.")
    # Сбрасываем состояние, чтобы можно было подключить нового клиента
    if client_state["sid"] == sid:
        client_state["sid"] = None
        client_state["os"] = None
        client_state["prompt"] = None
        client_state["is_running"] = False


@sio.on('client_info')
async def handle_client_info(sid, data):
    """
    Принимает начальную информацию (ОС и промпт) от клиента.
    """
    print(f"Получена информация от клиента {sid}: Модель = {data.get('model')}, ОС={data.get('os')}, Промпт={data.get('prompt')}")
    client_state["os"] = data.get("os")
    client_state["prompt"] = data.get("prompt")
    client_state["model"] = data.get("model")
    # После получения информации запускаем основной рабочий цикл
    if not client_state["is_running"]:
        client_state["is_running"] = True
    
    # ИСПРАВЛЕНИЕ: Отправляем клиенту команду на старт
    print(f"Отправка команды 'start_task' клиенту {sid}")
    await sio.emit('start_task', to=sid)


async def request_screenshot_from_client(sid):
    """
    Запрашивает скриншот у клиента, используя sio.call для ожидания ответа.
    Возвращает байты изображения или None в случае ошибки.
    """
    if not sid:
        print("Ошибка: Нет подключенного клиента для запроса скриншота.")
        return None

    print(f"Отправка запроса на скриншот клиенту {sid}...")
    try:
        # Используем `call` для отправки события и ожидания ответа от клиента
        response = await sio.call('request_screenshot', to=sid, timeout=20)

        if not isinstance(response, dict):
            raise RuntimeError(f"Некорректный тип ответа от клиента: {type(response)}")
        if "error" in response:
            raise RuntimeError(f"Клиент вернул ошибку: {response['error']}")

        image_bytes = response.get('image')
        if not image_bytes:
            raise RuntimeError("Клиент прислал пустые байты изображения.")

        print(f"Скриншот от {sid} успешно получен ({len(image_bytes):,} байт).")
        return image_bytes

    except asyncio.TimeoutError:
        print(f"Ошибка: Клиент {sid} не ответил на запрос скриншота вовремя.")
    except Exception as e:
        print(f"Критическая ошибка при запросе скриншота у клиента {sid}: {e}")

    return None

async def get_screenshot_image_and_path(sid):
    print("\n--- Получение и сохранение скриншота ---")
    image_bytes = await request_screenshot_from_client(sid)
    if not image_bytes:
        return None, None

    try:
        image = Image.open(io.BytesIO(image_bytes))
        save_directory = "screenshots"
        os.makedirs(save_directory, exist_ok=True)
        file_path = os.path.join(save_directory, "screenshot.png")
        await asyncio.to_thread(image.save, file_path, "PNG")
        print(f"Скриншот сохранён в: {file_path}")
        return image, file_path
    except Exception as e:
        print(f"Ошибка при сохранении скриншота: {e}")
        return None, None

#-------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------

# Load configuration
config = Config()

@sio.on('get_next_action')
async def handle_get_next_action(sid, data):
    
    print(f"\n--- Получена задача от {sid}: '{client_state['prompt']}' ---")

    try:
        processed_operations =  await get_next_action(sid, client_state["model"], data["messages"], client_state["prompt"], client_state["os"])
        return {"status": "success", "operations": processed_operations}

    except Exception as e:
        print(f"[ОШИБКА] Ошибка при обработке задачи: {e}")
        traceback.print_exc()
        # Возвращаем ошибку клиенту
        return {"status": "error", "message": str(e)}

async def get_next_action(sid, model, messages, objective, os_type):
    if config.verbose:
        print("[Self-Operating Computer][get_next_action]")
        print("[Self-Operating Computer][get_next_action] model", model)
    if model == "gemini-pro-with-ocr":
        return await call_gemini_pro_with_ocr(sid, model, messages, objective, os_type)
    raise ModelNotRecognizedException(model)


async def call_gemini_pro_with_ocr(sid, model, messages, objective, os_type):
    if config.verbose:
        print("[Self-Operating Computer | gemini-pro-with-ocr]")

    await asyncio.sleep(1)
    try:
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY не установлен. Укажите ключ API в server_commands.py.")
        genai.configure(api_key=GOOGLE_API_KEY)
        
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        
        # ИСПРАВЛЕНИЕ: Правильный вызов функции с двумя аргументами
        system_prompt = get_system_prompt(model, objective)

        if len(messages) == 1:
            turn_prompt = get_user_first_message_prompt()
        else:
            turn_prompt = get_user_prompt()
            
        final_prompt_text = f"{system_prompt}\n{turn_prompt}"
        
        screenshot_image, screenshot_filename = await get_screenshot_image_and_path(sid)
        if not screenshot_image:
            raise Exception("Не удалось получить скриншот от клиента.")
        
        prompt_parts = [final_prompt_text, screenshot_image]
        response = await asyncio.to_thread(gemini_model.generate_content, prompt_parts)
        content = response.text
        content = clean_json(content)
        
        # Сохраняем оригинальный ответ для истории сообщений
        content_str_for_history = content
        
        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError:
            print(f"GEMINI ERROR: Model did not return valid JSON. Response was: {content}")
            raise
        
        if isinstance(parsed_content, dict):
            parsed_content = [parsed_content]

        processed_content = []
        # Инициализируем OCR один раз
        reader = await asyncio.to_thread(easyocr.Reader, ['en', 'ru']) 

        for operation in parsed_content:
            if operation.get("operation") == "click":

                # Добавляем задержку в 3 секунды перед запуском OCR
                print("[Self-Operating Computer] Waiting up to 3 seconds for UI to load...")
                interrupted = False
                for _ in range(30): # 30 * 0.1s = 3 секунды
                    if config.stop_execution_flag:
                        interrupted = True
                        break
                    await asyncio.sleep(0.1)

                if interrupted:
                    raise Exception("Task interrupted by user during wait.")


                text_to_click = operation.get("text")
                if config.verbose:
                    print(f"[gemini-pro-ocr][click] text_to_click: '{text_to_click}'")
                
                # Распознаем текст на скриншоте
                result = await asyncio.to_thread(reader.readtext, screenshot_filename)

                # Находим координаты
                text_element_index = get_text_element(result, text_to_click, screenshot_filename)
                coordinates = get_text_coordinates(result, text_element_index, screenshot_filename)

                # Заменяем текстовое описание на точные координаты для исполнителя
                operation["x"] = coordinates["x"]
                operation["y"] = coordinates["y"]
                
                if config.verbose:
                    print(f"[gemini-pro-ocr][click] Found coordinates: {coordinates}")
                
                processed_content.append(operation)
            else:
                # Другие операции (write, press, done) добавляем без изменений
                processed_content.append(operation)

        with open(screenshot_filename, "rb") as img_file:
            img_bytes = await asyncio.to_thread(img_file.read)
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        
        vision_message = { "role": "user", "content": [{"type": "text", "text": final_prompt_text}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}]}
        messages.append(vision_message)
        
        # В историю добавляем оригинальный ответ модели (с "text" для клика)
        assistant_message = {"role": "assistant", "content": content_str_for_history}
        messages.append(assistant_message)
        
        return processed_content

    except Exception as e:
        print(f"{model} API ERROR: {e}")
        if config.verbose:
            traceback.print_exc()
        raise


def get_last_assistant_message(messages):
    """
    Retrieve the last message from the assistant in the messages array.
    If the last assistant message is the first message in the array, return None.
    """
    for index in reversed(range(len(messages))):
        if messages[index]["role"] == "assistant":
            if index == 0:  # Check if the assistant message is the first in the array
                return None
            else:
                return messages[index]
    return None  # Return None if no assistant message is found


def confirm_system_prompt(messages, objective, model):
    """
    On `Exception` we default to `call_gpt_4_vision_preview` so we have this function to reassign system prompt in case of a previous failure
    """
    if config.verbose:
        print("[confirm_system_prompt] model", model)

    os_type = client_state.get("os")
    # ИСПРАВЛЕНИЕ: Правильный вызов функции с двумя аргументами
    system_prompt = get_system_prompt(model, objective)
    new_system_message = {"role": "system", "content": system_prompt}
    # remove and replace the first message in `messages` with `new_system_message`

    messages[0] = new_system_message

    if config.verbose:
        print("[confirm_system_prompt]")
        print("[confirm_system_prompt] len(messages)", len(messages))
        for m in messages:
            if m["role"] != "user":
                print("--------------------[message]--------------------")
                print("[confirm_system_prompt][message] role", m["role"])
                print("[confirm_system_prompt][message] content", m["content"])
                print("------------------[end message]------------------")


def clean_json(content):
    if config.verbose:
        print("\n\n[clean_json] content before cleaning", content)
    if content.startswith("```json"):
        content = content[
            len("```json") :
        ].strip()  # Remove starting ```json and trim whitespace
    elif content.startswith("```"):
        content = content[
            len("```") :
        ].strip()  # Remove starting ``` and trim whitespace
    if content.endswith("```"):
        content = content[
            : -len("```")
        ].strip()  # Remove ending ``` and trim whitespace

    # Normalize line breaks and remove any unwanted characters
    content = "\n".join(line.strip() for line in content.splitlines())

    if config.verbose:
        print("\n\n[clean_json] content after cleaning", content)

    return content


if __name__ == '__main__':
    print("Запуск сервера на http://0.0.0.0:9003")
    uvicorn.run(app, host="0.0.0.0", port=9003, ws_max_size=10_000_000)

