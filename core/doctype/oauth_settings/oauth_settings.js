cur_frm.cscript.get_verification_code = function(doc, dt, dn){

	console.log("in the ks");
	wn.call({
		method:"core.doctype.oauth_settings.oauth_settings.get_verification_code",
		args:{client_id:doc.client_id, client_secret:doc.client_secret,app_name:doc.app_name},
		callback:function(r){
			
			window.open(r.message)
		}
	})
}

cur_frm.cscript.generate_token = function(doc, dt, dn){
	wn.call({
		method:"core.doctype.oauth_settings.oauth_settings.generate_token",
		args:{client_id:doc.client_id, client_secret:doc.client_secret,authorization_code:doc.verification_code,user_name:doc.user,app_name:doc.app_name},
	})
}

cur_frm.cscript.get_verification_code_for_calender= function(doc, dt, dn){
	wn.call({
		method:"core.doctype.oauth_settings.oauth_settings.genearate_calendar_cred",
		args:{client_id:doc.client_id,client_secret:doc.client_secret,authorization_code:doc.verification_code,app_name:doc.app_name},
		callback:function(r){
			window.open(r.message.authorize_url)
		}
	})
}

cur_frm.cscript.generate_credentials = function(doc, dt ,dn){
	return wn.call({
			method: "core.doctype.oauth_settings.oauth_settings.generate_credentials",
			args: {
				"client_id":doc.client_id, 
				"client_secret":doc.client_secret, 
				"app_name":doc.app_name,
				"authorization_code": cur_frm.doc.verification_code_for_calender,
				"user_name":doc.user
			},
		});
}

