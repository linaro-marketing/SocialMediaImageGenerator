import re
from slugify import slugify
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
import requests
from social_image_generator import SocialImageGenerator
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
            {"output": "output", "template": "/home/kyle/Documents/scripts_and_snippets/ConnectScripts/SocialMediaImageGenerator/assets/templates/san19-placeholder.jpg"})
        self.connect_code = "san19"
        self.sched_url = "https://linaroconnectsandiego.sched.com"
        # Users
        self.users = {}
        self.grab_users_data_from_sched()
        # Sessions
        self._sessions_data = self.get_api_results(
            "/api/session/list?api_key={0}&since=1282755813&format=json")
        # self._sessions_data = self.generate_revised_sessions(self.users)
        # Event Hashtag
        self.event_hash_tag = "#YVR18"
        self.generate(self._sessions_data)

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

    def add_user(self, user):
        self.users[user["name"]] = {
            "username": (user["username"]),
            "avatar": user["avatar"],
            "name": user["name"],
            "location": user["location"],
            "company": user["company"],
            "position": user["position"]
        }
        return True

    def merge_user(self, user):
        key = user["name"]
        user_to_modify = self.users[key]
        if user_to_modify["avatar"] != user["avatar"] and user["avatar"] != "":
            user_to_modify["avatar"] = user["avatar"]
        if user_to_modify["company"] != user["company"] and user["company"] != "":
            user_to_modify["company"] = user["company"]
        if user_to_modify["position"] != user["position"] and user["position"] != "":
            user_to_modify["position"] = user["position"]
        return True

    def grab_users_data_from_sched(self):
        """
        Grabs the users data from sched.com api
        """
        users_data = self.get_api_results(
            "/api/user/list?api_key={0}&format=json")
        for user in users_data:
            if user["name"] not in self.users:
                self.add_user(user)
            else:
                self.merge_user(user)
        return users_data


    def generate_revised_sessions(self, users_data):
        revised_sessions = []
        print("Collecting session data for {} sessions...".format(len(self._sessions_data)))
        for session in self._sessions_data:
            # Grab the relevant data from the sessions results
            sched_event_id = session["event_key"]
            session_active = session["active"]
            session_title = session["name"]
            session_start_time = session["event_start"]
            session_end_time = session["event_end"]
            try:
                session_track = session["event_type"]
            except Exception as e:
                session_track = None
            try:
                session_sub_track = session["event_subtype"]
            except KeyError as e:
                session_sub_track = None
            try:
                session_abstract = session["description"]
            except Exception as e:
                session_abstract = "Coming soon..."
            session_attendee_num = session["goers"]
            session_private = session["invite_only"]
            try:
                session_room = session["venue"]
            except Exception as e:
                session_room = None
            try:
                session_venue_id = session["venue_id"]
            except Exception as e:
                pass
            session_id_hash = session["id"]
            try:
                session_speakers = session["speakers"].split(",")
            except KeyError as e:
                session_speakers = None

            blacklistedTracks = ["Food & Beverage", "Informational"]
            if session_track not in blacklistedTracks:
                # Get the session id from the title
                try:
                    session_id_regex = re.compile(
                        'SAN19-[A-Za-z]*[0-9]+K*[0-9]*')
                    print("*", end="", flush=True)
                    session_id = session_id_regex.findall(session_title)[0]
                    session_name = re.sub(
                        "SAN19-[A-Za-z]*[0-9]+K*[0-9]*", "", session_title).strip()
                    skipping = False
                # Check to see if a session id exists in the title
                # if not then skip this session - marking as invalid if no session id is present.
                except Exception as e:
                    skipping = True
            else:
                skipping = True
            if skipping == False:
                # Gather the session speakers details
                if session_speakers is not None:
                    session_speakers_arr = []
                    for speaker in session_speakers:
                        speaker_name = speaker.strip()
                        speaker = users_data[speaker_name]
                        session_speakers_arr.append(speaker)
                    session_speakers_arr = self.download_speaker_images(
                        session_speakers_arr)
                else:
                    with open("missing_speakers.txt", "a+") as my_file:
                        my_file.write(session["name"] + "\n")
                    session_speakers_arr = None

                revised_speakers = []
                if session_speakers_arr != None:
                    for speaker in session_speakers_arr:
                        # Gets the speaker bio
                        speaker_details = self.get_speaker_bio(speaker)
                        revised_speakers.append({
                            "speaker_name": speaker_details["name"],
                            "speaker_username": speaker_details["username"],
                            "speaker_company": speaker_details["company"],
                            "speaker_position": speaker_details["position"],
                            "speaker_location": speaker_details["location"],
                            "speaker_image": speaker_details["image"],
                            "speaker_bio":  "{}".format(speaker_details["bio"]).replace("'", ""),
                        })

                session_image = {
                    "path": "/assets/images/featured-images/san19/" + session_id + ".png",
                    "featured": "true",
                }

                session_slot = {
                    "start_time": session_start_time,
                    "end_time": session_end_time,
                }
                # Session Tracks

                if session_sub_track != None:
                    session_tracks = session_sub_track.split(",")

                if session_track != None:
                    main_track = session_track.strip()

                with open("titles.txt", "a+") as my_file:
                    my_file.write(session_name + "\n")

                post_frontmatter = {
                    "title": session_name,
                    "session_id": session_id,
                    "session_speakers": revised_speakers,
                    "description": "{}".format(session_abstract).replace("'", ""),
                    "future_image": session_image,
                    "session_room": session_room,
                    "session_slot": session_slot,
                    "tags": session_tracks,
                    "categories": [self.connect_code],
                    "session_track": session_track,
                    "session_attendee_num": session_attendee_num,
                    "tag": "session",
                }
                revised_sessions.append(post_frontmatter)

        return revised_sessions

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

    def generate(self, sched_sessions):
        """
        This method does the actual generation of images using
        the social_image_generator.
        """
        # for session in sched_sessions:
        test_session = {'title': 'Opening Keynote', 'session_id': 'SAN19-100K1', 'session_speakers': [{'speaker_name': 'Li Gong', 'speaker_username': 'li.gong', 'speaker_company': 'Linaro', 'speaker_position': 'CEO', 'speaker_location': '', 'speaker_image': 'li-gong.jpg', 'speaker_bio': 'Li Gong is a globally experienced technologist and executive, with deep background in computer science, research and product development, and open source technologies. He has worked in senior leadership roles extensively in the US and in Asia, having served as President and COO at Mozilla Corporation, General Manager at Microsoft, as well as Distinguished Engineer at Sun Microsystems and Distinguished Scientist at SRI International. He graduated from Tsinghua University, Beijing, and received a PhD from University of Cambridge. In 1994 he received the Leonard G. Abraham Prize given by the IEEE Communications Society for “the most significant contribution to technical literature in the field of interest of the IEEE.”'}], 'description': 'Coming soon...', 'future_image': {
            'path': '/assets/images/featured-images/san19/SAN19-100K1.png', 'featured': 'true'}, 'session_room': 'Pacific Room (Keynote)', 'session_slot': {'start_time': '2019-09-23 10:00:00', 'end_time': '2019-09-23 10:45:00'}, 'tags': ['Keynote'], 'categories': ['san19'], 'session_track': 'Keynote', 'session_attendee_num': '154', 'tag': 'session'}
        print(test_session)
        speakers_list = test_session["session_speakers"]

        # Create the image options dictionary
        image_options = {
            "file_name": test_session["session_id"],
            "elements" : {
                "text": [{
                    "multiline": "True",
                    "centered": "True",
                    "wrap_width": 28,
                    "value": "test",
                    "position": {
                        "x": [920,970],
                        "y": 400
                    },
                    "font": {
                        "size": "32",
                        "family": "fonts/Lato-Regular.ttf",
                        "colour": {
                            "r": 255,
                            "g": 255,
                            "b": 255
                        }
                    }
                }],
            }
        }
        # Generate the image for each sesssion
        self.social_image_generator.create_image(image_options)


if __name__ == "__main__":
    generator = ConnectImageGenerator()
