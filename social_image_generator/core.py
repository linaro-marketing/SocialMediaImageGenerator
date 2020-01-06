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
from urllib.parse import urlparse


class SocialImageGenerator:
    """
    This class allows you to create an image based on a set of options.
    """

    def __init__(self, options):
        self._verbose = True  # Verbose Setting
        # Set the output path
        if options["output"]:
            if options["output"].endswith("/"):
                self.output_path = os.getcwd() + "/" + options["output"]
            else:
                self.output_path = os.getcwd() + "/" + options["output"] + "/"
        else:
            self.output_path = os.getcwd() + "/output"
        # Check to see if the output path exists and create if not
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        # Set the template
        if "template" in options:
            self.template = options["template"]
        else:
            self.template = "/home/kyle/Documents/scripts_and_snippets/ConnectScripts/SocialMediaImageGenerator/assets/templates/san19-placeholder.jpg"
        # Set the assets path
        if "assets_path" in options:
            if not options["assets_path"].endswith("/"):
                assets_path = options["assets_path"] + "/"
            else:
                assets_path = options["assets_path"]
            self._assets_path = os.getcwd() + "/" + assets_path
        else:
            self._assets_path = os.getcwd() + "/assets/"

        # Defaults
        self.defaults = {
            "text": {
                "font": {
                    "family": "Lato-regular.ttf",
                    "size": "16"
                }
            }
        }

        # Youtube Thumbnail Image URl
        self.youtube_thumbnail_image = "https://img.youtube.com/vi/{0}/sddefault.jpg"
        # Circle Thumbnail Size
        self.circle_thumb_size = (300, 300)
        # Offset of the photo
        self.photo_offset = (820, 80)
        # Define the fonts used when creating the social media graphics
        # These should be in the root of the project or wherever this script is running from.
        self.fonts = {"regular": "Lato-Regular.ttf",
                      "bold": "Lato-Bold.ttf"}
        # Define the colours used when writing text
        self.colours = {"black": (0, 0, 0),
                        "white": (255, 255, 255),
                        "grey": (153, 153, 153),
                        "linaro-blue": (70, 145, 218)}

    def grab_photo(self, url, output_filename, output_path="speaker_images/"):
        """Fetches attendee photo from the pathable data"""
        # Get the filename parsed in
        file_name = output_filename
        # Extract the path from the URL
        path = urlparse(url).path
        # Get the Extension from the path using os.path.splitext
        ext = os.path.splitext(path)[1]
        if ext != ".jpg" or ext != ".png":
            ext = ".jpg"
        # Add output folder to output path
        output = self._assets_path + "images/" + file_name + ext
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


    def draw_image(self, options):
        """Adds an image to the social_image_canvas object"""

        if "position" in options:
            coords = (options["position"]["x"], options["position"]["y"])
        if "dimensions" in options:
            dimensions = (options["dimensions"]["x"], options["dimensions"]["y"])
        if "image_name" in options:
            image_name = options["image_name"]
        if "circle" in options:
            if options["circle"] == "True":
                circle_thumb = True

        if circle_thumb:
            image_to_paste = self.create_circle_thumbnail(
                self._assets_path + "images/" + image_name, dimensions)

        return image_to_paste

    def draw_text(self, social_image_canvas, options):

        """This method draws text to a PIL canvas object and returns the modified canvas"""

        text_multiline = False
        text_centered = False
        font_family = self._assets_path + self.defaults["text"]["font"]["family"]
        font_size = int(self.defaults["text"]["font"]["size"])
        font_colour = self.colours["white"]
        wrap_width = 28
        text = "Text not set"

        # Get the text options
        if "wrap_width" in options:
            wrap_width = options["wrap_width"]
        if "multiline" in options:
            if options["multiline"] == "True":
                text_multiline = True
        if "centered" in options:
            if options["centered"] == "True":
                text_centered = True
        if "font" in options:
            # Get the font family
            if "family" in options["font"]:
                font_family = self._assets_path + options["font"]["family"]
            # Get the font size
            if "size" in options["font"]:
                font_size = int(options["font"]["size"])
            # Get the Font Colour
            if "colour" in options["font"]:
                font_colour = (
                    int(options["font"]["colour"]["r"]),
                    int(options["font"]["colour"]["g"]),
                    int(options["font"]["colour"]["b"])
                                )
        if "value" in options:
            text = options["value"]

        if "position" in options:
            coords = [options["position"]["x"],int(options["position"]["y"])]

        # Create an ImageFont object
        # Used to calculate the dimensions of the text based on a specific size and font.
        image_font = ImageFont.truetype(font_family, font_size)

        # Check to see if the text is centered and if it is get x coords of the centered text
        if text_centered:
            # Get the width and height of the text.
            text_width, text_height = image_font.getsize(str(text))
            # Fetch x coords passed in.
            x = int(coords[0][0])
            x2 = int(coords[0][1])
            # Calculate the start of the new line.
            text_x = x + ((x2 - x) - (text_width) / 2)
        else:
            text_x = int(coords[0])

        # Create a tuple which (x,y) coords needed for the text method.
        text_coords = (text_x, coords[1])

        # Check to see if the text we are writing out should be on multiple lines.
        if text_multiline == False:
            social_image_canvas.text(
                text_coords, text, font_colour, font=image_font)
        else:
            # Convert the text into multiple lines
            lines = textwrap.wrap(text, width=wrap_width)
            line_y = text_coords[1]
            for line in lines:
                # Get the width and height of each line.
                width, height = image_font.getsize(line)
                # Check to see if the text we are writing needs to be centered too.
                if text_centered:
                    # Calculate the width of each line of text in the multline text output
                    x = coords[0][0]
                    x2 = coords[0][1]
                    # Calculate width of each line based on the width of that particular line
                    text_x = x + ((x2 - x) - (width) / 2)
                    social_image_canvas.text(
                        (text_x, line_y), line, font_colour, font=image_font)
                else:
                    social_image_canvas.text(
                        (text_coords[0], line_y), line, font_colour, font=image_font)
                line_y += height

        return social_image_canvas

    def create_image(self, options):
        """Create an image based on an options dictionary"""
        if "template" in options:
            template = options["template"]
        else:
            template = self.template
        # Create a new image with the template base
        social_image = Image.open(template).convert("RGBA")
        social_image_canvas = ImageDraw.Draw(social_image)
        for element in options["elements"]:
            elements = options["elements"][element]
            if element == "text":
                for text_element in elements:
                    social_image_canvas = self.draw_text(
                        social_image_canvas, text_element)
            elif element == "images":
                for image_element in elements:
                    new_image = self.draw_image(image_element)
                    social_image.paste(new_image, (image_element["position"]["x"],image_element["position"]["y"]), new_image)
        # Save the new image
        output_file = self.output_path + options["file_name"] + ".png"
        if self._verbose:
            print(output_file)
        # Write the output file
        social_image.save(
            output_file, quality=100, format="png")

    def create_circle_thumbnail(self, file_path, dimensions):
        """Creates a ciruclar thumbnail given a file name of an image"""
        # Open the speaker image to generate the circular thumb.
        image_obj = Image.open(file_path).convert("RGBA")
        # Create a circle thumbnail file name
        circle_thumbnail_file_name = '{0}-{1}.png'.format(file_path, "circle")
        # Create a new circle thumb mask
        mask = Image.new('L', dimensions, 0)
        # Instantiate Draw() for mask.
        draw = ImageDraw.Draw(mask)
        # Draw a circle with set size and fill.
        draw.ellipse((0, 0) + dimensions, fill=255)
        # Fit the image to the mask
        circle_thumbnail = ImageOps.fit(
            image_obj, mask.size, centering=(0.5, 0.5))
        circle_thumbnail.putalpha(mask)
        circle_thumbnail.save(circle_thumbnail_file_name, format="png")
        circle_thumb = Image.open(circle_thumbnail_file_name)
        # Return the circular thumbnail
        return circle_thumb


if __name__ == "__main__":

    # Instantiate the class with parameters of your choice
    socailMediaImages = SocialImageGenerator(
        ["san19-placeholder.jpg"], using_api=True)
