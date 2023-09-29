# Core
from flask import Flask, request, send_file

# Repositories
from src.repositories.users import UserRepository
from dubbing_engine.entry import dub_video_entry
from flask_cors import CORS



# Libs
from dotenv import load_dotenv
import os
import boto3

# Config App
load_dotenv()
app = Flask(__name__)
CORS(app)



# # Initialize the S3 client
# s3 = boto3.client('s3', 
#                   aws_access_key_id=os.getenv('aws_access_key_id'), 
#                   aws_secret_access_key=os.getenv('aws_secret_access_key'), 
#                   region_name=os.getenv('region')
#                   )

# # Specify the bucket name and file key (file path in the bucket)
# bucket_name = os.getenv('bucket_name')
# file_key = 'YOUR_FILE_PATH_IN_BUCKET'
# download_path = 'LOCAL_PATH_WHERE_YOU_WANT_TO_DOWNLOAD'

# # Download the file
# s3.download_file(bucket_name, file_key, download_path)

hardcoded_video_link = "https://www.youtube.com/watch?v=wKw1tpN7NVE&ab_channel=LexFridman"
another_hardcoded_link = "https://www.youtube.com/watch?v=BeLIisX9n0U&ab_channel=CarsahhBJJRolls"
video_link_3 = "https://www.youtube.com/shorts/ZTg0tPtNc7o"


# Routes
@app.route("/", methods=["GET"])
def hello_word():

    return "Hello World"

    return dub_video_entry(video_link_3)


@app.route("/dub", methods=["POST"])
def dub_video(): 
    json = request.get_json()
    video_link = json["video_link"]
    if len(video_link) == 0:
        return "error"
    #return "success"
    return dub_video_entry(video_link)

@app.route("/video", methods=["GET"])
def get_video(): 

    return send_file("data/final_video.mp4", mimetype="video/mp4")



@app.route("/insert", methods=["POST"])
def insert():
    userRepo = UserRepository()
    userRepo.insert_user(request.json["name"])

    return "OK"

