import social_image_generator
from secrets import SCHED_API_KEY

class ConnectImageGenerator:
    """
    This is the ConnectImageGenerator which pulls event
    sessions from Sched.com and uses the SocialImageGenerator
    to generate unique placeholder images.
    """
    def __init__(self):

        # Setup a new instance of the SocialImageGenerator object
        self.social_image_generator = SocialImageGenerator()
        self.API_KEY = SCHED_API_KEY  # Sched.com API Key
        self.connect_code = "san19"
        self.sched_url = "https://linaroconnectsandiego.sched.com"
        self._sessions_data = self.grab_session_data_from_sched()
        self.users = {}
        self.grab_users_data_from_sched()
        # Event Hashtag
        self.event_hash_tag = "#YVR18"
        self._sessions_data = self.generate_revised_sessions(self.users)


    def generate(self, sched_sessions):
        """
        This method does the actual generation of images using
        the social_image_generator.
        """
        for session in sched_sessions:



if __name__ == "__main__":
    generator = ConnectImageGenerator()
