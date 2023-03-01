import os
import glob
import json
import flickrapi
import html
import time
import pathlib
import random
from operator import itemgetter
from datetime import datetime,timedelta
from flask import Flask,request,abort,g,Response,jsonify,redirect,url_for,render_template,session,flash,g
from flask_login import LoginManager,login_required,login_user,logout_user,current_user


app=Flask(__name__)
app.secret_key=b'QsGP7ncnr3KXoTfhzaO1'
login = LoginManager(app)
login.login_view = "login"

class User():
    def __init__(self):
        self.is_authenticated=True

    def is_active(self):
        return True

    def get_id(self):
        return 0

@login.user_loader
def load_user(id):
    return User()

@app.before_request
def before_request():
    g.api_key=os.getenv('FLICKR_KEY')
    g.api_secret=os.getenv('FLICKR_SECRET')
    g.token_cache_location=os.getenv('TOKEN_CACHE')
    g.slideshow_tag=os.getenv("SLIDESHOW_TAG")
    g.flickr_user_id=os.getenv("FLICKR_USER_ID")
    g.password=os.getenv("PASSWORD")
    g.search_days=1200
    g.max_photos=3000

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="GET":
        return render_template("login.html")
    else:
        if request.form.get("password")==g.password:
            user=User()
            login_user(user)
            return redirect("/")
        else:
            flash("Invalid password")
            return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Good Bye")
    return render_template('login.html')

@app.route("/edit/<int:page>")
@login_required
def edit_images(page):
    sort=request.args.get("sort")
    photo_filter=request.args.get("filter")
    if request.args.get("refresh"):
        try:
            os.remove(f"/tmp/photo_cache_{session.get('cache_id')}.json")
        except:
            pass
        return(redirect(url_for("edit_images",page=page,sort=sort)))
    now=time.time()
    cache_files=glob.glob("/tmp/photo_cache*.json")
    for file_name in cache_files:
        if now-os.stat(file_name).st_mtime>3600:
            os.remove(file_name)
    photos_per_page=50
    try:
        f=open(f"/tmp/photo_cache_{session.get('cache_id')}.json","r")
        edit_photos=json.loads(f.read())
        f.close()
        pathlib.Path(f"/tmp/photo_cache_{session.get('cache_id')}.json").touch()
    except:
        flickr=flickrapi.FlickrAPI(g.api_key,g.api_secret,format='parsed-json',token_cache_location=g.token_cache_location)
        if not flickr.token_valid(perms='write'):
            return redirect("/flickrlogin")
        edit_photos=[]
        loaded_photos={}
        end_date=datetime.now()
        while end_date.year>=1980:
            while True:
                start_date=end_date-timedelta(days=g.search_days)
                photos=flickr.photos.search(user_id=g.flickr_user_id,min_taken_date=start_date.strftime("%m/%d/%Y 00:00:00"),max_taken_date=end_date.strftime("%m/%d/%Y 23:59:59"),tags=g.slideshow_tag)
                total_photos=photos['photos']['total']
                if total_photos>g.max_photos:
                    g.search_days=int(g.search_days*0.8)
                else:
                    break
            current_page=1
            while total_photos>0:
                photos=flickr.photos.search(user_id=g.flickr_user_id,min_taken_date=start_date.strftime("%m/%d/%Y 00:00:00"),max_taken_date=end_date.strftime("%m/%d/%Y 23:59:59"),page=current_page,per_page=500,tags=g.slideshow_tag,extras='last_update,url_m,description,geo,date_taken')
                if current_page>photos['photos']['pages']:
                    break
                current_page=current_page+1
                for photo in photos['photos']['photo']:
                    if not 'url_m' in photo:
                        continue
                    photo_id=photo['id']
                    if photo_id in loaded_photos:
                        continue
                    loaded_photos[photo_id]=True
                    photo_url=photo['url_m']
                    lastupdate=int(photo['lastupdate'])
                    accuracy=int(photo['accuracy'])
                    date_taken=int(datetime.strptime(photo['datetaken'],"%Y-%m-%d %H:%M:%S").timestamp())
                    try:
                        description=json.loads(html.unescape(photo['description']['_content']))
                        description['location']=description.get('location','')
                        description['lcrop']=description.get('lcrop',0)
                        description['tcrop']=description.get('tcrop',0)
                        description['rcrop']=description.get('rcrop',100)
                        description['bcrop']=description.get('bcrop',100)
                    except:
                        description={"location":"","lcrop":0,"tcrop":0,"rcrop":100,"bcrop":100}
                    edit_photos.append({"id":photo_id,"url":photo_url,"description":description,"accuracy":accuracy,"datetaken":date_taken,"datetaken_str":photo['datetaken'],"lastupdate":lastupdate,"lastupdate_str":datetime.fromtimestamp(lastupdate).strftime('%Y-%m-%d')})
            end_date=start_date-timedelta(days=1)
        session["cache_id"]=f"{random.randint(100000,999999)}"
        f=open(f"/tmp/photo_cache_{session.get('cache_id')}.json","w")
        f.write(json.dumps(edit_photos))
        f.close()
    if photo_filter=="nolocation":
        display_photos=list(filter(lambda d: d['accuracy']==0 and d['description']['location']=="",edit_photos))
    else:
        display_photos=edit_photos
    if not sort:
        sort="lastupdate"
    display_photos=sorted(display_photos,key=itemgetter(sort),reverse=True)
    pages=int(len(display_photos)/photos_per_page)+1
    start_photo=photos_per_page*(page-1)
    page_labels={}
    for page_idx in range(1,pages+1):
        if sort=="datetaken":
            page_labels[page_idx]=datetime.fromtimestamp(display_photos[(page_idx-1)*50]['datetaken']).strftime('%m/%y')
        else:
            page_labels[page_idx]=page_idx
    return(render_template("edit.html",photos=display_photos[start_photo:start_photo+photos_per_page],cur_page=page,pages=pages,page_labels=page_labels,sort=sort))

