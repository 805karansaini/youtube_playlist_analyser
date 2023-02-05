import json
import os
import re
from datetime import timedelta
from googleapiclient.discovery import build
from flask import Flask, Response, request, render_template, url_for
import re
import requests


static_URL = 'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&fields=items/contentDetails/videoId,nextPageToken&key={}&playlistId={}&pageToken='

api_key = os.environ.get('YT_API_KEY')

youtube = build('youtube', 'v3', developerKey=api_key)

# To get the playlistId from the link
def pl_id(playlist_link):
    p_link = re.compile('^([\S]+list=)?([\w_-]+)[\S]*$')
    m_link = p_link.match(playlist_link)
    if m_link:
        return m_link.group(2)
    else:
        return 'invalid_playlist_link'


hours_pattern = re.compile(r'(\d+)H')
minutes_pattern = re.compile(r'(\d+)M')
seconds_pattern = re.compile(r'(\d+)S')

# To seconds_to_time the datetime object into readable time
def seconds_to_time(total_seconds):
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours =  divmod(hours, 24)
    if days == 0:
        if hours == 0:
            if minutes == 0:
                return f'{int(seconds)} Seconds'
            return f'{int(minutes)} Minutes, {int(seconds)} Seconds'
        return f'{int(hours)} Hours, {int(minutes)} Minutes, {int(seconds)} Seconds'
    return f'{int(days)} Days, {int(hours)} Hours, {int(minutes)} Minutes, {int(seconds)} Seconds'

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def home():
    if(request.method == 'GET'):
        return render_template("home.html")
    else :
        # get playlist link/id as input from the form 
        user_link = request.form.get('search_string').strip()
        pl_ID = pl_id(user_link)
        if pl_ID == 'invalid_playlist_link':
            display_text = ["The playlist identified with the request's playlistId parameter cannot be found.", "Please retry again with correct parameters."]
            return render_template("home.html", display_text = display_text)

    vid_counter = 0
    total_seconds = 0
    nextPageToken = None
    next_page = ''   
    chart_data = [ [], [] ]
    while True:
        try:
            temp_req = json.loads(requests.get(static_URL.format(api_key, pl_ID) + next_page).text)
            if "error" in temp_req:
                raise KeyError
        except KeyError:
            display_text = ["The playlist identified with the request's playlistId parameter cannot be found.", "Please retry again with correct parameters."]
            return render_template("home.html", display_text = display_text)
        pl_request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=pl_ID,
                maxResults=50,
                pageToken=nextPageToken
            )

        pl_response = pl_request.execute()
        vid_ids = []
        for item in pl_response['items']:
            vid_ids.append(item['contentDetails']['videoId'])

        vid_request = youtube.videos().list(
                            part="contentDetails",
                            id=','.join(vid_ids)
                        )

        title_request = youtube.videos().list(
                        part="snippet",
                        id=','.join(vid_ids)
                    )


        vid_response = vid_request.execute()
        title_response = title_request.execute()

        for item_time, item_title in zip(vid_response['items'], title_response['items']):
            duration = item_time['contentDetails']['duration']
            
            video_title = item_title['snippet']['title']
            # print(f"Titile is :- {video_title}")
            
            hours = hours_pattern.search(duration)
            minutes = minutes_pattern.search(duration)
            seconds = seconds_pattern.search(duration)

            hours = int(hours.group(1)) if hours else 0
            minutes = int(minutes.group(1)) if minutes else 0
            seconds = int(seconds.group(1)) if seconds else 0

            video_seconds = timedelta(
                hours=hours,
                minutes=minutes,
                seconds=seconds
            ).total_seconds()

            total_seconds += video_seconds
            chart_data[0].append(video_title)
            chart_data[1].append( video_seconds / 60)

        nextPageToken = pl_response.get('nextPageToken')
        vid_counter = len(chart_data[1])
        if not nextPageToken:
            break
        
    display_text = []
    display_text += ['No of videos : ' + str(vid_counter),
        'Average length of a video : ' + seconds_to_time(total_seconds/vid_counter), 
        'Total length of playlist : ' + seconds_to_time(total_seconds), 
        'At 1.25x : ' + seconds_to_time(total_seconds/1.25), 
        'At 1.50x : ' + seconds_to_time(total_seconds/1.5), 
        'At 1.75x : ' + seconds_to_time(total_seconds/1.75), 
        'At 2.00x : ' + seconds_to_time(total_seconds/2)]

    return render_template("home.html", display_text = display_text, chart_data = chart_data)


if __name__ == "__main__":
    app.run(use_reloader=True, debug=False)