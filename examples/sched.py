import re
from slugify import slugify
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
import requests
from social_image_generator import SocialImageGenerator
from sched_data_interface import SchedDataInterface

from secrets import SCHED_API_KEY

class ConnectImageGenerator:
    """
    This is the ConnectImageGenerator which pulls event
    sessions from Sched.com and uses the SocialImageGenerator
    to generate unique placeholder images.
    """
    def __init__(self):
        self.API_KEY = SCHED_API_KEY
        # Setup a new instance of the SocialImageGenerator object
        self.social_image_generator = SocialImageGenerator(
            {"output": "output", "assets_path": "assets", "template": "/home/kyle/Documents/scripts_and_snippets/ConnectAutomation/social_image_generator/assets/templates/bud20-placeholder.jpg"})
        # Setup SchedDataInterface instance
        data_interface = SchedDataInterface(
            "https://bud20.sched.com", SCHED_API_KEY, "BUD20")
        json_data = data_interface.getSessionsData()
        self.generate(json_data)

    def get_api_results(self, endpoint):
        """
            Gets the results from a specified endpoint
        """
        full_url = self.sched_url + endpoint.format(self.API_KEY)
        try:
            resp = requests.get(url=full_url)
            data = resp.json()
            return data
        except Exception as e:
            print(e)
            return False


    def get_speaker_bio(self, speaker):
        """
        Gets a speaker bio given a speaker speaker object
        """
        # Construct the API Query with the username added.
        api_query = "/api/user/get?api_key={0}&by=username&term=" + \
            speaker["username"] + "&format=json"
        # Get the speaker details
        speaker_details = self.get_api_results(api_query)

        speaker["bio"] = speaker_details["about"]

        return speaker

    def download_speaker_images(self, session_speakers_arr):
        """
            Downloads the session speaker images based on an array of speakers passed in
            Returns: speakers array with downloaded image paths
        """
        for speaker in session_speakers_arr:
            speaker_avatar_url = speaker["avatar"]
            if len(speaker_avatar_url) < 3:
                speaker["image"] = "placeholder.jpg"
            else:
                file_name = self.social_image_generator.grab_photo(
                    speaker_avatar_url, slugify(speaker["name"]))
                speaker["image"] = file_name
        return session_speakers_arr

    def generate(self, json_data):
        """
        This method does the actual generation of images using
        the social_image_generator.
        """
        for session in json_data.values():
            try:
                speaker_avatar_url = session["speakers"][0]["avatar"]
                if len(speaker_avatar_url) < 3:
                    speaker_image = "placeholder.jpg"
                else:
                    file_name = self.social_image_generator.grab_photo(
                        speaker_avatar_url, slugify(session["speakers"][0]["name"]))
                    speaker_image = file_name
                session_speakers = session["speakers"][0]["name"]
            except Exception as e:
                print("{} has no speakers".format(session["name"]))
                speaker_image = "placeholder.jpg"
                session_speakers = "TBC"
            # speakers_list = session["speakers"]
            # Create the image options dictionary
            image_options = {
                "file_name": session["session_id"],
                "elements": {
                    "images": [
                        {
                            "dimensions": {
                                "x": 300,
                                "y": 300
                            },
                            "position": {
                                "x": 820,
                                "y": 80
                            },
                            "image_name": speaker_image,
                            "circle": "True"
                        }
                    ],
                    "text": [
                        {
                            "multiline": "True",
                            "centered": "True",
                            "wrap_width": 28,
                            "value": session_speakers,
                            "position": {
                                "x": [920, 970],
                                "y": 400
                            },
                            "font": {
                                "size": 32,
                                "family": "fonts/Lato-Regular.ttf",
                                "colour": {
                                    "r": 255,
                                    "g": 255,
                                    "b": 255
                                }
                            }
                        },
                        {
                            "multiline": "False",
                            "centered": "False",
                            "wrap_width": 28,
                            "value": session["session_id"],
                            "position": {
                                "x": 80,
                                "y": 340
                            },
                            "font": {
                                "size": 48,
                                "family": "fonts/Lato-Bold.ttf",
                                "colour": {
                                    "r": 255,
                                    "g": 255,
                                    "b": 255
                                }
                            }
                        },
                        {
                            "multiline": "False",
                            "centered": "False",
                            "wrap_width": 28,
                            "value": session["event_type"],
                            "position": {
                                "x": 80,
                                "y": 400
                            },
                            "font": {
                                "size": 28,
                                "family": "fonts/Lato-Bold.ttf",
                                "colour": {
                                    "r": 255,
                                    "g": 255,
                                    "b": 255
                                }
                            }
                        },
                        {
                            "multiline": "True",
                            "centered": "False",
                            "wrap_width": 28,
                            "value": session["session_title"],
                            "position": {
                                "x": 80,
                                "y": 440
                            },
                            "font": {
                                "size": 48,
                                "family": "fonts/Lato-Bold.ttf",
                                "colour": {
                                    "r": 255,
                                    "g": 255,
                                    "b": 255
                                }
                            }
                        }
                    ],
                }
            }
            # Generate the image for each sesssion
            self.social_image_generator.create_image(image_options)


if __name__ == "__main__":
    generator = ConnectImageGenerator()
