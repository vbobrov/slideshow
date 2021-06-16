#!/usr/bin/env python3
import flickrapi
import os
import logging
import requests
import glob
import re
import json
import pathlib
import html
import sys
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import distance
from PIL import Image,ImageDraw,ImageFont
from PIL.ExifTags import TAGS,GPSTAGS
from config import *

def get_gps(dms_coord,ref):
	gps_coord=round(dms_coord[0]+dms_coord[1]/60.0+dms_coord[2]/3600.0,5)
	if ref in ['S','W']:
		return -gps_coord
	else:
		return gps_coord

pi=os.path.exists("/home/pi")

flickr=flickrapi.FlickrAPI(flickr_api_key,flickr_api_secret,format='parsed-json')
if not flickr.token_valid(perms='write'):
	if os.fstat(0)==os.fstat(1):
		flickr.get_request_token(oauth_callback='oob')
		authorize_url=flickr.auth_url(perms='write')
		print(f"Browse to: {authorize_url}")
		verifier = str(input('Verifier code: '))
		flickr.get_access_token(verifier)
	else:
		raise Exception("Flickr Authorization is required, but output is redirected")

geolocator=Nominatim(user_agent="picdnload")
try:
	f=open("locations.json","r")
	location_cache_text=f.read()
	f.close()
	location_cache=json.loads(location_cache_text)
except FileNotFoundError:
	location_cache_text=""
	location_cache=[]

update_count=0
delete_count=0
downloaded_files=glob.glob("*_z.jpg")
current_page=1
for tag_id in TAGS:
	if TAGS[tag_id]=="GPSInfo":
		gps_tag_id=tag_id
		break
