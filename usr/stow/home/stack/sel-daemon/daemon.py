from catalog_manager import *
from connection import *
from create_user import CreateUser

from Crypto.PublicKey import RSA 
from Crypto.Cipher import AES
from base64 import b64decode

from keystoneclient.v2_0 import client as kc
import swiftclient

from flask import *
app = Flask(__name__)

from myLogger import *
  
BLOCK_SIZE = 16

def update_req():                                                     
    try:                                                              
        receiver = request.headers['receiver']
        idkey = request.headers['id']
        obj = json.loads(request.data)
        update_catalogue(receiver, idkey, obj)
        logger.info('OK: receiver %s, idkey %s' % (receiver,idkey))
        return Response(status=200)
    except Exception,err:
        logger.debug('Error in update catalog. Exception: %s' % err)
        return Response(status=304)


def create_req():                                                     
    if request.method == 'GET':
        logger.info('Get request received. Send public_key')
        resp = Response(get_publicKey())
        return resp

    elif request.method == 'PUT':
        
        username, encpass, client_pubKey = request.data.split('#')
        password = decrypt(encpass)

        CreateUser(username,password,TENANT_NAME,META_TENANT,'Member',AUTH_URL).start()

        userid = getUserID(username)
        daemonid = getUserID(ADMIN_USER)
        create_catalog(userid,daemonid)

        meta_conn.put_object("Keys", userid, client_pubKey)


        logger.info('User correctly created')
        return Response(userid)

    else:
        logger.warning('ERROR: on create_req function')
        return Response(status=400)

def get_masterKey():    
    """ 
    Get the user's public key
    Returns:
        Public key
    """

    filename = '/opt/stack/sel-daemon/keys/mk.key'
    with open(filename, 'r') as f:
        master_key = f.read()
    return base64.b64decode(master_key)

def get_publicKey():    
    """ 
    Get the user's public key
    Returns:
        Public key
    """

    filename = '/opt/stack/sel-daemon/keys/pub.key'
    with open(filename, 'r') as f:
        public_key = f.read()
    return public_key

def get_privateKey():  
    """
    Get the plain user's private key
    Returns:
        The plain private key
    """
    filename = '/opt/stack/sel-daemon/keys/pvt.key'
    with open(filename, 'r') as f:
        private_key = f.read()
    unpad = lambda s: s[:-ord(s[len(s) - 1:])]
    private_key = base64.b64decode(private_key)
    iv = private_key[:BLOCK_SIZE]
    cipher = AES.new(get_masterKey(), AES.MODE_CBC, iv) 
    return unpad(cipher.decrypt(private_key[BLOCK_SIZE:]))


def getUserID(username):
    """
    Get the user's ID from Keystone
    """
    # Requires an admin connection
    kc_conn = kc.Client(username=ADMIN_USER, password=ADMIN_KEY, tenant_name=TENANT_NAME, auth_url=AUTH_URL)
    this_user = filter(lambda x: x.username == username, kc_conn.users.list())
    return this_user[0].id

def decrypt(secret):
    """
    Decipher the information sent by the client.
    Returns:
        The plain username,password,pub_key
    """
    # RSA decipher
    receiver_priv_key = RSA.importKey(get_privateKey())
    return receiver_priv_key.decrypt(b64decode(secret))



@app.route("/<mode>",methods=['GET','PUT'])
def start(mode):
    #logging.basicConfig(filename='/opt/stack/sel-daemon/logs/event.log',level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if mode is "update" and request.method is "PUT":
       return update_req()
    if mode is "create":
       return create_req()
    if mode is "get_id" and request.method is "PUT":
       return Response(getUserID(request.data))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(DAEMON_PORT))


