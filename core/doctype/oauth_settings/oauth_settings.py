# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import webnotes
import urllib
import json
import gdata
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.tools import run
import oauth2client.client
from oauth2client.client import Credentials
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import logging
from webnotes.model.doc import Document

# The URL root for accessing Google Accounts.
GOOGLE_ACCOUNTS_BASE_URL = 'https://accounts.google.com'


# Hardcoded dummy redirect URI for non-web apps.
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

@webnotes.whitelist()
def get_verification_code(client_id, client_secret,app_name):
	#webnotes.errprint("in the py")
	scope='https://mail.google.com/'
	webnotes.errprint(client_id)
	Url=GeneratePermissionUrl(client_id, scope)
	# webnotes.errprint(Url)
	# Url=genearate_calendar_cred(client_id, client_secret, app_name)
	return Url


def GeneratePermissionUrl(client_id, scope='https://mail.google.com/'):
	#webnotes.errprint('in the generate url')
	params = {}
	params['client_id'] = client_id
	params['redirect_uri'] = REDIRECT_URI
	params['scope'] = scope
	params['response_type'] = 'code'
	return '%s?%s' % (AccountsUrl('o/oauth2/auth'),
	                FormatUrlParams(params))

def FormatUrlParams(params):
	#webnotes.errprint("in the FormatUrlParams")
	param_fragments = []
	for param in sorted(params.iteritems(), key=lambda x: x[0]):
		param_fragments.append('%s=%s' % (param[0],UrlEscape(param[1])))
	return '&'.join(param_fragments)

def AccountsUrl(command):
	#webnotes.errprint("in the account url")
	return '%s/%s' % (GOOGLE_ACCOUNTS_BASE_URL, command)


def UrlEscape(text):
	#webnotes.errprint("in the UrlEscape")
	import urllib
	# See OAUTH 5.1 for a definition of which characters need to be escaped.
	return urllib.quote(text, safe='~-._')

# methods for generate_token
@webnotes.whitelist()
def generate_token(client_id, client_secret, authorization_code,user_name,app_name):
	AuthorizeTokens(client_id,client_secret,authorization_code,user_name)

@webnotes.whitelist()
def generate_token_calender(client_id, client_secret, authorization_code,app_name):
    generate_credentials(client_id, client_secret, authorization_code,app_name)	

	

def AuthorizeTokens(client_id, client_secret, authorization_code,user_name):
	import urllib
	params = {}
	params['client_id'] = client_id
	params['client_secret'] = client_secret
	params['code'] = authorization_code
	params['redirect_uri'] = REDIRECT_URI
	params['grant_type'] = 'authorization_code'
	request_url = AccountsUrl('o/oauth2/token')
	#webnotes.errprint(request_url)
	response_json= urllib.urlopen(request_url, urllib.urlencode(params)).read()
	# webnotes.errprint("authorised token")
	#webnotes.errprint(response_json)
	response=json.loads(response_json)
	# webnotes.errprint(response1)
	access_token=response["access_token"]
	#webnotes.errprint(response["access_token"])
	refresh_token=response["refresh_token"]
	#webnotes.errprint(response["refresh_token"])
	#webnotes.errprint(user_name)
	set_values(access_token,refresh_token,user_name)


def set_values(access_token,refresh_token,user_name):
	#webnotes.errprint("in the set_values")	
	pr = Document('Profile',user_name)
	pr.response = access_token
	pr.refresh_token=refresh_token
	pr.save()
	# webnotes.errprint(pr)

@webnotes.whitelist()
def genearate_calendar_cred(client_id, client_secret, app_name):
	#webnotes.errprint("in the genearate_calendar_cred")

	flow = get_gcalendar_flow(client_id, client_secret, app_name)
	authorize_url = flow.step1_get_authorize_url()
	# return authorize_url
	return {
		"authorize_url": authorize_url,
	}	

def get_gcalendar_flow(client_id, client_secret, app_name):
	#webnotes.errprint("in the get_gcalendar_flow")
	from oauth2client.client import OAuth2WebServerFlow
	if client_secret and client_id and app_name:
		flow = OAuth2WebServerFlow(client_id=client_id, 
			client_secret=client_secret,
			scope='https://www.googleapis.com/auth/calendar',
			redirect_uri='urn:ietf:wg:oauth:2.0:oob',
			user_agent=app_name)
	#webnotes.errprint("flow")	
	#webnotes.errprint(flow)
	# 'https://www.googleapis.com/auth/calendar',
	return flow

@webnotes.whitelist()
def generate_credentials(client_id, client_secret,authorization_code,app_name,user_name):
	#webnotes.errprint("in the generate_credentials")
	flow = get_gcalendar_flow(client_id, client_secret, app_name)
	if authorization_code:
		credentials = flow.step2_exchange(authorization_code)
	final_credentials = credentials.to_json()
	# final_token=json.loads(final_credentials)
	set_values_calender(final_credentials,user_name)
	# webnotes.errprint(type(final_credentials))
	# webnotes.errprint(final_credentials)
	# return{
	# 	'final_credentials': final_credentials
	# }

def set_values_calender(final_credentials,user_name):
	#webnotes.errprint("in the cal set_values")	
	# return json.loads(response)
	cr = Document('Profile',user_name)
	cr.credentails = final_credentials
	cr.save()
	#webnotes.errprint(cr)

