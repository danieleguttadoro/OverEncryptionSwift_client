#!/bin/bash
sudo git add *
echo "Insert commit message"
read msg
sudo git commit -m msg
sudo git remote add origin https://github.com/AlessandroSaullo/OverEncryptionSwift.git 
echo "Insert branch"
read branch
sudo git push origin branch 
