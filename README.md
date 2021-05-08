# Summary

Over many years, we've taken thousands upon thousands of pictures of places, family and friends. We pick a handful of the pictures and print them on physical frames.

Most of the pictures get locked away on a phone or a photo sharing site and never seen again.

There are digital frames out there but they're expensive and require a lot of maintenece to crop, label and upload images.

The tools here simplify and automate getting pictures stored in flickr to a standard monitor connected to an inexpensive Raspberry Pi.

# Solution Details

Everyone in our family have Apple iPhones.

Most of the photos are taken in portrait mode and in that mode, the images are in 3:4 aspect ratio.

All of the images are uploaded to Flickr.

The images are displayed on a wide screen monitor mounted in portrait mode. Aspect ratio of the monitor is 9:16.

3:4 image is smaller than 9:16 display. The extra space is at the top and bottom is used to display the location and the date.

## Flickr Information

Flickr comes with extensive API capabilities as well as slew of readily available metadata that is readily available.

In Flickr, images can be assigned one or more tags.

The tools pick up images with a specified tag that is configured later in this document

To determine the location of the image, GPS positioning are used.

Flickr can be configured to automatically retrieve GPS information from new images and store it in easily retrievable metadata attributes. More details further in the document

In addition to built-in metadata, the description field of the images is used to store a few slideshow-specific json-formatted attributes. Namely, the cropping dimensions and location override.

Here's an example metadata that would be stored in the description field

    {"lcrop": 20, "tcrop": 0, "rcrop": 73, "bcrop": 100, "location": "New York"}

Left, Top, Right and Bottom cropping numbers are in percentage points of the image size, rather than in raw pixels.

Location is mainly used for images with no GPS data. If location is specified for an image that has GPS coordinates. GPS data is ignore in generating the location of the image.

This data does not need to be updated manually. Slide Management Web App is used to update it interactively.

## Image Downloader

This tool will search the Flickr account for any images containing the specified tag.

If the metadata of the image contains GPS coordinates, they're used to determine image location

If GPS information is missing from metadata, the original image is downloaded and GPS information is attempted to be retrieved directly from the JPG file.

If the JPG file contains GPS coordinates, these coordinates are then posted back into image metadata on Flickr which can be used in the future.

If no GPS information was available, a tag of "nogps" is added to the image.

If the GPS coordinates are available, reverse geo lookup is performed using Nominatim library to get human readable locations where the image was taken. The location is cached in local location.json file. If any additional images that are taken within 300 meters of the same GPS coordinates will use the cached location information

Next, the tool downloads the highest resolution image from Flickr and stores it on the local disk. Cached images are never re-downloaded again.

Once all the images are downloaded, the slideshow directory is scanned if the slide show image for each of the tagged images is already generated or has an older timestamp than Flickr's lastupdate field.

For any slideshow images that need to be generated, the cropping dimensions are applied if so configured in metadata.

The image is, then, resized to fit into 1080x1920 portrait dimensions. The date taken is added at the bottom of the image.

For location, a simple algorithm is used to pick a short and descriptive name for the image. For US, City name is printed for most locations. For International, Country is printed instead. Please refer to source code for the algorithm

The final image is saved to slideshow folder.

An HTTP post is sent to a configured link to indicate successful completion. Healthchecks.io is a free and simple site that can generate alerts if a certain URL isn't accessed for a period of time.

Finally, **slideshow.sh** is executed to restart the slide show to pick up the new images.

## Slide Management

This Web App simplifies the process of updating images for the slide show.

This tool only needs to be used for images that need to be cropped or their location updated. If GPS coordinates are available and image location is correctly displayed on the slideshow, there's no need to update the image in this Web App.

The App automatically identifies all tagged images from Flickr.

The view of the App is split into two columns.

On the left, the information from Flickr is shown. It includes low resolution image, dates, location, crop dimensions.

