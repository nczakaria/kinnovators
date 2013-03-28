from datetime import datetime
import os
import urllib
import webapp2
import logging

from webapp2_extras import auth
from webapp2_extras import sessions
from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

import json

from google.appengine.api import urlfetch
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

#from gaesessions import get_current_session

# configure the RPX iframe to work with the server were on (dev or real)
ON_LOCALHOST = ('Development' == os.environ['SERVER_SOFTWARE'][:11])
if ON_LOCALHOST:
    import logging
    if os.environ['SERVER_PORT'] == '80':
        BASE_URL = 'localhost'
    else:
        BASE_URL = 'localhost:%s' % os.environ['SERVER_PORT']
else:
    BASE_URL = 'k-sketch-test.appspot.com'
LOGIN_IFRAME = '<iframe src="http://gae-sesssions-demo.rpxnow.com/openid/embed?token_url=http%3A%2F%2F' + BASE_URL + '%2Frpx_response" scrolling="no" frameBorder="no" allowtransparency="true" style="width:400px;height:240px"></iframe>'

# create our own simple users model to track our user's data
class User(db.Model):
    email           = db.EmailProperty()
    display_name    = db.TextProperty()

class BaseHandler(webapp2.RequestHandler):
    """
      BaseHandler for all requests
       Holds the auth and session properties so they are reachable for all requests
    """

    def dispatch(self):
        """
          Save the sessions for preservation across requests
        """
        try:
            response = super(BaseHandler, self).dispatch()
            self.response.write(response)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def session_store(self):
        return sessions.get_store(request=self.request)
    
    @webapp2.cached_property
    def session(self):
      # Returns a session using the default cookie key.
      return self.session_store.get_session()

    @webapp2.cached_property
    def auth_config(self):
      """
        Dict to hold urls for login/logout
      """
      return {
          'login_url': self.uri_for('login'),
          'logout_url': self.uri_for('logout')
      }    
    
class RPXTokenHandler(BaseHandler):
    """Receive the POST from RPX with our user's login information."""
    def post(self):
        token = self.request.get('token')
        url = 'https://rpxnow.com/api/v2/auth_info'
        args = {
            'format': 'json',
            'apiKey': '5fa9fabfa1141896e2d4025efd640ea5c1f54776',
            'token': token
        }
        r = urlfetch.fetch(url=url,
                           payload=urllib.urlencode(args),
                           method=urlfetch.POST,
                           headers={'Content-Type':'application/x-www-form-urlencoded'})
        json_data = json.loads(r.content)

        if json_data['stat'] == 'ok':
          # extract some useful fields
          info = json_data['profile']
          oid = info['identifier']
          email = info.get('email', '')
          try:
            display_name = info['displayName']
          except KeyError:
            display_name = email.partition('@')[0]

          # check if there is a user present with that auth_id
          user = self.auth.store.user_model.get_by_auth_id(oid)
          if not user:
            success, user = self.auth.store.user_model.create_user(oid, email=email, display_name=display_name)
            logging.info('New user created in the DS')
            
          userid = user.get_id()
          token = self.auth.store.user_model.create_auth_token(userid)
          self.auth.get_user_by_token(userid, token)
          logging.info('The user is already present in the DS')
          
          # assign a session
          self.session.add_flash('You have successfully logged in', 'success')
          self.redirect('/')
        else:
          self.session.add_flash('There was an error while processing the login', 'error')
          self.redirect('/')

class GetUser(BaseHandler):
    """Class which handles bootstrap procedure and seeds the necessary
    entities in the datastore.
    """
        
    def respond(self,result):
        """Returns a JSON response to the client.
        """
        callback = self.request.get('callback')
        self.response.headers['Content-Type'] = 'application/json'
        #self.response.headers['Content-Type'] = '%s; charset=%s' % (config.CONTENT_TYPE, config.CHARSET)
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD'
        self.response.headers['Access-Control-Allow-Headers'] = 'Origin, Content-Type, X-Requested-With'
        self.response.headers['Access-Control-Allow-Credentials'] = 'True'

        #Add a handler to automatically convert datetimes to ISO 8601 strings. 
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        if callback:
            content = str(callback) + '(' + json.dumps(result,default=dthandler) + ')'
            return self.response.out.write(content)
            
        return self.response.out.write(json.dumps(result,default=dthandler)) 
        
    def get(self):
      result = {'u_login': bool(False)}
      auser = self.auth.get_user_by_session()
      userid = auser['user_id']
      if userid:
        user = User.get_by_id(userid)
        if user:
          result = {'u_login': bool(True),
                      'u_name': user.display_name,
                      'u_email': user.email}
      return self.respond(result)   

class LogoutPage(BaseHandler):
    def get(self):
      self.auth.unset_session()
      # User is logged out, let's try redirecting to login page
      try:
          self.redirect(self.auth_config['login_url'])
      except (AttributeError, KeyError), e:
          return "User is logged out"

webapp2_config = {}
webapp2_config['webapp2_extras.sessions'] = {
		'secret_key': 'n\xd99\xd4\x01Y\xea5/\xd0\x8e\x1ba\\:\x91\x10\x16\xbcTA\xe0\x87lf\xfb\x0e\xd2\xc4\x15\\\xaf\xb0\x91S\x12_\x86\t\xadZ\xae]\x96\xd0\x11\x80Ds\xd5\x86.\xbb\xd5\xcbb\xac\xc3T\xaf\x9a+\xc5',
	}

application = webapp2.WSGIApplication([('/getuser', GetUser),
                                      ('/logout', LogoutPage),
                                      ('/janrain', RPXTokenHandler),
                                     ], config=webapp2_config)

def main(): run_wsgi_app(application)
if __name__ == '__main__': main()