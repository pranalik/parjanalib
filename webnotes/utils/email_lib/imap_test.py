import re
import imaplib

GMAIL_IMAP_HOST = 'imap.gmail.com'
GMAIL_IMAP_PORT = 993

auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
print 'auth_string'
			
print auth_string
imap_auth = self.imap.authenticate('XOAUTH2', lambda x: auth_string)