import os
import time
import google.generativeai as genai
import  requests
from fastapi import FastAPI

app = FastAPI()

genai.configure(api_key="AIzaSyAcJniPvMfJArheINs8yOXOzu7jq0HcFbE")

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

def wait_for_files_active(files):
  """Waits for the given files to be active.

  Some files uploaded to the Gemini API need to be processed before they can be
  used as prompt inputs. The status can be seen by querying the file's "state"
  field.

  This implementation uses a simple blocking polling loop. Production code
  should probably employ a more sophisticated approach.
  """
  print("Waiting for file processing...")
  for name in (file.name for file in files):
    file = genai.get_file(name)
    while file.state.name == "PROCESSING":
      print(".", end="", flush=True)
      time.sleep(10)
      file = genai.get_file(name)
    if file.state.name != "ACTIVE":
      raise Exception(f"File {file.name} failed to process")
  print("...all files ready")
  print()

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
)

def download_video(url, filename):
  """Downloads a video from the given URL and saves it to the given filename."""
  try:
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an exception for bad status codes
    with open(filename, 'wb') as f:
      for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
    print(f"Downloaded video to {filename}")
  except requests.exceptions.RequestException as e:
    print(f"Error downloading video: {e}")

video_urls = [
  "https://res.cloudinary.com/dqneghcme/video/upload/v1722939258/Y2meta.app-This_is_not_Morgan_Freeman_-_A_Deepfake_Singularity-_1080p_veegqk.mp4",
  "https://res.cloudinary.com/dqneghcme/video/upload/v1722931488/9_xibnhz.mp4",
  "https://res.cloudinary.com/dqneghcme/video/upload/v1722931436/lv_0_20240802211151_ll0hvt.mp4",
]

# Tải xuống video và lưu trữ
for i, url in enumerate(video_urls):
  filename = f"video_{i+1}.mp4"
  download_video(url, filename)

# Tạo danh sách file video đã tải xuống
files = [upload_to_gemini(f"video_{i+1}.mp4", mime_type="video/mp4") for i in range(len(video_urls))]

# Some files have a processing delay. Wait for them to be ready.
wait_for_files_active(files)

# chat_session = model.start_chat(
#   history=[
#     {
#       "role": "user",
#       "parts": [
#         files[0],
#       ],
#     },
#     {
#       "role": "model",
#       "parts": [
#         "Video này là một video được tạo ra bởi deepfake. Dù nó rất tinh vi nhưng tôi có thể nhìn ra được",
#       ],
#     },
#     {
#       "role": "user",
#       "parts": [
#         files[1],
#       ],
#     },
#     {
#       "role": "user",
#       "parts": [
#         "Đây là video deepfake hay người thật",
#       ],
#     },
#     {
#       "role": "model",
#       "parts": [
#         "Đây là một video deepfake",
#       ],
#     },
#     {
#       "role": "user",
#       "parts": [
#         files[2],
#       ],
#     },
#   ]
# )

# response = chat_session.send_message("Đây là video deepfake hay người thật, nếu nghi ngờ là deepfake phản hồi 1, nếu là người thật phản hồi 0")

# print(response.text)

def download_video(url, filename):
  """Downloads a video from the given URL and saves it to the given filename."""
  try:
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an exception for bad status codes
    with open(filename, 'wb') as f:
      for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
    print(f"Downloaded video to {filename}")
  except requests.exceptions.RequestException as e:
    print(f"Error downloading video: {e}")


@app.get("/")
async def root(url_video: str):
  filename = f"video_{len(files)}.mp4"
  download_video(url_video, filename)
  
  file22 = upload_to_gemini(filename, mime_type="video/mp4")
  
  wait_for_files_active([file22])
  
  chat_session = model.start_chat(
    history=[
      {
        "role": "user",
        "parts": [
          files[0],
        ],
      },
      {
        "role": "model",
        "parts": [
          "Video này là một video được tạo ra bởi deepfake. Dù nó rất tinh vi nhưng tôi có thể nhìn ra được",
        ],
      },
      {
        "role": "user",
        "parts": [
          files[1],
        ],
      },
      {
        "role": "user",
        "parts": [
          "Đây là video deepfake hay người thật",
        ],
      },
      {
        "role": "model",
        "parts": [
          "Đây là một video deepfake, dù tinh vi nhưng tôi có thể nhận ra được. Người thật có thể dễ dàng nhận thấy hơn",
        ],
      },
      {
        "role": "user",
        "parts": [
          file22,
        ],
      },
    ]
  )
  
  response = chat_session.send_message("Phản hồi nhị phân, Đây là video deepfake hay người thật.")

  os.remove(filename)

  return {"message": response.text}
