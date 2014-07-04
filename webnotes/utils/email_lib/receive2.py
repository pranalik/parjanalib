#opyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt 

from __future__ import unicode_literals
import time
# import poplib
import webnotes
from webnotes.utils import extract_email_id, convert_utc_to_user_timezone, now, cint
from webnotes.utils.scheduler import log
import re
import imaplib
from mailbox import Mailbox
# from utf import encode as encode_utf7, decode as decode_utf7
# from exceptions import *
# from mailbox import Mailbox

class EmailSizeExceededError(webnotes.ValidationError): pass
class EmailTimeoutError(webnotes.ValidationError): pass
class TotalSizeExceededError(webnotes.ValidationError): pass

class IncomingMail:
	"""
		Single incoming email object. Extracts, text / html and attachments from the email
	"""
	def __init__(self, content):
		import email, email.utils
		import datetime
		# print 'content start'
		# print content
		# print 'content end'
		self.mail = email.message_from_string(content)
		
		self.text_content = ''
		self.html_content = ''
		self.attachments = []	
		self.parse()
		self.set_content_and_type()
		self.set_subject()

		self.from_email = extract_email_id(self.mail["From"])
		self.from_real_name = email.utils.parseaddr(self.mail["From"])[0]
		
		if self.mail["Date"]:
			utc = time.mktime(email.utils.parsedate(self.mail["Date"]))
			utc_dt = datetime.datetime.utcfromtimestamp(utc)
			self.date = convert_utc_to_user_timezone(utc_dt).strftime('%Y-%m-%d %H:%M:%S')
			
		else:
			self.date = now()

	def parse(self):
		# print "in the parse method"
		for part in self.mail.walk():
			# print 'part'
			# print part
			self.process_part(part)

	def set_subject(self):
		# print "In the set subject method"
		import email.header
		_subject = email.header.decode_header(self.mail.get("Subject", "No Subject"))
		self.subject = _subject[0][0] or ""
		if _subject[0][1]:
			self.subject = self.subject.decode(_subject[0][1])
		else:
			# assume that the encoding is utf-8
			self.subject = self.subject.decode("utf-8")
			
		if not self.subject:
			self.subject = "No Subject"
			
	def set_content_and_type(self):
		# print "In the set content method"
		# print 'self.content_type'
		# print self.content_type
		# print"--------------------------------------------------------------------------------"
		self.content, self.content_type = '[Blank Email]', 'text/plain'
		# print 'self.text_content'
		if self.text_content:
			# print "in the plan text-----------------------------------------"
			self.content, self.content_type = self.text_content, 'text/plain'
		else:
			# print "in the html text00000000000000000000000000000000000000000000000000000"
			self.content, self.content_type = self.html_content, 'text/html'
		self.text_content=''	
		
	def process_part(self, part):
		# print "In the  process part method"
		content_type = part.get_content_type()
		# print 'content_type'
		# print content_type
		charset = part.get_content_charset()
		if not charset: charset = self.get_charset(part)

		if content_type == 'text/plain':
			# print "in the text"
			# print part
			self.text_content += self.get_payload(part, charset)

		if content_type == 'text/html':
			# print "in the html         ",part
			self.html_content += self.get_payload(part, charset)

		if part.get_filename():
			self.get_attachment(part, charset)

	def get_text_content(self):
		# print "In the get_text_content method"
		return self.text_content or self.html_content

	def get_charset(self, part):
		# print "In the get_charset method"

		charset = part.get_content_charset()
		if not charset:
			import chardet
			charset = chardet.detect(str(part))['encoding']

		return charset
			
	def get_payload(self, part, charset):
		try:
			return unicode(part.get_payload(decode=True),str(charset),"ignore")
		except LookupError:
			return part.get_payload()		

	def get_attachment(self, part, charset):
		self.attachments.append({
			'content-type': part.get_content_type(),
			'filename': part.get_filename(),
			'content': part.get_payload(decode=True),
		})
	
	def save_attachments_in_doc(self, doc):
		from webnotes.utils.file_manager import save_file, MaxFileSizeReachedError
		for attachment in self.attachments:
			try:
				fid = save_file(attachment['filename'], attachment['content'], 
					doc.doctype, doc.name)
			except MaxFileSizeReachedError:
				# WARNING: bypass max file size exception
				pass
			except webnotes.DuplicateEntryError:
				# same file attached twice??
				pass

	def get_thread_id(self):
	# print "in the get_thread_id"
		import re
		l = re.findall('(?<=\[)[\w/-]+', self.subject)
		return l and l[0] or None


