import os
# Fill in flickr API Key and Secret
os.environ["FLICKR_KEY"]="<Fill  In>"
os.environ["FLICKR_SECRET"]="<Fill  In>"
# Flickr Username owner of the slideshow images.
# The username can be seen in any image URLs view on flickr.com
os.environ["FLICKR_USER_ID"]="<Fill  In>"
# Image tag identifying images for the slideshow
os.environ["SLIDESHOW_TAG"]="slides"
# Password to login to Slide Management Web App
os.environ["PASSWORD"]="password"
# Leave this unchanged
os.environ["TOKEN_CACHE"]="/home/pi/.flickr"
from app import app as application