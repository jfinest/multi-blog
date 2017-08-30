import os
import re
import random
import hashlib
import hmac
# from user import User
# from post import Post
from string import letters

import webapp2
import jinja2

from google.appengine.ext import db


# The following is allowing for info to be passed into templates but also is the setup for the cookies needed to verify users login

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = 'fart'

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)

class MainPage(BlogHandler):
    def get(self):
        self.render('MainPage.html')

##### user stuff
def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


##### blog stuff

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

# table/entitity schema for Post

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    author_id = db.IntegerProperty()
    like_count = db.IntegerProperty(default = 0)
    dislike_count = db.IntegerProperty(default = 0)

    def render(self, user):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self, user = user)

# the following is where we query to get last 10 post to display

class Likes(db.Model):
    post_id = db.IntegerProperty(required = True)
    user_id = db.IntegerProperty(required = True)
    is_like = db.IntegerProperty(required = True)

    @classmethod
    def like_by_post(cls, post_id):
        u = db.GqlQuery("select * from Likes where post_id = " + post_id + "order by created_on desc")
        return u

    @classmethod
    def already_liked(cls, post_id, user_id):
        u = db.GqlQuery("select * from Likes where post_id = " + post_id + " and user_id = " + user_id)
        return u

class Comment(db.Model):
    comment = db.TextProperty(required= True)
    created_on = db.DateTimeProperty(auto_now_add = True)
    created_id = db.IntegerProperty()
    id_post = db.IntegerProperty()

    def renderd(self, user):
        self._render_text = self.comment.replace('\n', '<br>')
        return render_str("comment.html", c = self, user = user)

    @classmethod
    def by_post_id(cls, post_id):
        i = db.GqlQuery("select * from Comment where id_post = " + post_id + "order by created_on desc")
        return i

class BlogFront(BlogHandler):
    def get(self):
        if self.user:
            posts = db.GqlQuery("select * from Post order by created desc limit 10")
            self.render('front.html', posts = posts)
        else:
            self.redirect('/login')

# after newpost is submitted the permalink webpage is rendered.

class PostPage(BlogHandler):
    def get(self, post_id,):
        if self.user:
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)

            if not post:
                self.error(404)
                return

            self.render("permalink.html", post = post, user=self.user)
        else:
            self.redirect('/login')

class CommentPage(BlogHandler):
    def get(self, post_id,):
        if self.user:
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)

            if not post:
                self.error(404)
                return
            else:
                comment = Comment.by_post_id(post_id)
                self.render("comment_link.html", comment=comment, post = post, user=self.user)
        else:
            self.redirect('/login')

# when user wants to edit a blog they created then the following called. Only if user that created the blog is logged in

class CommentOnPost(BlogHandler):
    def get(self, post_id):
        if self.user:
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)

            if not post:
                self.error(404)
                return

            self.render("commentpage.html", post = post, user=self.user)
        else:
            self.redirect('/login')

    def post(self, post_id):
        if not self.user:
            self.redirect('/login')

        comment = self.request.get('comment')
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if comment:
            c = Comment(parent = blog_key(), comment = comment, created_id = self.user.key().id(), id_post = post.key().id())
            c.put()
            self.redirect('/blog')
        else:
            error = "comment needed please!"
            self.render("commentpage.html", error=error)

class EditPage(BlogHandler):
    def get(self, post_id):
        if self.user:
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)

            if not post:
                self.error(404)
                return
            elif post.author_id == self.user.key().id():
                self.render("EditPage.html", post_id = post_id, subject=post.subject, content=post.content)

        else:
            self.redirect("/login")

    def post(self, id_of_post):
        if self.user:
            subject = self.request.get('subject')
            content = self.request.get('content')
            id_of_post = self.request.get('id_of_post')
            key = db.Key.from_path('Post', int(id_of_post), parent=blog_key())
            post = db.get(key)

            if post and (post.author_id == self.user.key().id()):
                if subject and content:
                    post.subject= subject
                    post.content=content
                    post.put()
                    self.redirect('/blog/%s' % str(post.key().id()))
                else:
                    error = "subject and content, are needed! "
                    self.render("EditPage.html", subject=subject, content=content, error=error, post_id=id_of_post)
            else:
                self.redirect('/blog')
        else:
            self.redirect('/login')

