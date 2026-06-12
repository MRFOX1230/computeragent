# Рудимент,предположительно можно удалить
import base64
import io
import json
import os
import time
import traceback

import easyocr
import ollama
import pkg_resources
from PIL import Image
from ultralytics import YOLO

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

# Load configuration
config = Config()


async def get_next_action(model, messages, objective, session_id):
    if config.verbose:
        print("[Self-Operating Computer][get_next_action]")
        print("[Self-Operating Computer][get_next_action] model", model)
    # if model == "gpt-4":
    #     return call_gpt_4o(messages), None
    # if model == "qwen-vl":
    #     operation = await call_qwen_vl_with_ocr(messages, objective, model)
    #     return operation, None
    # if model == "gpt-4-with-som":
    #     operation = await call_gpt_4o_labeled(messages, objective, model)
    #     return operation, None
    # if model == "gpt-4-with-ocr":
    #     operation = await call_gpt_4o_with_ocr(messages, objective, model)
    #     return operation, None
    # if model == "gpt-4.1-with-ocr":
    #     operation = await call_gpt_4_1_with_ocr(messages, objective, model)
    #     return operation, None
    # if model == "o1-with-ocr":
    #     operation = await call_o1_with_ocr(messages, objective, model)
    #     return operation, None
    # if model == "agent-1":
    #     return "coming soon"
    if model == "gemini-pro-with-ocr":
        return call_gemini_pro_with_ocr(messages, objective, model), None
    # if model == "llava":
    #     operation = call_ollama_llava(messages)
    #     return operation, None
    # if model == "claude-3":
    #     operation = await call_claude_3_with_ocr(messages, objective, model)
    #     return operation, None
    # if model == "llava-with-ocr":
    #     operation = call_ollama_llava_with_ocr(messages, objective, model)
    #     return operation, None
    raise ModelNotRecognizedException(model)


# def call_gpt_4o(messages):
#     if config.verbose:
#         print("[call_gpt_4_v]")
#     time.sleep(1)
#     client = config.initialize_openai()
#     try:
#         screenshots_dir = "screenshots"
#         if not os.path.exists(screenshots_dir):
#             os.makedirs(screenshots_dir)

#         screenshot_filename = os.path.join(screenshots_dir, "screenshot.png")
#         # Call the function to capture the screen with the cursor
#         capture_screen_with_cursor(screenshot_filename)

#         with open(screenshot_filename, "rb") as img_file:
#             img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

#         if len(messages) == 1:
#             user_prompt = get_user_first_message_prompt()
#         else:
#             user_prompt = get_user_prompt()

#         if config.verbose:
#             print(
#                 "[call_gpt_4_v] user_prompt",
#                 user_prompt,
#             )

#         vision_message = {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": user_prompt},
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
#                 },
#             ],
#         }
#         messages.append(vision_message)

#         response = client.chat.completions.create(
#             model="gpt-4o",
#             messages=messages,
#             presence_penalty=1,
#             frequency_penalty=1,
#         )

#         content = response.choices[0].message.content

#         content = clean_json(content)

#         assistant_message = {"role": "assistant", "content": content}
#         if config.verbose:
#             print(
#                 "[call_gpt_4_v] content",
#                 content,
#             )
#         content = json.loads(content)

#         messages.append(assistant_message)

#         return content

#     except Exception as e:
#         print(
#             f"[Self-Operating Computer][Operate] That did not work. Trying again",
#             e,
#         )
#         print(
#             f"[Self-Operating Computer][Error] AI response was",
#             content,
#         )
#         if config.verbose:
#             traceback.print_exc()
#         return call_gpt_4o(messages)


# async def call_qwen_vl_with_ocr(messages, objective, model):
#     if config.verbose:
#         print("[call_qwen_vl_with_ocr]")

#     # Construct the path to the file within the package
#     try:
#         time.sleep(1)
#         client = config.initialize_qwen()

#         confirm_system_prompt(messages, objective, model)
#         screenshots_dir = "screenshots"
#         if not os.path.exists(screenshots_dir):
#             os.makedirs(screenshots_dir)

#         # Call the function to capture the screen with the cursor
#         raw_screenshot_filename = os.path.join(screenshots_dir, "raw_screenshot.png")
#         capture_screen_with_cursor(raw_screenshot_filename)

#         # Compress screenshot image to make size be smaller
#         screenshot_filename = os.path.join(screenshots_dir, "screenshot.jpeg")
#         compress_screenshot(raw_screenshot_filename, screenshot_filename)

#         with open(screenshot_filename, "rb") as img_file:
#             img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

#         if len(messages) == 1:
#             user_prompt = get_user_first_message_prompt()
#         else:
#             user_prompt = get_user_prompt()

#         vision_message = {
#             "role": "user",
#             "content": [
#                 {"type": "text",
#                  "text": f"{user_prompt}**REMEMBER** Only output json format, do not append any other text."},
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
#                 },
#             ],
#         }
#         messages.append(vision_message)

