import yt_dlp 
#import ffmpeg
import subprocess

#import boto3

# we do not override the mp4, so make sure we delete it from data before running the script with a new video
def download_video(url):

    download_dest = 'data/original_video.mp4'
    ydl_opts = {
        'format': 'best[ext=mp4]',  # Download best quality mp4 format with audio
        'outtmpl': download_dest,  # Name of the downloaded video
        'progress_hooks': [download_hook],
        'noplaylist' : True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return download_dest

def download_hook(d):
    if d['status'] == 'finished':
        print("Download finished, now processing the video...")
        separate_audio_and_video(d['filename'])

def separate_audio_and_video(input_video: str):
    # Names for output files
    silent_video = 'data/silent_video.mp4'
    audio_output = 'data/original_audio.mp3'
    print('trying to separate')

    # Extract audio
    try:
        subprocess.run(["ffmpeg", "-i", input_video, audio_output], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while extracting audio:\n{e.stderr.decode('utf8')}")
        raise e

    # Create a silent video
    try:
        subprocess.run(["ffmpeg", "-i", input_video, "-an", silent_video], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while creating silent video:\n{e.stderr.decode('utf8')}")
        raise e

    return silent_video, audio_output



def dub_video_entry(original_video_url: str):

    print("attempting to dub")

    #download video
    original_video_path = download_video(original_video_url)

    #separate audio from video 
    #silent_video_path, original_audio_path = separate_audio_and_video(original_video_path)
    

    #generate text from audio

    #text translation 

    #text to audio 

    #stich audio with text (try to match the silences)




 



# def upload_to_s3(file_name, s3):
#     try:
#         s3.upload_file(file_name, BUCKET_NAME, file_name)
#         print(f"Successfully uploaded {file_name} to {BUCKET_NAME}")
#     except Exception as e:
#         print(f"An error occurred: {e}")