class IMAPMailbox:
	# GMail IMAP defaults
	GMAIL_IMAP_HOST = 'imap.gmail.com'
	GMAIL_IMAP_PORT = 993
	GMAIL_SMTP_HOST = "smtp.gmail.com"
	GMAIL_SMTP_PORT = 587

	def __init__(self, args=None):
		print "in the imap"
		self.email_type=None
		self.connect()
		self.get_userinfo()

	def get_userinfo(self):
		print "in the get_userinfo"
		for user in webnotes.conn.sql("""select name,response, sync_email from `tabProfile` 
				 where name <>'Administrator' and name <> 'Guest' and response is not null and name like '%pranali%'""",as_dict=1):
			print user['name']
			print user['response']
			logged_in = self.authenticate(user['name'],user['response'])
			print logged_in
			if logged_in:
				if user['sync_email'] == 'No':
					print "in the inbox"
					self.get_messages(user['name'])
					print "in the sent"
					self.get_sent_messages(user['name'])
					webnotes.conn.sql("""Update `tabProfile` set sync_email='yes' where name ='%s'"""%(user['name']))
					webnotes.conn.sql("commit")
					log=self.logout()
				else:
					print "in the inbox"
					self.get_new_messages(user['name'])
					"in else sent"
			    	self.get_sent_new_messages(user['name'])
			    	log=self.logout()

	def setup(self, args=None):
		# overrride
		self.settings = args or webnotes._dict()
				
	def check_mails(self):
		print "-------------------in the check mail--------------------"
		# overrride
		return True
	
	def process_message(self, mail):
		# print'in main process_message'
		# overrride
		pass
		
	def connect(self, raise_errors=True):
		# print "in the connect method"

		self.imap = imaplib.IMAP4_SSL(self.GMAIL_IMAP_HOST, self.GMAIL_IMAP_PORT)
		
		return self.imap

	def authenticate(self, username, access_token):

		print "in authenticate"
		self.connect()
		try:
			auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
			imap_auth = self.imap.authenticate('XOAUTH2', lambda x: auth_string)
			# print imap_auth
			self.logged_in = (imap_auth and imap_auth[0] == 'OK')

		except imaplib.IMAP4.error, err:
			self.logged_in = False
		
		return self.logged_in



	def fetch_emails(self, email_uid, name,email_type):
		print "in the fetch mail"
		print email_type
		result, data = self.imap.uid('fetch',email_uid, '(RFC822)')

		email_body=data[0][1]
		incoming_mail = IncomingMail(email_body)

		webnotes.conn.begin()
		self.process_message(incoming_mail,name,email_uid,email_type)
		webnotes.conn.commit()
		# self.email_type=None

	def get_email_uid(self):
		print "in the get_email_uid"
		if not self.check_mails():
			return # nothing to do

		webnotes.conn.commit()
		incoming_mail = None

		self.imap.select('INBOX')
		result, data = self.imap.uid('search', None, "ALL") # search and return uids instead
		list_email_uid = data[0].split()
		# email_t='Inbox'
		# print list_email_uid

		return list_email_uid

	def get_messages(self,name):
		print"in the get_messages"
		print name
		print self.get_email_uid()[:100]
		self.email_type=None
		self.email_type='Inbox'
		# t,s=self.get_sent_email_uid()[:100]
		# print s

		print self.email_type
		for email_uid in self.get_email_uid()[:100]:
			self.fetch_emails(email_uid, name,self.email_type)
		print "finish"	
			
		return

	def get_new_messages(self,name):
		print "in the  get new messg"
		self.email_type=None

		self.email_type='Inbox'
		res_uid=webnotes.conn.sql("""select max(email_uid) from `tabEmail Inbox` where owner='%s'"""%(name),as_list=1)
		if res_uid:
			last_uid=res_uid[0][0]
		print last_uid	
		print cint(last_uid)

		list_email_uids=self.get_email_uid()
		print "list id"
		print list_email_uids[0][0]
		for num in list_email_uids:
			print 
		
		# for email_uid in self.get_email_uid()[cint(last_uid):cint(last_uid)+100]:
		for email_uid in list_email_uids[cint(last_uid):cint(last_uid)+100]:	
			print "email_uid"
			print email_uid
			if cint(email_uid) > last_uid:
				print email_uid
				self.fetch_emails(email_uid, name,self.email_type)
		print "finish"		
		return

	def get_sent_messages(self,name):
		self.email_type=None
		print 'in the  get sent messages'
		print name
		print self.get_sent_email_uid()[cint(last_uid):cint(last_uid)+100]
		self.email_type='Sent'
		for email_uid in self.get_sent_email_uid():
			self.fetch_emails(email_uid, name,self.email_type)
			
		return

	def get_sent_email_uid(self):
		print "in the get sent email_uid"
		if not self.check_mails():
			return # nothing to do

		webnotes.conn.commit()
		incoming_mail = None

		self.imap.select('"[Gmail]/Sent Mail"')
		print 'ok'
		result, data = self.imap.uid('search', None, "ALL") # search and return uids instead
		list_sent_uid = data[0].split()
		print list_sent_uid 
		print "b4"

		return list_sent_uid

	def get_sent_new_messages(self,name):
		print "in the sent new email"
		self.email_type=None
		self.email_type='Sent'
		res_uid=webnotes.conn.sql("""select max(email_uid) from `tabSent Mail` where owner='%s'"""%(name),as_list=1)
		if res_uid:
			last_uid=res_uid[0][0]
		print last_uid 	

		print self.get_sent_email_uid()[cint(last_uid):cint(last_uid)+100]
		
		for email_uid in self.get_sent_email_uid()[cint(last_uid):cint(last_uid)+100]:
			if cint(email_uid) > last_uid:
				self.fetch_emails(email_uid, name,self.email_type)
		print 'finish'		
		return		

						

	def logout(self):
		print "logout"
		self.imap.logout()
		self.logged_in = False
		return