#         response = client.chat.completions.create(
#             model="qwen2.5-vl-72b-instruct",
#             messages=messages,
#         )

#         content = response.choices[0].message.content

#         content = clean_json(content)

#         # used later for the messages
#         content_str = content

#         content = json.loads(content)

#         processed_content = []

#         for operation in content:
#             if operation.get("operation") == "click":
#                 text_to_click = operation.get("text")
#                 if config.verbose:
#                     print(
#                         "[call_qwen_vl_with_ocr][click] text_to_click",
#                         text_to_click,
#                     )
#                 # Initialize EasyOCR Reader
#                 reader = easyocr.Reader(["en", "ru"])

#                 # Read the screenshot
#                 result = reader.readtext(screenshot_filename)

#                 text_element_index = get_text_element(
#                     result, text_to_click, screenshot_filename
#                 )
#                 coordinates = get_text_coordinates(
#                     result, text_element_index, screenshot_filename
#                 )

#                 # add `coordinates`` to `content`
#                 operation["x"] = coordinates["x"]
#                 operation["y"] = coordinates["y"]

#                 if config.verbose:
#                     print(
#                         "[call_qwen_vl_with_ocr][click] text_element_index",
#                         text_element_index,
#                     )
#                     print(
#                         "[call_qwen_vl_with_ocr][click] coordinates",
#                         coordinates,
#                     )
#                     print(
#                         "[call_qwen_vl_with_ocr][click] final operation",
#                         operation,
#                     )
#                 processed_content.append(operation)

#             else:
#                 processed_content.append(operation)

#         # wait to append the assistant message so that if the `processed_content` step fails we don't append a message and mess up message history
#         assistant_message = {"role": "assistant", "content": content_str}
#         messages.append(assistant_message)

#         return processed_content

#     except Exception as e:
#         print(
#             f"[Self-Operating Computer][{model}] That did not work. Trying another method"
#         )
#         if config.verbose:
#             print("[Self-Operating Computer][Operate] error", e)
#             traceback.print_exc()
#         return gpt_4_fallback(messages, objective, model)




# Изначальная функция
#-----------------------------------------------------------------------------
# def call_gemini_pro_with_ocr(messages, objective, model):
#     if config.verbose:
#         print("[Self-Operating Computer | gemini-pro-with-ocr]")

#     time.sleep(1)
#     try:
#         gemini_model = config.initialize_google()
        
#         # Убеждаемся, что используется промпт, оптимизированный под OCR
#         system_prompt = get_system_prompt("gemini-pro-with-ocr", objective)

#         if len(messages) == 1:
#             turn_prompt = get_user_first_message_prompt()
#         else:
#             turn_prompt = get_user_prompt()
            
#         final_prompt_text = f"{system_prompt}\n{turn_prompt}"
        
#         from PIL import Image
#         screenshots_dir = "screenshots"
#         screenshot_filename = os.path.join(screenshots_dir, "screenshot.png")
#         capture_screen_with_cursor(screenshot_filename)
#         screenshot_image = Image.open(screenshot_filename)
        
#         prompt_parts = [final_prompt_text, screenshot_image]
#         response = gemini_model.generate_content(prompt_parts)
#         content = response.text
#         content = clean_json(content)
        
#         # Сохраняем оригинальный ответ для истории сообщений
#         content_str_for_history = content
        
#         try:
#             parsed_content = json.loads(content)
#         except json.JSONDecodeError:
#             print(f"GEMINI ERROR: Model did not return valid JSON. Response was: {content}")
#             return call_gpt_4o(messages) # Фоллбэк на GPT-4
        
#         if isinstance(parsed_content, dict):
#             parsed_content = [parsed_content]

#         processed_content = []
#         # Инициализируем OCR один раз
#         reader = easyocr.Reader(['en', 'ru']) 

#         for operation in parsed_content:
#             if operation.get("operation") == "click":

#                 # Добавляем задержку в 3 секунды перед запуском OCR
#                 print("[Self-Operating Computer] Waiting up to 3 seconds for UI to load...")
#                 interrupted = False
#                 for _ in range(30): # 30 * 0.1s = 3 секунды
#                     if config.stop_execution_flag:
#                         interrupted = True
#                         break
#                     time.sleep(0.1)

#                 if interrupted:
#                     raise Exception("Task interrupted by user during wait.")


#                 text_to_click = operation.get("text")
#                 if config.verbose:
#                     print(f"[gemini-pro-ocr][click] text_to_click: '{text_to_click}'")
                
#                 # Распознаем текст на скриншоте
#                 result = reader.readtext(screenshot_filename)

#                 # Находим координаты
#                 text_element_index = get_text_element(result, text_to_click, screenshot_filename)
#                 coordinates = get_text_coordinates(result, text_element_index, screenshot_filename)