@app.route("/update/<photo_id>",methods=["POST"])
@login_required
def update_photo(photo_id):
    photo_data=json.loads(request.data)
    if photo_data['location'].strip()=="":
        del photo_data['location']
    if photo_data.get('lcrop')==0 and photo_data.get('tcrop')==0 and photo_data.get('rcrop')==100 and photo_data.get('bcrop')==100:
        del photo_data['lcrop'],photo_data['tcrop'],photo_data['rcrop'],photo_data['bcrop']
    flickr=flickrapi.FlickrAPI(g.api_key,g.api_secret,format='parsed-json',token_cache_location=g.token_cache_location)
    photo_info=flickr.photos.getInfo(photo_id=photo_id)
    try:
        description=json.loads(html.unescape(photo_info['photo']['description']['_content']))
    except:
        description={}
    if description!=photo_data:
        description=photo_data
        flickr.photos.setMeta(photo_id=photo_id,description=html.escape(json.dumps(description)))
        try:
            f=open(f"/tmp/photo_cache_{session.get('cache_id')}.json","r")
            edit_photos=json.loads(f.read())
            f.close()
            pathlib.Path(f"/tmp/photo_cache_{session.get('cache_id')}.json").touch()
            for i,photo in enumerate(edit_photos):
                if photo['id']==photo_id:
                    edit_photos[i]['description']=json.loads(request.data.decode())
                    break
            f=open(f"/tmp/photo_cache_{session.get('cache_id')}.json","w")
            f.write(json.dumps(edit_photos))
            f.close()
        except:
            pass
    return(json.loads(request.data))

@app.route("/flickrlogin")
@login_required
def flickr_login():
    flickr=flickrapi.FlickrAPI(g.api_key,g.api_secret,format='parsed-json',token_cache_location=g.token_cache_location)
    if flickr.token_valid(perms='write'):
        return redirect("/")	
    flickr_auth=url_for("flickr_auth",_external=True)
    flickr.get_request_token(oauth_callback=flickr_auth)
    authorize_url = flickr.auth_url(perms="write")
    session["request_token"] = flickr.flickr_oauth.resource_owner_key
    session["request_token_secret"] = flickr.flickr_oauth.resource_owner_secret
    session["requested_permissions"] = flickr.flickr_oauth.requested_permissions
    return redirect(authorize_url)

@app.route('/flickrauth')
def flickr_auth():
    flickr = flickrapi.FlickrAPI(g.api_key,g.api_secret,token_cache_location=g.token_cache_location)
    flickr.flickr_oauth.resource_owner_key = session['request_token']
    flickr.flickr_oauth.resource_owner_secret = session['request_token_secret']
    flickr.flickr_oauth.requested_permissions = session['requested_permissions']
    verifier = request.args["oauth_verifier"]
    flickr.get_access_token(verifier)
    if flickr.token_valid(perms='write'):
        return redirect("/")
    redirect("/flickrlogin")

@app.route("/")
def home():
    return(redirect(url_for("edit_images",page=1)))

if __name__ == '__main__':
    app.run(host="0.0.0.0")
