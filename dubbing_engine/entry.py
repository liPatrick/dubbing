import yt_dlp 
import subprocess
import replicate
import os
from dotenv import load_dotenv
import requests
import base64
from concurrent.futures import ThreadPoolExecutor
import random
import string


# we do not override the mp4, so make sure we delete it from data before running the script with a new video
def download_video(url):

    download_dest = 'data/original_video.mp4'
    ydl_opts = {
        'format': 'best[ext=mp4]',  # Download best quality mp4 format with audio
        'outtmpl': download_dest,  # Name of the downloaded video
        #'progress_hooks': [download_hook],
        'noplaylist' : True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    separate_audio_and_video(download_dest)

    return download_dest

# def download_hook(d):
#     if d['status'] == 'finished':
#         print("Download finished, now processing the video...")
#         separate_audio_and_video("data/original_video.mp4")

def separate_audio_and_video(input_video: str):
    # Names for output files
    silent_video = 'data/silent_video.mp4'
    audio_output = 'data/original_audio.mp3'
    delete_file("data", "silent_video.mp4")
    delete_file("data", "original_audio.mp3")

    cmd_extract_audio = [
        'ffmpeg',
        '-i', input_video,
        '-q:a', '0',  # Best audio quality
        '-map', 'a',
        audio_output
    ]
    subprocess.run(cmd_extract_audio)

    # Create a silent MP4 by removing the audio stream
    cmd_silent_mp4 = [
        'ffmpeg',
        '-i', input_video,
        '-an',  # Remove audio
        silent_video
    ]
    subprocess.run(cmd_silent_mp4)


    # print('trying to separate')

    # # Extract audio
    # try:
    #     subprocess.run(["ffmpeg", "-i", input_video, audio_output], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # except subprocess.CalledProcessError as e:
    #     print(f"Error occurred while extracting audio:\n{e.stderr.decode('utf8')}")
    #     raise e

    # # Create a silent video
    # try:
    #     subprocess.run(["ffmpeg", "-i", input_video, "-an", silent_video], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # except subprocess.CalledProcessError as e:
    #     print(f"Error occurred while creating silent video:\n{e.stderr.decode('utf8')}")
    #     raise e






def translate_text(block):
    text = block["text"]
    # Assuming you have a function called `translate_to_spanish` that takes a text and returns its translation
    translated_text = translate_to_german(text)
    return {
        "start": block["start"],
        "end": block["end"],
        "text": translated_text
    }

def translate_to_german(text):
    DEEPL_TOKEN = os.environ.get("DEEPL_TOKEN")
    url = "https://api-free.deepl.com/v2/translate"
    headers = {
        "Authorization": f"DeepL-Auth-Key {DEEPL_TOKEN}",
        "User-Agent": "YourApp/1.2.3",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "text": text,
        "target_lang": "DE"  # German
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json()["translations"][0]["text"]

def text_to_audio(text, index, voice_id):
    ELEVEN_LABS_TOKEN = os.environ.get("ELEVEN_LABS_TOKEN")

    CHUNK_SIZE = 1024
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": f"{ELEVEN_LABS_TOKEN}"
    }

    data = {
    "text": text,
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.5
    }
    }

    response = requests.post(url, json=data, headers=headers)
    with open(f'data/audio_chunks_unprocessed/{index}_unprocessed_output.mp3', 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)

def get_voices():
    ELEVEN_LABS_TOKEN = os.environ.get("ELEVEN_LABS_TOKEN")

    url = "https://api.elevenlabs.io/v1/voices"

    headers = {
    "Accept": "application/json",
    "xi-api-key": f"{ELEVEN_LABS_TOKEN}"
    }

    response = requests.get(url, headers=headers)
    return response.text

def add_voice():
    ELEVEN_LABS_TOKEN = os.environ.get("ELEVEN_LABS_TOKEN")

    url = "https://api.elevenlabs.io/v1/voices/add"

    headers = {
    "Accept": "application/json",
    "xi-api-key": f"{ELEVEN_LABS_TOKEN}"
    }

    random_name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))


    data = {
        'name': random_name,
        'labels': '{"accent": "American"}',
        'description': 'Voice description'
    }

    files = [
        ('files', ('original_audio.mp3', open(f'data/original_audio.mp3', 'rb'), 'audio/mpeg')),
    ]

    response = requests.post(url, headers=headers, data=data, files=files)
    return response.json()["voice_id"]

def get_audio_duration(audio_path):
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout)