#                 # Заменяем текстовое описание на точные координаты для исполнителя
#                 operation["x"] = coordinates["x"]
#                 operation["y"] = coordinates["y"]
                
#                 if config.verbose:
#                     print(f"[gemini-pro-ocr][click] Found coordinates: {coordinates}")
                
#                 processed_content.append(operation)
#             else:
#                 # Другие операции (write, press, done) добавляем без изменений
#                 processed_content.append(operation)

#         # <<< Шаг 3: Обновление истории сообщений и возврат результата >>>
#         # Используем ту же логику обновления истории, что и в оригинальной функции Gemini
#         with open(screenshot_filename, "rb") as img_file:
#             img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
        
#         vision_message = { "role": "user", "content": [{"type": "text", "text": final_prompt_text}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}]}
#         messages.append(vision_message)
        
#         # В историю добавляем оригинальный ответ модели (с "text" для клика)
#         assistant_message = {"role": "assistant", "content": content_str_for_history}
#         messages.append(assistant_message)
        
#         return processed_content

#     except Exception as e:
#         print(f"{model} API ERROR: {e}")
#         if config.verbose:
#             traceback.print_exc()
#         # При ошибке также делаем фоллбэк на GPT-4
#         return call_gpt_4o(messages)
#------------------------------------------------------------------------------

