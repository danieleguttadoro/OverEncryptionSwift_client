from swift import gettext_ as _

from swift.common.swob import Request, Response, HTTPServerError
from swift.common.utils import get_logger, generate_trans_id
from swift.common.wsgi import WSGIContext
from swift.common.swob import wsgify

#To use encswift
from catalogue import *
import time

from keystoneclient import session

#DAEMON_IP = '127.0.0.1'
class key_master(WSGIContext):

    userID = "1c58937ce4634808b8cbd8a638d01cfc" 

    def __init__(self,app, conf):
        self.app = app
        self.conf = conf

    def __call__(self, env, start_response):
        
        print "----------------- KEY_MASTER -----------------------"
        req = Request(env)
        
        username   = env.get('HTTP_X_USER_NAME',None)
        userid     = env.get('HTTP_X_USER_ID',None)
        print "USERNAME ----> ", username
        print "USERID   ----> ", userid
        
        #COMMENT: Control the author of the request. DA AGGIUNGERE IL CONTROLLO SULL'ID DEL CEILOMETER(OMONOMIA con un utente)
        if req.method == "GET" and username != "ceilometer" and username != "encadmin" and username != "admin" and username != None:
            
            version, account, container, obj = req.split_path(1,4,True)

            if obj != None:
                new_req = Request.blank(req.path_info,None,req.headers,None)
                new_req.method = "HEAD"
                new_req.path_info = "/".join(["",version,account,container])
                response = new_req.get_response(self.app)
                cont_header = response.headers
                sel_id_key_container = cont_header.get('x-container-meta-sel-id-key',"")
                print "1"
                if sel_id_key_container is not "":
                    resp_obj = req.get_response(self.app)
                    sel_id_key_object = resp_obj.headers.get('x-object-meta-sel-id-key',"")
                    print "2"
                    if sel_id_key_object != sel_id_key_container:
                        key = get_cat_obj(self.userID, sel_id_key_object)
                        if key is not None:
                            print('Decryption token found')

                            env['swift_crypto_fetch_token'] = key

        return self.app(env, start_response)

def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def except_filter(app):
        return key_master(app,conf)
    return except_filter
