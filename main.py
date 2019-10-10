from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageOps
from urllib import request
import requests
import io
import textwrap
import csv
import os
import pickle
import ast
import re
from slugify import slugify
from urllib.parse import urlparse

class SocialMediaImageAutomation:
    """
    This class is used to generate social media images based on a CSV outputs from
    pathable. It combines the users export and the sessions export to create social
    share images for the website and social media promotion.
    """
    def __init__(self, media_templates, using_api=False, data_src_file_name="sessions.csv", user_src_file_name="users.csv", local_file_folder="resources/",output_path="output/"):

        # Get the data source csv file
        self._data_src_file_name = data_src_file_name
        # Get the data source csv file
        self._user_src_file_name = user_src_file_name
        self.connect_code = "san19"
        self.sched_url = "https://linaroconnectsandiego.sched.com"
        # Local resources directory path
        self.local_resources_path = local_file_folder
        # Local Output path for images
        self.output_path = os.getcwd() + "/" + output_path
        # Circle Thumbnail Size
        self.circle_thumb_size = (300, 300)
        # Sched.com API Key
        self.API_KEY = ""
        # Path to the speaker photos
        self._photos_path = "photos/"
        self.speaker_image_path = "/assets/images/speakers/san19/"
        # Placeholder types supported by the social media image generator
        self._types = ["san19-placeholder.jpg"]

        # Verbose Setting
        self._verbose = True

        # Get the users data
        # Get the sessions data
        # self._sessions_data = self.grab_session_data_from_csv()
        # Grab session data from sched.com api
        self._sessions_data = self.grab_session_data_from_sched()
        self._users_data = self.grab_users_data_from_sched()
        self._sessions_data =  self.generate_revised_sessions(self._users_data)

        # Youtube Thumbnail Image URl
        self.youtube_thumbnail_image = "https://img.youtube.com/vi/{0}/sddefault.jpg"

        # Background image template
        self.template_images = media_templates

        # Offset of the photo
        self.photo_offset = (820,80)
        # Event Hashtag
        self.event_hash_tag = "#YVR18"

        # Define the fonts used when creating the social media graphics
        # These should be in the root of the project or wherever this script is running from.
        self.fonts = {"regular":"Lato-Regular.ttf",
                      "bold":"Lato-Bold.ttf"}


        # Define the colours used when writing text
        self.colours = {"black":(0,0,0),
                        "white":(255,255,255),
                        "grey":(153,153,153),
                        "linaro-blue":(70,145,218)}


        # Create the output path if it does not already exist.
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        for template in self.template_images:
            self.create_social_media_images(template)

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

    def generate_revised_sessions(self, users_data):
        revised_sessions = []
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

            blacklistedTracks =  ["Food & Beverage","Informational"]
            if session_track not in blacklistedTracks:
                # Get the session id from the title
                try:
                    session_id_regex = re.compile('SAN19-[A-Za-z]*[0-9]+K*[0-9]*')
                    print(session_title)
                    session_id = session_id_regex.findall(session_title)[0]
                    session_name = re.sub("SAN19-[A-Za-z]*[0-9]+K*[0-9]*", "", session_title).strip()
                    skipping = False
                # Check to see if a session id exists in the title
                # if not then skip this session - marking as invalid if no session id is present.
                except Exception as e:
                    skipping = True
                    print(e)
            else:
                skipping = True
            if skipping == False:
                # Gather the session speakers details
                if session_speakers is not None:
                    session_speakers_arr = []
                    for speaker in session_speakers:
                        speaker_name = speaker.strip()
                        for speaker_object in users_data:
                            if speaker_object["name"] == speaker_name:
                                session_speakers_arr.append(speaker_object)
                    session_speakers_arr =  self.download_speaker_images(session_speakers_arr)
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
                            "speaker_bio":  "{}".format(speaker_details["bio"]).replace("'",""),
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
                        "description": "{}".format(session_abstract).replace("'",""),
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


    def grab_session_data_from_sched(self):
        """
        Grabs the session data from sched.com api
        """
        sessions = self.get_api_results("/api/session/list?api_key={0}&since=1282755813&format=json")
        return sessions

    def grab_users_data_from_sched(self):
        """
        Grabs the users data from sched.com api
        """
        users_data =  self.get_api_results("/api/user/list?api_key={0}&format=json")
        return users_data

    def get_speaker_bio(self, speaker):
        """
        Gets a speaker bio given a speaker speaker object
        """
        # Construct the API Query with the username added.
        api_query = "/api/user/get?api_key={0}&by=username&term=" + speaker["username"] + "&format=json"
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
                file_name = self.grab_photo(speaker_avatar_url, slugify(speaker["name"]))
                speaker["image"] = file_name
        return session_speakers_arr

    def grab_photo(self, url, output_filename, output_path="speaker_images/"):
        """Fetches attendee photo from the pathable data"""
        # Get the filename parsed in
        file_name = output_filename
        # Extract the path from the URL
        path = urlparse(url).path
        # Get the Extension from the path using os.path.splitext
        ext = os.path.splitext(path)[1]
        # Add output folder to output path
        output =  self._photos_path + file_name + ext
        # Try to download the image and Except errors and return as false.
        try:
            opener = request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            request.install_opener(opener)
            request.urlretrieve(url, output)
        except Exception as e:
            print(e)
            image = False
        return(file_name + ext)

    def grab_session_data_from_csv(self):
        """Fetches the session data from the pathable meetings export"""
        my_file = self._data_src_file_name
        with open(my_file, 'rt',encoding="utf8") as f:
            reader = csv.reader(f)
            csv_data = list(reader)
            data = []
            for each in csv_data:
                title = each[4]
                desc = each[5]
                session_id = each[1]
                speaker_names = each[10]
                tracks = each[7]
                new_dict = {
                    "title":title,
                    "blurb":desc,
                    "session_id":session_id,
                    "speakers":speaker_names,
                    "tracks": tracks
                }
                data.append(new_dict)
                print(new_dict["title"])
        return data

    def grab_user_data_from_csv(self):
        """Fetches the user data from the pathable attendees csv export"""
        my_file = self._user_src_file_name
        with open(my_file, 'rt',encoding="utf8") as f:
            reader = csv.reader(f)
            csv_data = list(reader)
            data = []
            for each in csv_data:
                email = each[12]
                first_name = each[2]
                second_name = each[3]
                title = each[4]
                company = each[6]
                bio = each[7]
                photo_url = each[16]
                new_dict = {
                    "speaker_email":email,
                    "first_name":first_name,
                    "second_name":second_name,
                    "job_title":title,
                    "company": company,
                    "bio": bio,
                    "photo_url": photo_url
                }
                data.append(new_dict)
            # for each in data:
            #     print(each)
            #     input()
        return data

    def get_users(self):
        """ Get the users data from the pickle file or grab from users.csv"""
        users = self.grab_user_data_from_csv()
        # Download attendee photos from pathable.
        for user in users:
            if user["photo_url"]:
                username = user["first_name"] + user["second_name"]
                photo_download = self.grab_photo(user["photo_url"], output_filename=username)
                print(photo_download)
                user["image-name"] = photo_download
                # Dump the data into cache file
        return users


    def get_sessions(self):
        """ Get the sessions data from the pickle file or grab from sessions.csv"""
        sessions = self.grab_session_data_from_csv()
        return sessions

    def write_text(self, background_image_draw, text, coords, font_size, font, colour, centered=False, multiline=False, wrap_width=28):
        """Writes text to an image based on multiple parameters passed in"""

        # Create an ImageFont object based on the font size and the font type we are using.
        # This is used to calculate the dimensions of the text based on a specific size and font.
        image_font = ImageFont.truetype(font, font_size)

        # Check to see if the text is centered and if it is get x coords of the centered text
        if centered:
            # Get the width and height of the text.
            text_width, text_height = image_font.getsize(text)
            # Fetch x coords passed in.
            x = coords[0][0]
            x2 = coords[0][1]
            # Calculate the start of the new line.
            text_x = x + ((x2 - x) - (text_width) / 2)
        else:
            text_x = coords[0]

        # Create a tuple which (x,y) coords needed for the text method.
        text_coords = (text_x,coords[1])

        # Check to see if the text we are writing out should be on multiple lines.
        if multiline == False:
            background_image_draw.text(text_coords, text, colour, font=image_font)
        else:
            # Convert the text into multiple lines
            lines = textwrap.wrap(text, width=wrap_width)
            line_y = text_coords[1]
            for line in lines:
                # Get the width and height of each line.
                width, height = image_font.getsize(line)
                # Check to see if the text we are writing needs to be centered too.
                if centered:
                    # Calculate the width of each line of text in the multline text output
                    x = coords[0][0]
                    x2 = coords[0][1]
                    # Calculate width of each line based on the width of that particular line
                    text_x = x + ((x2 - x) - (width) / 2)
                    background_image_draw.text((text_x,line_y), line, colour, font=image_font)
                else:
                    background_image_draw.text((text_coords[0],line_y), line, colour, font=image_font)
                line_y += height

        return background_image_draw


    def create_social_media_images(self, media_template):
        """Generates the social media images for a given media template based
        on the sessions and users data collected in the constructor"""
        # Iterate through each session in the sessions data
        for session in self._sessions_data:
            # Grab session info from dictionary
            title = session["title"]
            speakers = session['session_speakers']
            session_id = session["session_id"]
            tracks = session["tags"]

            if self._verbose:
                print("Generating image for {}...".format(session_id))
                print(session)


            # tracks = tracks.replace(";",", ")
            # tracks.rsplit(", ")[0]
            # tracks_list = tracks.split(",")


            # speaker_emails = speakers.split(",")
            # # Collect speaker info for each email in speaker_emails
            # speaker_list = []
            # for email in speaker_emails:
            #     for user in self._users_data:
            #         if email == user["speaker_email"]:
            #             speaker_list.append(user)


            # Check to see if the length of the speakers array is greater than 1
            # If length is 1 then create a circular thumbnail and paste on background image
            if speakers:
                # Create circlar thumbnail
                circle_thumb = self.create_circle_thumbnail(self._photos_path + speakers[0]["speaker_image"])
            else:
                circle_thumb = False
            # Open the media template e.g YVR18 placeholder background
            background_image = Image.open(media_template).convert("RGBA")
            # If Circular thumbnail exists then past on background
            if circle_thumb:
                background_image.paste(circle_thumb, self.photo_offset, circle_thumb)
            # Get the draw object from ImageDraw.Draw() method
            background_image_draw = ImageDraw.Draw(background_image)
            # Check if the media_template is a valid type specified in self.types
            if media_template in self._types:
                if media_template == self._types[0]:
                    # Collect string with all speakers and job titles.
                    names_of_speakers = ""
                    # Count the number of speakers
                    speaker_count = 0
                    for speaker in session['session_speakers']:
                        speaker_name_string = speaker["speaker_name"]
                        if speaker["speaker_position"]:
                            speaker_name_string = speaker_name_string + ", " + speaker["speaker_position"]
                            if speaker["speaker_company"]:
                                speaker_name_string = speaker_name_string + " at " + speaker["speaker_company"]
                        elif len(speaker["speaker_company"]) > 2:
                            speaker_name_string = speaker_name_string + " at " + speaker["speaker_company"]

                        names_of_speakers = names_of_speakers +  "{0}, ".format(speaker_name_string)
                        speaker_count += 1
                    print(names_of_speakers)
                    # print("Not Split: ", names_of_speakers)
                    if names_of_speakers.endswith(', '):
                        names_of_speakers = names_of_speakers[:-2]
                    # print("Split: ", names_of_speakers)
                    # Write the names to the background image
                    if len(names_of_speakers) > 30:
                        background_image_draw = self.write_text(background_image_draw, names_of_speakers,[[920,970],400], 22, self.fonts["regular"], self.colours["white"], centered=True, multiline=True)
                    else:
                        background_image_draw = self.write_text(background_image_draw, names_of_speakers,[[920,970],400], 22, self.fonts["regular"], self.colours["white"], centered=True, multiline=True)

                    # Add the session ID to the background image
                    if "SAN19" in session_id:
                        background_image_draw = self.write_text(background_image_draw, session_id,[80, 340],48, self.fonts["bold"], self.colours["white"], centered=False, multiline=False)

                    # Add the tracks
                    background_image_draw = self.write_text(background_image_draw, tracks[0],[80,400],28, self.fonts["bold"], self.colours["white"], centered=False, multiline=False)

                    # Add the title to the background image
                    if len(title) < 40:
                        background_image_draw = self.write_text(background_image_draw, title,[80,440],48, self.fonts["bold"], self.colours["white"], centered=False, multiline=True)
                    else:
                        background_image_draw = self.write_text(background_image_draw, title,[80,440],44, self.fonts["bold"], self.colours["white"], centered=False, multiline=True)

                    # Create the output file name from the session_id and the output_path
                    output_file = self.output_path + session_id + ".png"
                    if self._verbose:
                        print(output_file)
                    # Write the output file
                    background_image.save(output_file, quality=100, format="png")
                else:
                    print("media_tempalte not in self._types")
            else:
                print("No media template")

        return True


    def create_circle_thumbnail(self, file_name):
        """Creates a ciruclar thumbnail given a file name of an image"""
        # Open the speaker image to generate the circular thumb.
        image_obj = Image.open(file_name).convert("RGBA")
        # Create a circle thumbnail file name
        circle_thumbnail_file_name = '{0}-{1}.png'.format(file_name,"circle")
        # Create a new circle thumb mask
        mask = Image.new('L', self.circle_thumb_size, 0)
        # Instantiate Draw() for mask.
        draw = ImageDraw.Draw(mask)
        # Draw a circle with set size and fill.
        draw.ellipse((0, 0) + self.circle_thumb_size, fill=255)
        # Fit the image to the mask
        circle_thumbnail = ImageOps.fit(image_obj, mask.size, centering=(0.5, 0.5))
        circle_thumbnail.putalpha(mask)
        circle_thumbnail.save(circle_thumbnail_file_name, format="png")
        circle_thumb = Image.open(circle_thumbnail_file_name)
        # Return the circular thumbnail
        return circle_thumb


if __name__ == "__main__":

    # Instantiate the class with parameters of your choice
    socailMediaImages = SocialMediaImageAutomation(["san19-placeholder.jpg"], using_api=True)