while True:
	photos=flickr.photos.search(user_id=flickr_user_id,page=current_page,per_page=500,extras='last_update,date_taken,url_o,url_6k,url_5k,url_4k,url_3k,url_k,url_h,url_b,url_c,url_z,description,geo,tags',tags=slideshow_tag)
	if current_page>photos['photos']['pages']:
		break
	print(f"Processing page {current_page} of {photos['photos']['pages']}")
	current_page=current_page+1
	for photo in photos['photos']['photo']:
		photo_id=photo['id']
		photo_title=photo['title']
		pic_date=datetime.strptime(photo['datetaken'],"%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")
		try:
			description=json.loads(html.unescape(photo['description']['_content']))
		except:
			description={}
		if not 'jpg' in photo['url_o']:
			print("File is not jpg. Skipping")
			continue
		file_name=None
		if not os.path.exists(f"{photo_id}_z.jpg"):
			for url_name in ["url_6k","url_5k","url_4k","url_3k","url_k","url_h","url_b","url_c","url_z"]:
				if not url_name in photo:
					continue
				url=photo[url_name]
				print(f"Download URL for {url_name} is {url}")
				response=requests.get(url)
				file_name=f"{photo_id}_z.jpg"
				print(f"Saving to {file_name}")
				pic_file=open(file_name,"wb")
				pic_file.write(response.content)
				pic_file.close()
				break
			else:
				print("Image resolution too low. Removing slideshow tag")
				photo_info=flickr.photos.getInfo(photo_id=photo_id)
				for tag in photo_info['photo']['tags']['tag']:
					if tag['raw']==slideshow_tag:
						flickr.photos.removeTag(tag_id=tag['id'])
				break

		gps_lat=None
		gps_lon=None
		if int(photo['accuracy'])==0 and not 'nogps' in photo['tags']:
			url=photo['url_o']
			print(f"Download URL for url_o is {url}")
			image=Image.open(requests.get(url,stream=True).raw)
			exifdata=image._getexif()
			try:
				data=exifdata.get(gps_tag_id)
				latitude_ref=data[1]
				latitude=data[2]
				longitude_ref=data[3]
				longitude=data[4]
				gps_lat=get_gps(latitude,latitude_ref)
				gps_lon=get_gps(longitude,longitude_ref)
				print("GPS information available. Updating photo location.")
				flickr.photos.geo.setLocation(photo_id=photo_id,lat=gps_lat,lon=gps_lon)
			except:
				print("GPS information not available. Setting nogps tag")
				flickr.photos.addTags(photo_id=photo_id,tags='nogps')
		if int(photo['accuracy'])>0:
			gps_lat=float(photo['latitude'])
			gps_lon=float(photo['longitude'])
		if not file_name:
			print(f"{photo_id} already downloaded")
			try:
				downloaded_files.remove(f"{photo_id}_z.jpg")
			except:
				pass
		slide_file=pathlib.Path(f"slideshow/{photo_id}_slideshow.jpg")
		if not slide_file.exists() or int(photo['lastupdate'])>slide_file.stat().st_mtime:
			print(f"Slideshow photo needs to be updated")
			print(f"Photo taken on {pic_date}")
			if 'location' in description:
				pic_location={"override":description['location']}
				print(f"Location override found: {pic_location}")
			elif gps_lat and gps_lon:
				print(f"Photo coordinates {gps_lat} {gps_lon}")
				for location in location_cache:
					location_distance=distance((gps_lat,gps_lon),(location['gps_lat'],location['gps_lon'])).m
					if location_distance<300:
						pic_location=location['address']
						print(f'Found cached location {int(location_distance)}m away')
						break
				else:
					location=geolocator.reverse(f"{gps_lat},{gps_lon}")
					pic_location=location.raw['address']
					location_cache.append({'address':pic_location,"gps_lat":gps_lat,"gps_lon":gps_lon})
			else:
				pic_location=None
			source_image=Image.open(f"{photo_id}_z.jpg")
			if 'lcrop' in description:
				lcrop_px=int(source_image.width*description['lcrop']/100)
				tcrop_px=int(source_image.height*description['tcrop']/100)
				rcrop_px=int(source_image.width*description['rcrop']/100)
				bcrop_px=int(source_image.height*description['bcrop']/100)
				source_image=source_image.crop(box=(lcrop_px,tcrop_px,rcrop_px,bcrop_px))
			display_width=1080
			display_height=1920
			resize_ratio=min(display_width/source_image.width,display_height/source_image.height)
			source_image=source_image.resize((int(source_image.width*resize_ratio),int(source_image.height*resize_ratio)))
			slide_image=Image.new("RGB",(display_width,display_height))
			slide_image.paste(source_image,(int((display_width-source_image.width)/2),int((display_height-source_image.height)/2)))
			draw=ImageDraw.Draw(slide_image)
			font=ImageFont.truetype('OpenSans-Bold.ttf',size=int(slide_image.height*0.07))
			draw.text((int(slide_image.width/2),int(slide_image.height*0.99)),f"{pic_date}",fill='rgb(255,255,255)',font=font,stroke_fill='rgb(0,0,0)',stroke_width=int(slide_image.height*0.004),anchor="md")
			if pic_location:
				print(f"Photo taken in {pic_location}")
				slide_location=""
				if pic_location.get('override'):
					slide_location=pic_location['override']
				elif pic_location.get('country')=="United States":
					for locality in ['town','village','suburb','city','tourism','state']:
						if pic_location.get(locality):
							slide_location=pic_location.get(locality)
							break
				else:
					slide_location=pic_location.get('country')
				slide_location=slide_location.replace(' Township','')
				slide_location=slide_location.replace("Disney's ",'')
				print(f"Picture location: {slide_location}")
				draw.text((int(slide_image.width/2),int(slide_image.height*0.01)),f"{slide_location}",fill='rgb(255,255,255)',font=font,stroke_fill='rgb(0,0,0)',stroke_width=int(slide_image.height*0.004),anchor="ma")
			print("Saving slide show file")
			slide_image.save(f"slideshow/{photo_id}_slideshow.jpg",quality=95)
			update_count=update_count+1
if photos['photos']['pages']>0:
	if len(downloaded_files)<5:
		for file_name in downloaded_files:
			file_re=re.match(r'^(\d+)_\S+(\..*)$',file_name)
			file_prefix=file_re[1]
			file_suffix=file_re[2]
			print(f"Deleting {file_name}")
			try:
				os.remove(f"{file_name}")
			except:
				pass
			print(f"Deleting {file_prefix}_o{file_suffix}")
			try:
				os.remove(f"{file_prefix}_o{file_suffix}")
			except:
				pass
			print(f"Deleting slideshow/{file_prefix}_slideshow{file_suffix}")
			try:
				os.remove(f"slideshow/{file_prefix}_slideshow{file_suffix}")
			except:
				pass
			delete_count=delete_count+1
	else:
		print("Too many images deleted. Stopping")
else:
	print("No images found with the specified tag")
if location_cache_text!=json.dumps(location_cache):
	print("Saving location cache")
	f=open("locations.json","w")
	f.write(json.dumps(location_cache))
	f.close()
else:
	print("Location cache has not changed")
if pi:
	if healthcheck_url:
		requests.post(healthcheck_url,data=f"Updated {update_count} images")
	if update_count:
		print("Restarting slide show")
		os.system("/home/pi/slideshow/rpi/slideshow.sh&")