class CommentEditPage(BlogHandler):
    def get(self, comment_id):
        if self.user:
            key = db.Key.from_path('Comment', int(comment_id), parent=blog_key())
            comm = db.get(key)

            if not comm:
                self.error(404)
                return
            elif comm.created_id == self.user.key().id():
                self.render("commentedit.html", comment_id=comment_id, comment=comm.comment)

        else:
            self.redirect("/login")

    def post(self, id_of_comment):
        if self.user:
            comment = self.request.get('comment')
            id_of_comment = self.request.get('id_of_comment')
            key = db.Key.from_path('Comment', int(id_of_comment), parent=blog_key())
            comm = db.get(key)

            if comm and (comm.created_id == self.user.key().id()):
                if comment:
                    comm.comment = comment
                    comm.put()
                    self.redirect('/blog/comments/%s' % str(comm.id_post))
                else:
                    error = "Comment is needed! "
                    self.render("commentedit.html", comment_id=id_of_comment, comment=comment, error=error)
            else:
                self.redirect('/blog')
        else:
            self.redirect('/login')    

# Used for when user wants to delete a particular blog.


class DeletePost(BlogHandler):
    def get(self, post_id):
        if self.user:
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)

            if not post:
                self.error(404)
                return

            self.render("DeletePost.html", post = post, user=self.user)
        else:
            self.redirect('/login')

    def post(self, post_id):
        if self.user:
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)
            if post.author_id == self.user.key().id():
                post.delete()
                self.redirect('/blog')
        else:
            self.redirect('/login')

class CommentDeletePage(BlogHandler):
    def get(self, comment_id):
        if self.user:
            key = db.Key.from_path('Comment', int(comment_id), parent=blog_key())
            comm = db.get(key)

            if not comm:
                self.error(404)
                return
            elif comm.created_id == self.user.key().id():
                self.render("commentdelete.html", comment_id=comment_id, comment=comm.comment, comm=comm)    
        else:
            self.redirect('/login')    

    def post(self, comment_id):
        if self.user:
            key = db.Key.from_path('Comment', int(comment_id), parent=blog_key())
            comm = db.get(key)

            if comm.created_id == self.user.key().id():    
                comm.delete()
                self.redirect('/blog')
        else:
            self.redirect('/login')


# When user enters a valid blog(contains subject & content) then its created in the datastore with a value of the user so it can be validated when it comes time to edit/delete posts

class NewPost(BlogHandler):
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/blog')

        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content, author_id = self.user.key().id())
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)