On the right, a preview of the image is shown as it would appear on the actual slideshow. This image is cropped and resized to 9:16 aspect ratio. The image in this preview is based off the low resolution image shown on the left. When the image is actually generated by downloader, it will be based on the highest resolution available on Flickr.

Status of a location is shown in four different colors:

* Red (Not Available) - GPS is not in metadata and location override is not set, no location will be shown on the slideshow.

* Green (Available) - GPS coordinates are available in Flickr metadata.

* Blue (Available) - GPS coordinates are not available and location override is set.

* Yellow (Availble) - GPS coordinates are available, but it is overridden with a different value

To edit properties of an image, simply click on that image.
![Edit-Screenshot] (https://raw.githubusercontent.com/vbobrov/slideshow/main/screenshots/slidemgm-edit.jpg)

This will switch the image into crop mode showing the crop box to select which part of the image will be used for the slide show.

Lock Aspect Ratio check box will force the crop box to be in 3:4 aspect ration to match the default aspect of pictures taken by iPhones.

Location text is used to override the value displayed on the slide show.

Save button will save the changes. If the changes are successful the background will switch to green for a few seconds. If the changes fail for any reason, the background will turn red and stay in Edit mode.

Cancel can be pressed to discard any changes.

To speed up operation of the App, metadata retrieved from Flickr is cached on the local disk. There's a button in the menu bar at the top to force a refresh from Flickr. The cache is also discarded after one hour of inactivity.

Also in the menu bar, is the option to change how the images are sorted. By default, images are sorted by last update to show most recent images at the top. When sorting by date taken, instead of page numbers, the pages are in MM/YY format to help identify an approximate page where image would be found.

# Installation and Configuration

## Flickr Preparation

These tools require Flickr API to interface with the data. You can request an API at this page: https://www.flickr.com/services/apps/create/apply/

The API is issue as a pair of values: Key and Secret

In order to allow Flickr to consume GPS coordinates on uploaded images into metadata, enable Import **EXIF location data** in privacy settings: https://www.flickr.com/account/privacy

## Raspberry Pi Configuration

This guide is based Raspbian Buster Desktop Image dated 2021-03-04.

The instructions were tested on a Raspberry Pi 3.

The slideshow and the downloader tool were tested to run on Raspberry Pi Zero without any problems.

Slide Managment website was not tested on Pi Zero. It could work, but I'd imagine it would be very slow.

The device is connected to a monitor with 16:9 aspect ratio, eg. 1920x1080

I'm assuming that the Raspberry PI will be dedicated to the slideshow and we don't need to bother with virtual environments.

### Clone slideshow repository

    pi@raspberrypi:~$ git clone git@github.com:vbobrov/slideshow.git
    pi@raspberrypi:~$ cd slideshow/

### Disable screen blanking

Copy included X11 config file to disable screensaver. This is the same as disabling Screen Blanking in the GUI.

    pi@raspberrypi:~$ sudo cp rpi/10-blanking.conf /etc/X11/xorg.conf.d

### Switch the screen to portait mode

Add display_htmi_rotate=1 (90 degrees) or =3 (270 degrees) to /boot/config.txt depending on how the monitor is mounted

    pi@raspberrypi:~$ grep display_hdmi_rotate /boot/config.txt
    display_hdmi_rotate=3

### Configure slideshow to start on restart

Add /home/pi/slideshow/rpi/slideshow.sh to /etc/xdg/lxsession/LXDE-pi/autostart

    pi@raspberrypi:~$ cat /etc/xdg/lxsession/LXDE-pi/autostart
    @lxpanel --profile LXDE-pi
    @pcmanfm --desktop --profile LXDE-pi
    @xscreensaver -no-splash
    /home/pi/slideshow/rpi/slideshow.sh

### Optionally, turn off the screen overnight

Run crontab -e and add hdmi scripts to run at appropriate time

This example turns off the screen between 9:00 pm and 6:30 am

    0 21 * * * /home/pi/slideshow/rpi/hdmioff.sh
    30 6 * * * /home/pi/slideshow/rpi/hdmion.sh

### Install packages

    pi@raspberrypi:~$ sudo apt install feh apache2 libapache2-mod-wsgi-py3

### Install required python modules

    pi@raspberrypi:~$ cd ~/slideshow/
    pi@raspberrypi:~/slideshow$ python3 -m pip install --upgrade pip
    pi@raspberrypi:~/slideshow$ python3 -m pip install --upgrade -r requirements.txt

### Set downloader parameters
Rename config-example.py to config.py and fill in the required parameters

    pi@raspberrypi:~$ cd slideshow/downloader
    pi@raspberrypi:~$ mv config-example.py config.py
    pi@raspberrypi:~$ cat config.py
    # Fill in flickr API Key and Secret
    flickr_api_key='<Fill  In>'
    flickr_api_secret='<Fill  In>'
    # Image tag identifying images for the slideshow
    slideshow_tag='slides'
    # Flickr Username owner of the slideshow images
    flickr_user_id='<Fill  In>'
    # Healthcheck URL. This url is called at the end of script run.
    # Visit healthcheck.io to create free acount.
    # You can also set this variable to None to disable health checking
    healthcheck_url="https://hc-ping.com/fill-in"

### Flickr authorization
First time downloader script is run, it will require authorization to flicker.

The script will request write access to the Flickr account. It is required to update GPS positions and manage tags

After successful authorization, the script will run and download images with the configured tag.

    pi@raspberrypi:~/slideshow/downloader$ ./picdnload.py
    Browse to: https://www.flickr.com/services/oauth/authorize?oauth_token=snip&perms=write
    Verifier code: 111-111-111
    Processing page 1 of 1
    Download URL for url_4k is https://live.staticflickr.com/65535/snip_4k.jpg
    Saving to 1234_z.jpg
    Slideshow photo needs to be updated
    Photo taken on 02 Jan 2011
    Photo coordinates 11.964427 11.178559
    Photo taken in {'amenity': 'Ericsson Fountain', 'road': 'Spring Garden Tunnel', 'city': 'Philadelphia', 'county': 'Philadelphia County', 'state': 'Pennsylvania', 'postcode': '19104-2892', 'country': 'United States', 'country_code': 'us'}
    Picture location: Philadelphia
    Saving slide show file
    Saving location cache
    Restarting slide show

Verify that an images or images were downloaded

    pi@raspberrypi:~/slideshow/downloader$ ls -l slideshow/
    total 648
    -rw-r--r-- 1 pi pi 662118 May 6 17:28 1234_slideshow.jpg

### Schedule downloader task  

Set downloader to be run periodically through crontab -e
This example runs it every 30 minutes

    0,30 * * * * cd /home/pi/slideshow/downloader;./downloader.py

### Configure apache for Slide Management

The steps below will configure apache with https using self-signed certificate included with Raspberry Pi

The browser will display a certificate warning when accessing this website.

HTTPS is required for Flicker authorization

Rename app-example.wsgi to app.wsgi and update flicker api information

    pi@raspberrypi:~$ cd ~/slideshow/slidemgm/
    pi@raspberrypi:~/slideshow/slidemgm$ mv app-example.wsgi app.wsgi
    pi@raspberrypi:~/slideshow/slidemgm$ cat app.wsgi
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

Activate modules

    pi@raspberrypi:~$ sudo a2enmod ssl rewrite

Copy provided configuration file to apache directory

    pi@raspberrypi:~/slideshow/slidemgm$ sudo cp slidemgm.conf /etc/apache2/sites-enabled/000-default.conf

Restart apache2 service

    pi@raspberrypi:~$ sudo service apache2 restart

Attempt to access https://raspberry-pi-ip.

You should be presented with a login screen. The password is what's configured in app.wsgi file above

Once logged in, you should see a listing of all the images tagged with the the value listed in app.wsgi

If Flicker authorization hasn't been done yet in either downloader tool or the Web App, the browser will redirect to Flicker authorization page to access access to the account.
