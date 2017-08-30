# README

## Overview:
	
Ever wanted a place where you can just write down anything that is on your mind? Ever wanted to read what is on other people's mind? Now you can. Here people are able to register or login. Don't want to register, you still will be able to read any post others have written. But only members of the blog can create, edit, delete their own posts/comments.

## CONTEXT:
1. blog.py
2. index.yaml
3. app.js
4. app.yaml
5. README
6. static(folder)
    1. js(folder)
        1. event.js
    2. main.css
7. templates(folder)
    1. DeletePost.html
    2. post.html
    3. commentview.html
    4. commentpage.html
    5. comment_link.html
    6. commentdelete.html
    7. comment.html
    8. commentedit.html
    9. base.html
    10. jquery-3.1.1.js
    11. front.html
    12. welcome.html
    13. MainPage.html
    14. signup-form.html
    15. login-form.html
    16. EditPage.html
    17. newpost.html
    18. permalink.html

## Requirements:
1. Web Browser
2. google account to have acess to gcloud
3. Gcloud SDK
    1. Following link below will help with all installaing process of gcloud
        * https://drive.google.com/file/d/0Byu3UemwRffDc21qd3duLW9LMm8/view

##Instructions

There are to ways to open project. 
	1. Simply visit the current live version of the app at 
        * https://blog-160619.appspot.com/

	2. To run a version of the blog from your local server then you need following:

A. Need to make sure you have registered for google account if not please register for one.
B. Need to be able to create an App Engine Project from 
    * https://console.cloud.google.com/
C. Download project from
    1. Terminal type gitclone https://github.com/jfinest/multi-blog.git
    2. or from * https://github.com/jfinest/multi-blog.git select download
D. From Terminal/Command line change into the Directory where the project’s file are located.
E. Run command gcloud dev_appserver.py .
F. Now go to localhost://8080 to view app

For a detailed instructions please follow https://drive.google.com/file/d/0Byu3UemwRffDc21qd3duLW9LMm8/view 

## Source that helped with code for this project
1. Part of the CSS style were taken from https://radiant-hamlet-1763.herokuapp.com/, and some button style were taken from bootstrap. 
2. Some Handlers, template codes from udacity lessons