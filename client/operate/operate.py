import time
import asyncio
from prompt_toolkit import prompt
from operate.exceptions import ModelNotRecognizedException
import threading
from pynput import keyboard


from operate.models.prompts import (
    USER_QUESTION,
    get_system_prompt,
)
from operate.config import Config
from operate.utils.style import (
    ANSI_GREEN,
    ANSI_RESET,
    ANSI_YELLOW,
    ANSI_RED,
    ANSI_BRIGHT_MAGENTA,
    ANSI_BLUE,
    style,
)
from operate.utils.operating_system import OperatingSystem
# from operate.models.apis import get_next_action

# Load configuration
config = Config()
operating_system = OperatingSystem()


def on_press(key):
    if key == keyboard.Key.esc:
        print(f"\n{ANSI_BRIGHT_MAGENTA}Нажата клавиша ESC! Прерывание текущей задачи...{ANSI_RESET}")
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
        if initial_prompt:
            objective = initial_prompt
            # Используем начальный промпт только один раз
            initial_prompt = None
        else:
            # В цикле запрашиваем новые команды
            print(f"\n[{ANSI_GREEN}Self-Operating Computer {ANSI_RESET}|{ANSI_BRIGHT_MAGENTA} {model}{ANSI_RESET}]")
            print(f"Ожидаю текстовую команду (для завершения введите 'exit')")
            print(f"{ANSI_YELLOW}[User]{ANSI_RESET}")
            objective = prompt(style=style)

        if objective.lower() == 'exit':
            print(f"{ANSI_BRIGHT_MAGENTA}Выход из программы...{ANSI_RESET}")
            break

        if not objective:
            print(f"{ANSI_RED}Команда не может быть пустой. Попробуйте снова.{ANSI_RESET}")
            continue

        # Запускаем выполнение полученной задачи
        await run_objective_task(objective, model)


async def run_objective_task(objective, model):
    print(f"\n{ANSI_BLUE}Новая задача: {ANSI_RESET}{objective}")
    
    system_prompt = get_system_prompt(model, objective)
    system_message = {"role": "system", "content": system_prompt}
    messages = [system_message]
    loop_count = 0
    session_id = None

    while True:
        if config.verbose:
            print("[Self Operating Computer] loop_count", loop_count)
            
        config.stop_execution_flag = False
            
        try:
            # Получаем следующее действие от AI
            get_next_action(model, messages, objective, session_id)

            # Передаем операции на выполнение
            stop_task = operate(operations, model)
            if stop_task or config.stop_execution_flag:
                if not config.stop_execution_flag:
                     print(f"{ANSI_GREEN}Задача выполнена или прервана AI.{ANSI_RESET}")
                break

            loop_count += 1
            if loop_count > 10:
                print(f"{ANSI_YELLOW}Достигнут лимит итераций для этой задачи.{ANSI_RESET}")
                break
        except ModelNotRecognizedException as e:
            print(f"{ANSI_GREEN}[Self-Operating Computer]{ANSI_RED}[Error] -> {e} {ANSI_RESET}")
            break
        except Exception as e:
            print(f"{ANSI_GREEN}[Self-Operating Computer]{ANSI_RED}[Error] -> {e} {ANSI_RESET}")
            break


def operate(operations, model):
    
    listener_thread = threading.Thread(target=listen_for_esc, daemon=True)
    listener_thread.start()

    print(f"{ANSI_GREEN}▶ Выполняю задачу... (для преждевременной отмены нажмите ESC){ANSI_RESET}")

    for operation in operations:

        if config.stop_execution_flag:
            break

        if config.verbose:
            print("[Self Operating Computer][operate] operation", operation)
        
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
            print(f"[{ANSI_GREEN}Self-Operating Computer {ANSI_RESET}|{ANSI_BRIGHT_MAGENTA} {model}{ANSI_RESET}]")
            print(f"{ANSI_BLUE}Objective Complete: {ANSI_RESET}{summary}\n")
            return True # Сигнал о завершении ЗАДАЧИ
        else:
            print(f"{ANSI_GREEN}[Self-Operating Computer]{ANSI_RED}[Error] unknown operation response :({ANSI_RESET}")
            print(f"{ANSI_GREEN}[Self-Operating Computer]{ANSI_RED}[Error] AI response {ANSI_RESET}{operation}")
            return True

        print(f"[{ANSI_GREEN}Self-Operating Computer {ANSI_RESET}|{ANSI_BRIGHT_MAGENTA} {model}{ANSI_RESET}]")
        print(f"{operate_thought}")
        print(f"{ANSI_BLUE}Action: {ANSI_RESET}{operate_type} {operate_detail}\n")

    return False