# Переделанная фунцкия
def call_gemini_pro_with_ocr(messages, objective, model):
    if config.verbose:
        print("[Self-Operating Computer | gemini-pro-with-ocr]")

    time.sleep(1)
    try:
        gemini_model = config.initialize_google()
        
        # Убеждаемся, что используется промпт, оптимизированный под OCR
        system_prompt = get_system_prompt("gemini-pro-with-ocr", objective)

        if len(messages) == 1:
            turn_prompt = get_user_first_message_prompt()
        else:
            turn_prompt = get_user_prompt()
            
        final_prompt_text = f"{system_prompt}\n{turn_prompt}"
        
        from PIL import Image
        screenshots_dir = "screenshots"
        screenshot_filename = os.path.join(screenshots_dir, "screenshot.png")
        capture_screen_with_cursor(screenshot_filename)
        screenshot_image = Image.open(screenshot_filename)
        
        prompt_parts = [final_prompt_text, screenshot_image]
        response = gemini_model.generate_content(prompt_parts)
        content = response.text
        content = clean_json(content)
        
        # Сохраняем оригинальный ответ для истории сообщений
        content_str_for_history = content
        
        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError:
            print(f"GEMINI ERROR: Model did not return valid JSON. Response was: {content}")
            return call_gpt_4o(messages) # Фоллбэк на GPT-4
        
        if isinstance(parsed_content, dict):
            parsed_content = [parsed_content]

        processed_content = []
        # Инициализируем OCR один раз
        reader = easyocr.Reader(['en', 'ru']) 

        for operation in parsed_content:
            if operation.get("operation") == "click":

                # Добавляем задержку в 3 секунды перед запуском OCR
                print("[Self-Operating Computer] Waiting up to 3 seconds for UI to load...")
                interrupted = False
                for _ in range(30): # 30 * 0.1s = 3 секунды
                    if config.stop_execution_flag:
                        interrupted = True
                        break
                    time.sleep(0.1)

                if interrupted:
                    raise Exception("Task interrupted by user during wait.")


                text_to_click = operation.get("text")
                if config.verbose:
                    print(f"[gemini-pro-ocr][click] text_to_click: '{text_to_click}'")
                
                # Распознаем текст на скриншоте
                result = reader.readtext(screenshot_filename)

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

        # <<< Шаг 3: Обновление истории сообщений и возврат результата >>>
        # Используем ту же логику обновления истории, что и в оригинальной функции Gemini
        with open(screenshot_filename, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
        
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
        # При ошибке также делаем фоллбэк на GPT-4
        #return call_gpt_4o(messages)
        return
















# async def call_gpt_4o_with_ocr(messages, objective, model):
#     if config.verbose:
#         print("[call_gpt_4o_with_ocr]")

#     # Construct the path to the file within the package
#     try:
#         time.sleep(1)
#         client = config.initialize_openai()

#         confirm_system_prompt(messages, objective, model)
#         screenshots_dir = "screenshots"
#         if not os.path.exists(screenshots_dir):
#             os.makedirs(screenshots_dir)

#         screenshot_filename = os.path.join(screenshots_dir, "screenshot.png")
#         # Call the function to capture the screen with the cursor
#         capture_screen_with_cursor(screenshot_filename)

#         with open(screenshot_filename, "rb") as img_file:
#             img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

#         if len(messages) == 1:
#             user_prompt = get_user_first_message_prompt()
#         else:
#             user_prompt = get_user_prompt()

#         vision_message = {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": user_prompt},
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
#                 },
#             ],
#         }
#         messages.append(vision_message)

#         response = client.chat.completions.create(
#             model="gpt-4o",
#             messages=messages,
#         )

#         content = response.choices[0].message.content

#         content = clean_json(content)

#         # used later for the messages
#         content_str = content

#         content = json.loads(content)

#         processed_content = []

#         for operation in content:
#             if operation.get("operation") == "click":
#                 text_to_click = operation.get("text")
#                 if config.verbose:
#                     print(
#                         "[call_gpt_4o_with_ocr][click] text_to_click",
#                         text_to_click,
#                     )
#                 # Initialize EasyOCR Reader
#                 reader = easyocr.Reader(["en"])

#                 # Read the screenshot
#                 result = reader.readtext(screenshot_filename)

#                 text_element_index = get_text_element(
#                     result, text_to_click, screenshot_filename
#                 )
#                 coordinates = get_text_coordinates(
#                     result, text_element_index, screenshot_filename
#                 )

#                 # add `coordinates`` to `content`
#                 operation["x"] = coordinates["x"]
#                 operation["y"] = coordinates["y"]

#                 if config.verbose:
#                     print(
#                         "[call_gpt_4o_with_ocr][click] text_element_index",
#                         text_element_index,
#                     )
#                     print(
#                         "[call_gpt_4o_with_ocr][click] coordinates",
#                         coordinates,
#                     )
#                     print(
#                         "[call_gpt_4o_with_ocr][click] final operation",
#                         operation,
#                     )
#                 processed_content.append(operation)

#             else:
#                 processed_content.append(operation)

#         # wait to append the assistant message so that if the `processed_content` step fails we don't append a message and mess up message history
#         assistant_message = {"role": "assistant", "content": content_str}
#         messages.append(assistant_message)

#         return processed_content

#     except Exception as e:
#         print(
#             f"[Self-Operating Computer][{model}] That did not work. Trying another method"
#         )
#         if config.verbose:
#             print("[Self-Operating Computer][Operate] error", e)
#             traceback.print_exc()
#         return gpt_4_fallback(messages, objective, model)


# async def call_gpt_4_1_with_ocr(messages, objective, model):
#     if config.verbose:
#         print("[call_gpt_4_1_with_ocr]")

#     try:
#         time.sleep(1)
#         client = config.initialize_openai()

#         confirm_system_prompt(messages, objective, model)
#         screenshots_dir = "screenshots"
#         if not os.path.exists(screenshots_dir):
#             os.makedirs(screenshots_dir)

#         screenshot_filename = os.path.join(screenshots_dir, "screenshot.png")
#         capture_screen_with_cursor(screenshot_filename)

#         with open(screenshot_filename, "rb") as img_file:
#             img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

#         if len(messages) == 1:
#             user_prompt = get_user_first_message_prompt()
#         else:
#             user_prompt = get_user_prompt()

#         vision_message = {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": user_prompt},
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
#                 },
#             ],
#         }
#         messages.append(vision_message)

#         response = client.chat.completions.create(
#             model="gpt-4.1",
#             messages=messages,
#         )

#         content = response.choices[0].message.content

#         content = clean_json(content)

#         content_str = content

#         content = json.loads(content)

#         processed_content = []

#         for operation in content:
#             if operation.get("operation") == "click":
#                 text_to_click = operation.get("text")
#                 if config.verbose:
#                     print(
#                         "[call_gpt_4_1_with_ocr][click] text_to_click",
#                         text_to_click,
#                     )
#                 reader = easyocr.Reader(["en"])

#                 result = reader.readtext(screenshot_filename)

#                 text_element_index = get_text_element(
#                     result, text_to_click, screenshot_filename
#                 )
#                 coordinates = get_text_coordinates(
#                     result, text_element_index, screenshot_filename
#                 )

#                 operation["x"] = coordinates["x"]
#                 operation["y"] = coordinates["y"]

#                 if config.verbose:
#                     print(
#                         "[call_gpt_4_1_with_ocr][click] text_element_index",
#                         text_element_index,
#                     )
#                     print(
#                         "[call_gpt_4_1_with_ocr][click] coordinates",
#                         coordinates,
#                     )
#                     print(
#                         "[call_gpt_4_1_with_ocr][click] final operation",
#                         operation,
#                     )
#                 processed_content.append(operation)

#             else:
#                 processed_content.append(operation)

#         assistant_message = {"role": "assistant", "content": content_str}
#         messages.append(assistant_message)

#         return processed_content

#     except Exception as e:
#         print(
#             f"[Self-Operating Computer][{model}] That did not work. Trying another method"
#         )
#         if config.verbose:
#             print("[Self-Operating Computer][Operate] error", e)
#             traceback.print_exc()
#         return gpt_4_fallback(messages, objective, model)


# async def call_o1_with_ocr(messages, objective, model):
#     if config.verbose:
#         print("[call_o1_with_ocr]")

#     # Construct the path to the file within the package
#     try:
#         time.sleep(1)
#         client = config.initialize_openai()

#         confirm_system_prompt(messages, objective, model)
#         screenshots_dir = "screenshots"
#         if not os.path.exists(screenshots_dir):
#             os.makedirs(screenshots_dir)

#         screenshot_filename = os.path.join(screenshots_dir, "screenshot.png")
#         # Call the function to capture the screen with the cursor
#         capture_screen_with_cursor(screenshot_filename)

#         with open(screenshot_filename, "rb") as img_file:
#             img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

#         if len(messages) == 1:
#             user_prompt = get_user_first_message_prompt()
#         else:
#             user_prompt = get_user_prompt()

#         vision_message = {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": user_prompt},
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
#                 },
#             ],
#         }
#         messages.append(vision_message)

#         response = client.chat.completions.create(
#             model="o1",
#             messages=messages,
#         )

#         content = response.choices[0].message.content

#         content = clean_json(content)

#         # used later for the messages
#         content_str = content

#         content = json.loads(content)

#         processed_content = []

#         for operation in content:
#             if operation.get("operation") == "click":
#                 text_to_click = operation.get("text")
#                 if config.verbose:
#                     print(
#                         "[call_o1_with_ocr][click] text_to_click",
#                         text_to_click,
#                     )
#                 # Initialize EasyOCR Reader
#                 reader = easyocr.Reader(["en"])

#                 # Read the screenshot
#                 result = reader.readtext(screenshot_filename)

#                 text_element_index = get_text_element(
#                     result, text_to_click, screenshot_filename
#                 )
#                 coordinates = get_text_coordinates(
#                     result, text_element_index, screenshot_filename
#                 )

#                 # add `coordinates`` to `content`
#                 operation["x"] = coordinates["x"]
#                 operation["y"] = coordinates["y"]

#                 if config.verbose:
#                     print(
#                         "[call_o1_with_ocr][click] text_element_index",
#                         text_element_index,
#                     )
#                     print(
#                         "[call_o1_with_ocr][click] coordinates",
#                         coordinates,
#                     )
#                     print(
#                         "[call_o1_with_ocr][click] final operation",
#                         operation,
#                     )
#                 processed_content.append(operation)

#             else:
#                 processed_content.append(operation)

#         # wait to append the assistant message so that if the `processed_content` step fails we don't append a message and mess up message history
#         assistant_message = {"role": "assistant", "content": content_str}
#         messages.append(assistant_message)

#         return processed_content

#     except Exception as e:
#         print(
#             f"[Self-Operating Computer][{model}] That did not work. Trying another method"
#         )
#         if config.verbose:
#             print("[Self-Operating Computer][Operate] error", e)
#             traceback.print_exc()
#         return gpt_4_fallback(messages, objective, model)


# async def call_gpt_4o_labeled(messages, objective, model):
#     time.sleep(1)

#     try:
#         client = config.initialize_openai()

#         confirm_system_prompt(messages, objective, model)
#         file_path = pkg_resources.resource_filename("operate.models.weights", "best.pt")
#         yolo_model = YOLO(file_path)  # Load your trained model
#         screenshots_dir = "screenshots"
#         if not os.path.exists(screenshots_dir):
#             os.makedirs(screenshots_dir)

#         screenshot_filename = os.path.join(screenshots_dir, "screenshot.png")
#         # Call the function to capture the screen with the cursor
#         capture_screen_with_cursor(screenshot_filename)

#         with open(screenshot_filename, "rb") as img_file:
#             img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

#         img_base64_labeled, label_coordinates = add_labels(img_base64, yolo_model)

#         if len(messages) == 1:
#             user_prompt = get_user_first_message_prompt()
#         else:
#             user_prompt = get_user_prompt()

#         if config.verbose:
#             print(
#                 "[call_gpt_4_vision_preview_labeled] user_prompt",
#                 user_prompt,
#             )

#         vision_message = {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": user_prompt},
#                 {
#                     "type": "image_url",
#                     "image_url": {
#                         "url": f"data:image/jpeg;base64,{img_base64_labeled}"
#                     },
#                 },
#             ],
#         }
#         messages.append(vision_message)

#         response = client.chat.completions.create(
#             model="gpt-4o",
#             messages=messages,
#             presence_penalty=1,
#             frequency_penalty=1,
#         )

#         content = response.choices[0].message.content

#         content = clean_json(content)

#         assistant_message = {"role": "assistant", "content": content}

#         messages.append(assistant_message)

#         content = json.loads(content)
#         if config.verbose:
#             print(
#                 "[call_gpt_4_vision_preview_labeled] content",
#                 content,
#             )

#         processed_content = []

#         for operation in content:
#             print(
#                 "[call_gpt_4_vision_preview_labeled] for operation in content",
#                 operation,
#             )
#             if operation.get("operation") == "click":
#                 label = operation.get("label")
#                 if config.verbose:
#                     print(
#                         "[Self Operating Computer][call_gpt_4_vision_preview_labeled] label",
#                         label,
#                     )

#                 coordinates = get_label_coordinates(label, label_coordinates)
#                 if config.verbose:
#                     print(
#                         "[Self Operating Computer][call_gpt_4_vision_preview_labeled] coordinates",
#                         coordinates,
#                     )
#                 image = Image.open(
#                     io.BytesIO(base64.b64decode(img_base64))
#                 )  # Load the image to get its size
#                 image_size = image.size  # Get the size of the image (width, height)
#                 click_position_percent = get_click_position_in_percent(
#                     coordinates, image_size
#                 )
#                 if config.verbose:
#                     print(
#                         "[Self Operating Computer][call_gpt_4_vision_preview_labeled] click_position_percent",
#                         click_position_percent,
#                     )
#                 if not click_position_percent:
#                     print(
#                         f"[Self-Operating Computer][Error] Failed to get click position in percent. Trying another method"
#                     )
#                     return call_gpt_4o(messages)

#                 x_percent = f"{click_position_percent[0]:.2f}"
#                 y_percent = f"{click_position_percent[1]:.2f}"
#                 operation["x"] = x_percent
#                 operation["y"] = y_percent
#                 if config.verbose:
#                     print(
#                         "[Self Operating Computer][call_gpt_4_vision_preview_labeled] new click operation",
#                         operation,
#                     )
#                 processed_content.append(operation)
#             else:
#                 if config.verbose:
#                     print(
#                         "[Self Operating Computer][call_gpt_4_vision_preview_labeled] .append none click operation",
#                         operation,
#                     )

#                 processed_content.append(operation)

#             if config.verbose:
#                 print(
#                     "[Self Operating Computer][call_gpt_4_vision_preview_labeled] new processed_content",
#                     processed_content,
#                 )
#             return processed_content

#     except Exception as e:
#         print(
#             f"[Self-Operating Computer][{model}] That did not work. Trying another method"
#         )
#         if config.verbose:
#             print("[Self-Operating Computer][Operate] error", e)
#             traceback.print_exc()
#         return call_gpt_4o(messages)


# def call_ollama_llava(messages):
#     if config.verbose:
#         print("[call_ollama_llava]")
#     time.sleep(1)
#     try:
#         model = config.initialize_ollama()
#         screenshots_dir = "screenshots"
#         if not os.path.exists(screenshots_dir):
#             os.makedirs(screenshots_dir)

#         screenshot_filename = os.path.join(screenshots_dir, "screenshot.png")
#         # Call the function to capture the screen with the cursor
#         capture_screen_with_cursor(screenshot_filename)

#         if len(messages) == 1:
#             user_prompt = get_user_first_message_prompt()
#         else:
#             user_prompt = get_user_prompt()

#         if config.verbose:
#             print(
#                 "[call_ollama_llava] user_prompt",
#                 user_prompt,
#             )

#         vision_message = {
#             "role": "user",
#             "content": user_prompt,
#             "images": [screenshot_filename],
#         }
#         messages.append(vision_message)

#         response = model.chat(
#             model="llava",
#             messages=messages,
#         )

#         # Important: Remove the image path from the message history.
#         # Ollama will attempt to load each image reference and will
#         # eventually timeout.
#         messages[-1]["images"] = None

#         content = response["message"]["content"].strip()

#         content = clean_json(content)

#         assistant_message = {"role": "assistant", "content": content}
#         if config.verbose:
#             print(
#                 "[call_ollama_llava] content",
#                 content,
#             )
#         content = json.loads(content)

#         messages.append(assistant_message)

#         return content

#     except ollama.ResponseError as e:
#         print(
#             f"[Self-Operating Computer][Operate] Couldn't connect to Ollama. With Ollama installed, run `ollama pull llava` then `ollama serve`",
#             e,
#         )

#     except Exception as e:
#         print(
#             f"[Self-Operating Computer][llava] That did not work. Trying again",
#             e,
#         )
#         print(
#             f"[Self-Operating Computer][Error] AI response was",
#             content,
#         )
#         if config.verbose:
#             traceback.print_exc()
#         return call_ollama_llava(messages)


# def call_ollama_llava_with_ocr(messages, objective, model):
#     """
#     Вызывает модель Ollama LLaVA и использует OCR для обработки кликов по тексту.
#     """
#     if config.verbose:
#         print("[call_ollama_llava_with_ocr]")
    
#     try:
#         time.sleep(1)
#         # Инициализация модели и подготовка скриншота
#         ollama_model = config.initialize_ollama()
        
#         # Убеждаемся, что используется правильный системный промпт для OCR
#         confirm_system_prompt(messages, objective, model)
        
#         screenshots_dir = "screenshots"
#         if not os.path.exists(screenshots_dir):
#             os.makedirs(screenshots_dir)

#         screenshot_filename = os.path.join(screenshots_dir, "screenshot.png")
#         capture_screen_with_cursor(screenshot_filename)

#         # Формирование промпта для пользователя
#         if len(messages) == 1:
#             user_prompt = get_user_first_message_prompt()
#         else:
#             user_prompt = get_user_prompt()

#         if config.verbose:
#             print("[call_ollama_llava_with_ocr] user_prompt", user_prompt)

#         # Формирование сообщения с картинкой для Ollama
#         vision_message = {
#             "role": "user",
#             "content": user_prompt,
#             "images": [screenshot_filename],
#         }
#         messages.append(vision_message)

#         # Вызов модели
#         response = ollama_model.chat(
#             model="llava", # Убедитесь, что у вас скачана модель llava
#             messages=messages,
#         )

#         # Важно: удаляем путь к картинке из истории сообщений
#         messages[-1]["images"] = None
        
#         # Обработка ответа
#         content = response["message"]["content"].strip()
#         content = clean_json(content)
#         content_str = content  # Сохраняем оригинальный строковый ответ для истории
        
#         try:
#             content = json.loads(content)
#         except json.JSONDecodeError as e:
#             print(f"[Ollama] ERROR: Model did not return valid JSON. Response was: {content}")
#             # Возвращаем пустой список, чтобы избежать сбоя
#             return []

#         # --- НАЧАЛО ЛОГИКИ OCR (как в call_o1_with_ocr) ---
        
#         processed_content = []
#         reader = easyocr.Reader(['en', 'ru']) # Инициализируем OCR

#         for operation in content:
#             if operation.get("operation") == "click":
#                 text_to_click = operation.get("text")
#                 if config.verbose:
#                     print(f"[ollama-ocr][click] text_to_click: '{text_to_click}'")
                
#                 # Запускаем OCR
#                 result = reader.readtext(screenshot_filename)
                
#                 # Находим координаты текста
#                 text_element_index = get_text_element(result, text_to_click, screenshot_filename)
#                 coordinates = get_text_coordinates(result, text_element_index, screenshot_filename)

#                 # Заменяем текст на координаты
#                 operation["x"] = coordinates["x"]
#                 operation["y"] = coordinates["y"]

#                 processed_content.append(operation)
#             else:
#                 # Другие операции добавляем без изменений
#                 processed_content.append(operation)

#         # --- КОНЕЦ ЛОГИКИ OCR ---

#         # Добавляем ответ ассистента в историю для сохранения контекста
#         assistant_message = {"role": "assistant", "content": content_str}
#         messages.append(assistant_message)

#         return processed_content

#     except ollama.ResponseError as e:
#         print(f"[Ollama] ERROR: Couldn't connect to Ollama. Run `ollama serve`.\nDetails: {e}")
#         return [] # Возвращаем пустой список при ошибке

#     except Exception as e:
#         print(f"[Ollama] ERROR: An unexpected error occurred: {e}")
#         if config.verbose:
#             traceback.print_exc()
#         # Можно добавить фоллбэк на GPT-4, если нужно
#         # return gpt_4_fallback(messages, objective, model)
#         return []







# async def call_claude_3_with_ocr(messages, objective, model):
#     if config.verbose:
#         print("[call_claude_3_with_ocr]")

#     try:
#         time.sleep(1)
#         client = config.initialize_anthropic()

#         confirm_system_prompt(messages, objective, model)
#         screenshots_dir = "screenshots"
#         if not os.path.exists(screenshots_dir):
#             os.makedirs(screenshots_dir)

#         screenshot_filename = os.path.join(screenshots_dir, "screenshot.png")
#         capture_screen_with_cursor(screenshot_filename)

#         # downsize screenshot due to 5MB size limit
#         with open(screenshot_filename, "rb") as img_file:
#             img = Image.open(img_file)

#             # Convert RGBA to RGB
#             if img.mode == "RGBA":
#                 img = img.convert("RGB")

#             # Calculate the new dimensions while maintaining the aspect ratio
#             original_width, original_height = img.size
#             aspect_ratio = original_width / original_height
#             new_width = 2560  # Adjust this value to achieve the desired file size
#             new_height = int(new_width / aspect_ratio)
#             if config.verbose:
#                 print("[call_claude_3_with_ocr] resizing claude")

#             # Resize the image
#             img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

#             # Save the resized and converted image to a BytesIO object for JPEG format
#             img_buffer = io.BytesIO()
#             img_resized.save(
#                 img_buffer, format="JPEG", quality=85
#             )  # Adjust the quality parameter as needed
#             img_buffer.seek(0)

#             # Encode the resized image as base64
#             img_data = base64.b64encode(img_buffer.getvalue()).decode("utf-8")

#         if len(messages) == 1:
#             user_prompt = get_user_first_message_prompt()
#         else:
#             user_prompt = get_user_prompt()

#         vision_message = {
#             "role": "user",
#             "content": [
#                 {
#                     "type": "image",
#                     "source": {
#                         "type": "base64",
#                         "media_type": "image/jpeg",
#                         "data": img_data,
#                     },
#                 },
#                 {
#                     "type": "text",
#                     "text": user_prompt
#                     + "**REMEMBER** Only output json format, do not append any other text.",
#                 },
#             ],
#         }
#         messages.append(vision_message)

#         # anthropic api expect system prompt as an separate argument
#         response = client.messages.create(
#             model="claude-3-opus-20240229",
#             max_tokens=3000,
#             system=messages[0]["content"],
#             messages=messages[1:],
#         )

#         content = response.content[0].text
#         content = clean_json(content)
#         content_str = content
#         try:
#             content = json.loads(content)
#         # rework for json mode output
#         except json.JSONDecodeError as e:
#             if config.verbose:
#                 print(
#                     f"[Self-Operating Computer][Error] JSONDecodeError: {e}"
#                 )
#             response = client.messages.create(
#                 model="claude-3-opus-20240229",
#                 max_tokens=3000,
#                 system=f"This json string is not valid, when using with json.loads(content) \
#                 it throws the following error: {e}, return correct json string. \
#                 **REMEMBER** Only output json format, do not append any other text.",
#                 messages=[{"role": "user", "content": content}],
#             )
#             content = response.content[0].text
#             content = clean_json(content)
#             content_str = content
#             content = json.loads(content)

#         if config.verbose:
#             print(
#                 f"[Self-Operating Computer][{model}] content: {content}"
#             )
#         processed_content = []

#         for operation in content:
#             if operation.get("operation") == "click":
#                 text_to_click = operation.get("text")
#                 if config.verbose:
#                     print(
#                         "[call_claude_3_ocr][click] text_to_click",
#                         text_to_click,
#                     )
#                 # Initialize EasyOCR Reader
#                 reader = easyocr.Reader(["en"])

#                 # Read the screenshot
#                 result = reader.readtext(screenshot_filename)

#                 # limit the text to extract has a higher success rate
#                 text_element_index = get_text_element(
#                     result, text_to_click[:3], screenshot_filename
#                 )
#                 coordinates = get_text_coordinates(
#                     result, text_element_index, screenshot_filename
#                 )

#                 # add `coordinates`` to `content`
#                 operation["x"] = coordinates["x"]
#                 operation["y"] = coordinates["y"]

#                 if config.verbose:
#                     print(
#                         "[call_claude_3_ocr][click] text_element_index",
#                         text_element_index,
#                     )
#                     print(
#                         "[call_claude_3_ocr][click] coordinates",
#                         coordinates,
#                     )
#                     print(
#                         "[call_claude_3_ocr][click] final operation",
#                         operation,
#                     )
#                 processed_content.append(operation)

#             else:
#                 processed_content.append(operation)

#         assistant_message = {"role": "assistant", "content": content_str}
#         messages.append(assistant_message)

#         return processed_content

#     except Exception as e:
#         print(
#             f"[Self-Operating Computer][{model}] That did not work. Trying another method"
#         )
#         if config.verbose:
#             print("[Self-Operating Computer][Operate] error", e)
#             traceback.print_exc()
#             print("message before convertion ", messages)

#         # Convert the messages to the GPT-4 format
#         gpt4_messages = [messages[0]]  # Include the system message
#         for message in messages[1:]:
#             if message["role"] == "user":
#                 # Update the image type format from "source" to "url"
#                 updated_content = []
#                 for item in message["content"]:
#                     if isinstance(item, dict) and "type" in item:
#                         if item["type"] == "image":
#                             updated_content.append(
#                                 {
#                                     "type": "image_url",
#                                     "image_url": {
#                                         "url": f"data:image/png;base64,{item['source']['data']}"
#                                     },
#                                 }
#                             )
#                         else:
#                             updated_content.append(item)

#                 gpt4_messages.append({"role": "user", "content": updated_content})
#             elif message["role"] == "assistant":
#                 gpt4_messages.append(
#                     {"role": "assistant", "content": message["content"]}
#                 )

#         return gpt_4_fallback(gpt4_messages, objective, model)


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


# def gpt_4_fallback(messages, objective, model):
#     if config.verbose:
#         print("[gpt_4_fallback]")
#     system_prompt = get_system_prompt("gpt-4o", objective)
#     new_system_message = {"role": "system", "content": system_prompt}
#     # remove and replace the first message in `messages` with `new_system_message`

#     messages[0] = new_system_message

#     if config.verbose:
#         print("[gpt_4_fallback][updated]")
#         print("[gpt_4_fallback][updated] len(messages)", len(messages))

#     return call_gpt_4o(messages)


def confirm_system_prompt(messages, objective, model):
    """
    On `Exception` we default to `call_gpt_4_vision_preview` so we have this function to reassign system prompt in case of a previous failure
    """
    if config.verbose:
        print("[confirm_system_prompt] model", model)

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
