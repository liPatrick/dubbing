# Core
from flask import Flask, request

# Repositories
from src.repositories.users import UserRepository
from dubbing_engine.entry import dub_video_entry



# Libs
from dotenv import load_dotenv
import os
import boto3
from dotenv import load_dotenv

# Config App
load_dotenv()
app = Flask(__name__)


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

# Routes
@app.route("/", methods=["GET"])
def hello_word():

    dub_video_entry(hardcoded_video_link)




    return 'Hello World'

@app.route("/video", methods=["POST"])
def dub_video(): 

    json = request.get_json()
    video_link = json["video_link"]

    #dub_video_entry

    return ''



@app.route("/insert", methods=["POST"])
def insert():
    userRepo = UserRepository()
    userRepo.insert_user(request.json["name"])

    return "OK"