class LikePost(BlogHandler):
    def post(self, post_id):
        if not self.user:
            self.redirect('/login')
        else:
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)
            keyed = db.Key.from_path('Likes', int(post_id), parent=blog_key())
            likedd = db.get(keyed)
            user_id = str(self.user.key().id())
            isLike = self.request.get('isLike')
            l = Likes.already_liked(post_id, user_id).get()
            #start real logic
            retData = {}

            if post and (isLike == '1' or isLike == '0'):
                # first time liking or disliking post logic
                if not l:
                    like = Likes(post_id=int(post_id), user_id=int(user_id), is_like=int(isLike))
                    like.put()
                    if isLike == '1':
                        post.like_count = post.like_count + 1
                        post.put()
                    else:
                        post.dislike_count = post.dislike_count + 1
                        post.put()
                elif (l and (l.is_like == 0) and (isLike == '1')):
                    post.like_count = post.like_count + 1
                    post.dislike_count = post.dislike_count - 1
                    post.put()
                    l.is_like = 1
                    l.put()
                elif (l and (l.is_like == 1) and (isLike == '0')):
                    post.like_count = post.like_count - 1
                    post.dislike_count = post.dislike_count + 1
                    post.put()
                    l.is_like = 0
                    l.put()
                else:
                    return self.write("No Action Applied")
                retData["likes"] = int(post.like_count)
                retData["dislikes"] = int(post.dislike_count)
                return self.write(retData)  
            else:
                return self.write("invalid arguments")
            #return self.write(retData)
            #return self.write("logic ended")


            #end real logic

            # if l and l.user_id: 
            #     return self.write('likes user is :' + str(l.user_id) ) 
            # else:
            #     like = Likes(post_id=int(post_id), user_id=int(user_id), is_like=int(isLike))
            #     like.put()
            #     self.write('Does not exists added like')   
            #if post and ((isLike == '1') or (isLike == '0')):
            #    post.like_count = post.like_count + 1
                # post.dislike_count = blah
            #    post.put()
               #return self.write('Like count is : ' + isLike + ": " + str(post.like_count))
            #else:
            #   return self.write('Doesnt Exists')
            #return self.write("other stuff")

            ##    u = db.GqlQuery(""" Select * from Likes Where post_id = 6333186975989760 """)
                # if Likes.already_liked(post_id, user_id):
            #    for use in u:
            ##        print (use.like_Count)
            ##        if use.like_Count == 0 and use.user_id == self.user.key().id():
            ##            use.like_Count = 1
            ##            use.dislike_Count = 0
            ##            use.put()
            ##            print("it was changed")
            #         if u.like_Count == 1:
            #             print("nothing will happen")
            #         else:
            #             u.like_Count = 1
            #             u.dislike_Count = 0
            #             u.put()
            #             print("values should have swapped")
            #     else:
            #         l = Likes(parent = blog_key(), like_Count = 1, dislike_Count = 0, user_id = self.user.key().id(), post_id = post.key().id())
            #         l.put()
            # else:
            #     print("no post")
            #     self.redirect('/blog')

        # if not self.user:
        #     self.redirect('/login')

        # else:
        #     key = db.Key.from_path("Post", int(post_id), parent=blog_key())
        #     post = db.get(key)
        #     key2 = db.Key.from_path("Likes", int(post_id), parent=blog_key())
        #     liked = db.get(key)
        #     author = post.author_id
        #     current_user = self.user.key().id()
        #     liked.like_Count += 1

        #     counter = liked.like_Count

        #     if author == current_user and current_user not in (Likes.like_by_post(post_id)):
        #         li = Likes(parent = blog_key(), like_Count = counter, post_id = author, user_id = current_user)
        #         li.put()
        #         return self.write("hellol")
        #     else:
        #         self.redirect('/blog')

            # if author == current_user or logged_user in liked.user_id:
            #     self.redirect("/error")
            # else:
            #     post.likes += 1
            #     post.liked_by.append(logged_user)
            #     post.put()
            #     self.redirect("/blog")


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

# In this class this is to verify

class Signup(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username,
                      email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError

class Register(Signup):
    def done(self):
        #make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username = msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/welcome')

# Login method is retrieving what user enters as username & password and verifies that specific user exists.

class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/welcome')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error = msg)

# This logout class is to logout current user. Which calls the logout function from Bloghandler.

class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/login')

class Welcome(BlogHandler):
    def get(self):
        if self.user:
            self.render('welcome.html', username = self.user.name)
        else:
            self.redirect('/signup')


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/blog/editpage/([0-9]+)', EditPage),
                               ('/blog/delete/([0-9]+)', DeletePost),
                               ('/welcome', Welcome),
                               ('/blog/comments/([0-9]+)', CommentPage),
                               ('/blog/add/comments/([0-9]+)', CommentOnPost),
                               ('/blog/comments/([0-9]+)/edit', CommentEditPage),
                               ('/blog/comments/([0-9]+)/delete', CommentDeletePage),
                               ('/blog/like/([0-9]+)', LikePost)
                               ],
                              debug=True)