def resize_audio(audio_path, output_path, target_duration):
    current_duration = get_audio_duration(audio_path)
    tempo = current_duration / target_duration

    # List to hold tempo filters
    tempo_filters = []

    # While tempo is greater than 2, halve it and add a 2x speed-up filter
    while tempo > 2.0:
        tempo_filters.append("atempo=2.0")
        tempo /= 2.0

    # While tempo is less than 0.5, double it and add a 0.5x slowdown filter
    while tempo < 0.5:
        tempo_filters.append("atempo=0.5")
        tempo *= 2.0

    # Add the remaining tempo change
    tempo_filters.append(f"atempo={tempo}")

    # Join the tempo filters
    filter_str = ",".join(tempo_filters)

    cmd = [
        'ffmpeg', 
        '-i', audio_path, 
        '-ar', '44100',  # Set sample rate to 44100 Hz
        '-ac', '2',      # Set channel layout to stereo
        '-filter:a', filter_str, 
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def create_silent_audio(duration, output_file):
    """
    Creates a silent audio file of the specified duration using ffmpeg.

    Parameters:
    - duration (float): Duration of the silent audio in seconds.
    - output_file (str): Name of the output audio file.

    Returns:
    - None
    """
    # Command to generate silent audio using ffmpeg
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", f"anullsrc=r=44100:cl=stereo",
        "-t", str(duration),
        output_file
    ]

    # Execute the command
    subprocess.run(cmd)


def delete_all_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


