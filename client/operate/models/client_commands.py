# Рудимент, предположительно можно будет удалить
import asyncio
import io
import platform
import socketio
import pyautogui

sio = socketio.AsyncClient(logger=False, engineio_logger=False)


@sio.event
async def connect():
    print('Успешно подключено к серверу!')
    await send_initial_info()


@sio.event
async def disconnect():
    """
    Вызывается при отключении от сервера.
    """
    print('Отключено от сервера.')


@sio.on('request_screenshot')
async def handle_request_screenshot(_=None):
    print("Получен запрос на скриншот от сервера...")
    try:
        def _make_screenshot():
            img = pyautogui.screenshot()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()

        img_bytes = await asyncio.to_thread(_make_screenshot)
        print("Скриншот готов, отправляю ответ серверу.")
        return {"image": img_bytes, "format": "PNG"}

    except Exception as e:
        print(f"Ошибка при создании скриншота: {e}")
        return {"error": str(e)}


@sio.on('execute_action')
async def handle_execute_action(data):
    """
    Принимает и выполняет команды от сервера.
    """
    action = data.get("action")
    print(f"Получена команда от сервера: {data}")

    try:
        if action == "click":
            x, y = int(data["x"]), int(data["y"])
            print(f"Выполняю клик в точке ({x}, {y})")
            pyautogui.click(x, y)
        elif action == "type":
            text_to_type = data["text"]
            print(f"Печатаю текст: '{text_to_type}'")
            pyautogui.write(text_to_type, interval=0.05)
        else:
            print(f"Получена неизвестная команда: '{action}'")

    except Exception as e:
        print(f"Ошибка при выполнении команды '{action}': {e}")


# --- Вспомогательные функции ---

async def send_initial_info():
    prompt = "Найди и открой калькулятор" # Пример промпта
    os_type = platform.system()
    model = "gemini-pro-with-ocr"

    data = {"os": os_type, "prompt": prompt, "model": model}
    await sio.emit('client_info', data=data)
    print(f"Начальная информация ({os_type}, '{prompt}') отправлена на сервер.")


async def main():
    """
    Основная функция для подключения к серверу и ожидания событий.
    """
    server_address = 'http://localhost:9003'
    try:
        print(f"Подключение к серверу {server_address}...")
        await sio.connect(server_address)
        # sio.wait() будет работать вечно, пока соединение активно
        await sio.wait()
    except socketio.exceptions.ConnectionError as e:
        print(f"Не удалось подключиться к серверу: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        print("Программа завершена.")


if __name__ == '__main__':
    # Запускаем основную асинхронную функцию
    asyncio.run(main())