# class IMAPMailbox:
# 	# GMail IMAP defaults
#     GMAIL_IMAP_HOST = 'imap.gmail.com'
#     GMAIL_IMAP_PORT = 993
#     GMAIL_SMTP_HOST = "smtp.gmail.com"
#     GMAIL_SMTP_PORT = 587

#     def __init__(self, args=None):

#     	self.connect()
#         self.get_userinfo()

#     def get_userinfo(self):

# 	    for user in webnotes.conn.sql("""select name,response, sync_email from `tabProfile` 
# 	                    where name <>'Administrator' and name <> 'Guest' and response is not null""",as_dict=1):

# 	    	logged_in = self.authenticate(user['name'],user['response'])
# 	    	if logged_in:
# 	    		if user['sync_email'] == 'No':
# 	    			self.get_messages(user['name'])
#                     webnotes.conn.sql("""Update `tabProfile` set sync_email='yes' where name ='%s'"""%(user['name']))
#                     webnotes.conn.sql("commit")
#                     log=self.logout()
#                 else:
#                 	self.get_new_messages(user['name'])
#                     log=self.logout()


#     def setup(self, args=None):
#     	# overrride
#         self.settings = args or webnotes._dict()

#     def check_mails(self):
#     	print "-------------------in the check mail--------------------"
#         # overrride
#         return True
# 	def process_message(self, mail):
#         # print'in main process_message'
#         # overrride
#         pass

# 	def connect(self, raise_errors=True):
#         # print "in the connect method"

#         self.imap = imaplib.IMAP4_SSL(self.GMAIL_IMAP_HOST, self.GMAIL_IMAP_PORT)

#         return self.imap

# 	def authenticate(self, username, access_token):
# 		self.connect()
#         try:

#             auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
#             imap_auth = self.imap.authenticate('XOAUTH2', lambda x: auth_string)
#             self.logged_in = (imap_auth and imap_auth[0] == 'OK')

#         except imaplib.IMAP4.error, err:

#             self.logged_in = False

#         return self.logged_in

# 	def get_email_uid(self):

#         if not self.check_mails():
#         	return # nothing to do

#         webnotes.conn.commit()
#         incoming_mail = None

#         self.imap.select('INBOX')
#         result, data = self.imap.uid('search', None, "ALL") # search and return uids instead
#         list_email_uid = data[0].split()

#         return list_email_uid

# 	def fetch_emails(self, email_uid, name):
# 		result, data = self.imap.uid('fetch',email_uid, '(RFC822)')
#         email_body=data[0][1]
#         incoming_mail = IncomingMail(email_body)

#         webnotes.conn.begin()
#         self.process_message(incoming_mail,name,email_uid)
#         webnotes.conn.commit()

#     def get_messages(self,name):

#         print name
#         print self.get_email_uid()[:100]
#         for email_uid in self.get_email_uid()[:100]:
#         	self.fetch_emails(email_uid, name)
#         return

#     def get_new_messages(self,name):
#         res_uid=webnotes.conn.sql("""select max(email_uid) from `tabEmail Inbox` where owner='%s'"""%(name),as_list=1)
#         if res_uid:
#         	last_uid=res_uid[0][0]
#         print self.get_email_uid()[cint(last_uid):cint(last_uid)+100]
#         for email_uid in self.get_email_uid()[cint(last_uid):cint(last_uid)+100]:
#         	if cint(email_uid) > last_uid:
#         		self.fetch_emails(email_uid, name)
#         return

#     def logout(self):
#     	print "logout"
#         self.imap.logout()
#         self.logged_in = False
#         return
