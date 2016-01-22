from swift import gettext_ as _

from swift.common.swob import Request, Response, HTTPServerError
from swift.common.utils import get_logger, generate_trans_id
from swift.common.wsgi import WSGIContext
from swift.common.swob import wsgify


#To use encswift
import catalog_functions

#To use barbican
import sys
import traceback

from barbicanclient import client
from keystoneclient import session
from keystoneclient.auth import identity
################

class key_master(WSGIContext):

   # Names of meta container and file of the graph
   meta_container = "meta"
   graph_tokens = "b"

   def __init__(self,app, conf):
        self.app = app
        self.conf = conf
   

   def __call__(self, env, start_response):
      print "----------------- KEY_MASTER -----------------------"
      #barbican_client()
      req = Request(env)
      resp = req.get_response(self.app)

      #COMMENT: Finding user and method
      username = env.get('HTTP_X_USER_NAME',None)
      userid   = env.get('HTTP_X_USER_ID',None)
      userid = "9665a758e2544ee3a3eb8b89fd878aa5"
      print "------------USERID, USERNAME----------------"
      print username
      print userid
      #COMMENT: Control the author of the request. DA AGGIUNGERE IL CONTROLLO SULL'ID DEL CEILOMETER(OMONOMIA con un utente)
      if username != "ceilometer" and username != None:
      
       if req.method != "PUT":
	#Get the catalog from metacontainer
        req_meta_container, json_catalog = catalog_functions.get_catalog(req,self.app)
	#print json_catalog
	graph = catalog_functions.load_graph(json_catalog)
	#graph2 =  catalog_functions.get_graph(json_catalog)
        print "-----------------GRAPH-------------------"
	print graph
	#print graph2
	
	if req.method == "GET":
	    
    	    # COMMENT: Scan the graph to obtain the key and insert it in the env (GET) or to modify the graph in order to add or delete a key (PUT)
	    #token = catalog_functions.get_DerivPath(catalog_functions.get_graph(json_catalog),"prova")
	    version , account , container , obj = req.split_path(1,4,True)
	    print container	
            #cryptotoken = catalog_functions.get_cryptotoken(json_catalog,container) 
	    print "TOKEN"
	    #print cryptotoken

	    #if cryptotoken != None:
	        #env['swift_crypto_fetch_crypto_token'] = cryptotoken
	        #pass
	    
             
	elif True:# req.method == "POST":
		
	    #if env['overencrypt']=="QualcosaYes"         
	     
		new_graph = catalog_functions.overencrypt(userid,json_catalog,["22222211prova234"],["rreeeeeeeeefk9384ghnivu"])
                req_meta_container.body = new_graph
	    #else if env['overencrypt'] =="QualcosaltroNo"

		#COMMENT: Control the graph
		#req_meta_container.body = catalog_functions.control_graph(json_catalog,["111111prova234","prova234"])
 
            	#COMMENT: Upload on metacontainer the new version of graph
            	req_meta_container.method = 'PUT'
            	req_meta_container.get_response(self.app)

	elif req.method == "DELETE":
	    #TODO
      
	    pass
      
      return self.app(env, start_response)


def barbican_client():

    #Variables for barbican
    ADMIN_USER="admin"
    ADMIN_PASS="secretsecret"
    ADMIN_TENANT="demo"
    AUTH_URL="http://127.0.0.1:5000/v2.0"
    BARB_URL="http://127.0.0.1:9311"
    AUTH_IP="127.0.0.1"
	
    try:
       # We'll use Keystone API v3 for authentication
        auth = identity.v2.Password(auth_url=AUTH_URL,
            username=ADMIN_USER,
            password=ADMIN_PASS,
            tenant_name=ADMIN_TENANT)

        # Next we'll create a Keystone session using the auth plugin we just created
        sess = session.Session(auth=auth)

	print '-----------------------BARBICAN---------------------------'
        print 'session created successfully'

        # Now we use the session to create a Barbican client
        barbican = client.Client(endpoint=BARB_URL, session=sess)

        print 'barbican client created successfully'

        # Let's create a Secret to store some sensitive data
        secret = barbican.secrets.create(name=u'Self destruction sequence',
                                         payload=u'the magic words are squeamish ossifrage')

        print 'secret created successfully'

        # Now let's store the secret by using its store() method. This will send the secret data
        # to Barbican, where it will be encrypted and stored securely in the cloud.
        secret.store()
        #u'http://localhost:9311/v1/secrets/85b220fd-f414-483f-94e4-2f422480f655'

        print 'secret stored successfully'

        # The URI returned by store() uniquely identifies your secret in the Barbican service.
        # After a secret is stored, the URI is also available by accessing
        # the secret_ref attribute.
        print(secret.secret_ref.replace('localhost',AUTH_IP))
        #http://localhost:9311/v1/secrets/091adb32-4050-4980-8558-90833c531413

        # When we need to retrieve our secret at a later time, we can use the secret_ref
        retrieved_secret = barbican.secrets.get(secret.secret_ref.replace('localhost',
            AUTH_IP))
        # We can access the secret payload by using the payload attribute.
        # Barbican decrypts the secret and sends it back.
        print(retrieved_secret.payload)
        #the magic words are squeamish ossifrage

    except:
        traceback.print_exc(file=sys.stdout)



@wsgify
def raise_error(req,stat):

    if stat == 403:
        return Response(request=req, status=403, body="USER UNAUTHORIZED TO OBTAIN THIS FILE",
                        content_type="text/plain")


def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def except_filter(app):
        return key_master(app,conf)
    return except_filter