def delete_file(folder_path, filename):
    file_path = os.path.join(folder_path, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        print(f"The file {filename} does not exist in {folder_path}")




def dub_video_entry(original_video_url: str):

    #download video and separate audio from video
    delete_file("data", "original_video.mp4")
    original_video_path = download_video(original_video_url)

    #get voice from original audio (assuming only one voice)
    voice_id = add_voice()

    #generate text from audio
    output = replicate.run(
        "daanelson/whisperx:9aa6ecadd30610b81119fc1b6807302fd18ca6cbb39b3216f430dcf23618cedd",
        input={"audio": open("data/original_audio.mp3", "rb"), "align_output": True}, 
    )

    
    with ThreadPoolExecutor() as executor: 
        translatedOutput = list(executor.map(translate_text, output))

    translatedOutput = sorted(translatedOutput, key=lambda x: x["start"])
    for i in range(len(translatedOutput)):
        translatedOutput[i]["index"] = i

    
    #translatedOutput = [{'start': 0.228, 'end': 3.51, 'text': ' Miriam fragt: "Hallo Lex.', 'index': 0}, {'start': 3.51, 'end': 9.072, 'text': 'In Ihrem Interview mit Ariana haben Sie erwähnt, dass Leiden gut für die Seele ist.', 'index': 1}, {'start': 9.072, 'end': 11.994, 'text': 'Woher kommt das?', 'index': 2}, {'start': 11.994, 'end': 16.256, 'text': 'Was ist Ihr Glaubenssystem, um Selbstdisziplin und einen starken Charakter zu bewahren, egal was passiert?', 'index': 3}, {'start': 18.192, 'end': 23.456, 'text': ' Ich denke, dass vieles davon sehr persönlich ist, weil man sich selbst kennen muss.', 'index': 4}, {'start': 23.456, 'end': 26.859, 'text': 'Wie ist die Verteilung der Energieniveaus, die Sie haben?', 'index': 5}, {'start': 26.859, 'end': 27.88, 'text': 'Was macht Sie faul?', 'index': 6}, {'start': 27.88, 'end': 28.84, 'text': 'Was regt Sie auf?', 'index': 7}, {'start': 28.84, 'end': 29.781, 'text': 'Was motiviert Sie?', 'index': 8}, {'start': 29.781, 'end': 32.183, 'text': 'Ich denke, das ist von Person zu Person unterschiedlich.', 'index': 9}, {'start': 32.183, 'end': 34.925, 'text': 'Aber es gibt einige Dinge, die ich sagen könnte.', 'index': 10}, {'start': 34.925, 'end': 44.593, 'text': 'Ich denke, ich versuche, jeden Tag etwas Schwieriges zu tun, etwas, das ich nicht tun will.', 'index': 11}, {'start': 46.372, 'end': 58.013, 'text': ' Wirklich, wenn du deinen Geist, dein Ohr für die Momente öffnest, in denen du keine Lust hast, es zu tun,', 'index': 12}, {'start': 60.294, 'end': 62.517, 'text': ' Tun Sie es.', 'index': 13}, {'start': 62.517, 'end': 75.651, 'text': 'Ich denke, diese Art von Dingen trainiert den Verstand auf die richtige Art und Weise, um die Dinge in deinem Leben anzugehen, von denen du weißt, dass du sie tun solltest, die dir aber schwer fallen und die du deshalb versuchst zu vermeiden.', 'index': 14}, {'start': 76.792, 'end': 90.883, 'text': ' Ich meine, diesen Muskel zu trainieren, nicht bei echten Dingen, sondern jeden Tag bei so dummen Dingen wie zum Beispiel, dass ich manchmal eine eiskalte Dusche nehme.', 'index': 15}, {'start': 90.883, 'end': 96.407, 'text': 'Normalerweise frage ich mich: Ist das etwas, worauf ich im Moment wirklich keine Lust habe?', 'index': 16}, {'start': 97.688, 'end': 103.995, 'text': ' Und ich habe eigentlich nie Lust auf eine kalte Dusche, aber es gibt Tage, an denen ich wirklich keine Lust habe, und dann mache ich es eben.', 'index': 17}, {'start': 103.995, 'end': 112.563, 'text': 'Und ich stehe mindestens eine Minute lang eiskalt unter dem Wasser.', 'index': 18}, {'start': 112.563, 'end': 116.047, 'text': 'Manchmal kann es auch einfach nur darum gehen, dass Sie sich schlecht fühlen,', 'index': 19}, {'start': 118.115, 'end': 127.023, 'text': ' Aber wenn ich in ein Starbucks gehe, ist mir nicht danach, zu lächeln oder freundlich zu sein, aber ich tue es trotzdem.', 'index': 20}, {'start': 127.023, 'end': 128.524, 'text': 'Ich habe keine Lust, es zu tun, und tue es trotzdem.', 'index': 21}, {'start': 128.524, 'end': 130.766, 'text': 'Üben Sie also einfach diesen Muskel.', 'index': 22}, {'start': 130.766, 'end': 134.389, 'text': 'Bewegung, verdammt ja, jeden einzelnen Tag.', 'index': 23}, {'start': 134.389, 'end': 136.111, 'text': 'Das tue ich nicht wirklich, vor allem nicht beim Laufen.', 'index': 24}, {'start': 136.111, 'end': 138.273, 'text': 'Ich laufe nicht gerne, deshalb tue ich es ja auch.', 'index': 25}, {'start': 140.12, 'end': 143.603, 'text': ' Ich mag nicht, vor allem nicht, wenn ich anfange zu laufen.', 'index': 26}, {'start': 143.603, 'end': 155.392, 'text': 'Da rauszugehen und die erste Meile, die ersten zwei Meilen zu laufen, ist etwas, das ich im Moment nicht tun will, aber ich tue es.', 'index': 27}, {'start': 155.392, 'end': 161.938, 'text': 'Ich glaube, das sind diese kleinen Momente, es klingt dramatisch, das als Leiden zu bezeichnen, aber,', 'index': 28}, {'start': 163.842, 'end': 188.648, 'text': ' Es ist wirklich dieser Trostkampf, der deinen Verstand so schult, dass du in anderen Dingen, die dich zutiefst begeistern, die langfristig Teil deines Lebens sind, sie langfristig durch die dunklen Teile, durch den Kampf, durch das geistige und körperliche Leiden verfolgen kannst.', 'index': 29}, {'start': 188.648, 'end': 190.788, 'text': 'So mental sind die Selbstzweifel.', 'index': 30}, {'start': 190.788, 'end': 193.229, 'text': 'Es gibt so viele Tage, an denen ich voller Zweifel aufwache.', 'index': 31}, {'start': 194.529, 'end': 205.072, 'text': ' Und ich denke, diese Tage, diese Momente sind nichts, was man ohne Übung auf sich nehmen kann.', 'index': 32}, {'start': 205.072, 'end': 216.695, 'text': 'Vor allem, wenn man schwierige Dinge tut, vor allem, wenn man Dinge tut, die nicht traditionell sind oder so, aber wirklich jeder stößt oft genug an die Wand, wenn man etwas Großes macht.', 'index': 33}, {'start': 219.557, 'end': 225.38, 'text': ' Ich denke, das ist etwas, das man ernst nehmen muss, und man muss üben und üben und üben.', 'index': 34}, {'start': 225.38, 'end': 230.303, 'text': 'Und ein großer Teil der Praxis, zumindest für mich, sind Gewohnheiten.', 'index': 35}, {'start': 230.303, 'end': 243.991, 'text': 'Die meisten Dinge, bei denen ich festgestellt habe, dass ich sie gut kann, und die meisten Dinge, die mir am Herzen liegen und die ich lösen möchte, sind also Dinge, die ich ausnahmslos jeden Tag tue.', 'index': 36}, {'start': 244.971, 'end': 260.298, 'text': ' Für mich ist es besser, jeden Tag eine Minute lang etwas zu tun, ohne Ausnahme, als einmal im Monat einen ganzen Tag lang.', 'index': 37}, {'start': 260.298, 'end': 272.483, 'text': 'Ich glaube, dieses Ritual hat etwas an sich, das die Fähigkeit des Verstandes vervielfacht, die Aufgabe wirklich in ihrer ganzen Tiefe zu erfassen,', 'index': 38}]


    #generate unprocessed audio chunks from translated text. We set 3 because the concurrency rate limit is 3 for the starter plan
    delete_all_files_in_folder("data/audio_chunks_unprocessed")
    with ThreadPoolExecutor(max_workers=3) as executor: 
        executor.map(text_to_audio, [block["text"] for block in translatedOutput], [block["index"] for block in translatedOutput], [voice_id for _ in translatedOutput])
    


    #resize audio chunks to match original audio duration
    delete_all_files_in_folder("data/audio_chunks_resized")
    with ThreadPoolExecutor() as executor: 
        executor.map(resize_audio, [f'data/audio_chunks_unprocessed/{block["index"]}_unprocessed_output.mp3' for block in translatedOutput], [f'data/audio_chunks_resized/{block["index"]}_resized_output.mp3' for block in translatedOutput], [float(block["end"]) - float(block["start"]) for block in translatedOutput])



    #create silent audio chunks to match original audio duration
    durations_list = [] #this is always len(translatedOutput) + 1
    total_duration = get_audio_duration("data/original_audio.mp3")

    less_less_than_zeros = 0
    for i in range(len(translatedOutput)):
        if i == 0:
            if translatedOutput[i]["start"] > 0:
                durations_list.append(translatedOutput[i]["start"])
            else: 
                less_less_than_zeros += 1
                durations_list.append(0.01)
        else:
            if translatedOutput[i]["start"] - translatedOutput[i-1]["end"] > 0:
                durations_list.append(translatedOutput[i]["start"] - translatedOutput[i-1]["end"])
            else: 
                less_less_than_zeros += 1
                durations_list.append(0.01)
    
    if total_duration - translatedOutput[-1]["end"] > 0:
        durations_list.append(total_duration - translatedOutput[-1]["end"])
    else: 
        durations_list.append(0.01)

    delete_all_files_in_folder("data/audio_chunks_silence")
    with ThreadPoolExecutor() as executor: 
        executor.map(create_silent_audio, durations_list, [f'data/audio_chunks_silence/{i}_silent_audio.mp3' for i in range(len(durations_list))])

    

    #combining silent and resized audio chunks 
    audio_chunks_silence = [f'data/audio_chunks_silence/{i}_silent_audio.mp3' for i in range(len(durations_list))]
    audio_chunks_resized = [f'data/audio_chunks_resized/{block["index"]}_resized_output.mp3' for block in translatedOutput]
    
    combined_audio_chunks = []
    for i in range(len(audio_chunks_resized)):
        if durations_list[i] != 0.01:
            combined_audio_chunks.append(audio_chunks_silence[i])
        combined_audio_chunks.append(audio_chunks_resized[i])
    combined_audio_chunks.append(audio_chunks_silence[-1])

    delete_file("data", "concatenated_output.mp3")
    concat_audio_list(combined_audio_chunks)


    #combine silent video and audio
    delete_file("data", "final_video.mp4")
    combine_audio_video('data/silent_video.mp4', 'data/concatenated_output.mp3', 'data/final_video.mp4')

    return "success"


    

def concat_audio_list(audio_files, output_audio='data/concatenated_output.mp3'):
    # Ensure there are at least two files to concatenate
    if len(audio_files) < 2:
        raise ValueError("Provide at least two audio files to concatenate.")

    # Create a temporary file to list the audio files
    with open('temp_list.txt', 'w') as f:
        for audio in audio_files:
            f.write(f"file '{audio}'\n")


    # Use ffmpeg to concatenate the audio files
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', 'temp_list.txt',
        '-c', 'copy',
        output_audio
    ]
    subprocess.run(cmd)

    # Remove the temporary file
    os.remove('temp_list.txt')

    return output_audio

 
def combine_audio_video(video_path, audio_path, output_path):
    cmd = [
        'ffmpeg', 
        '-i', video_path, 
        '-i', audio_path, 
        '-c:v', 'copy', 
        '-c:a', 'aac', 
        '-strict', 'experimental', 
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


    


    # def upload_to_s3(file_name, s3):
    #     try:
    #         s3.upload_file(file_name, BUCKET_NAME, file_name)
    #         print(f"Successfully uploaded {file_name} to {BUCKET_NAME}")
    #     except Exception as e:
    #         print(f"An error occurred: {e}")